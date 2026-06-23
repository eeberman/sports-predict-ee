"""
Per-match forecast worksheet generator.

Pulls the 10 questions (SportsPredict MCP) + odds anchors (The Odds API),
dispatches each normalized question to compute/priors, and renders a review
table: question | prob | range | evidence | main risk | grounding.

NO auto-submit. Writes outputs/worksheets/{match}.md and .csv (the .csv carries
market_id so a human can submit after review).
"""
from __future__ import annotations

import json
import re
import statistics as st
from pathlib import Path

from provider_probe.clients.sportspredict import _tool
from provider_probe.clients import the_odds_api as odds
from sportspredict_inventory.normalize import normalize_market
from sportspredict_inventory import config as spc
from forecasting import compute as c
from forecasting import base_rate_priors as priors
from forecasting import team_loo_rates

WC_SPORT = "soccer_fifa_world_cup"
OUTDIR = Path(__file__).resolve().parents[1] / "outputs" / "worksheets"


# ── team-name helpers ───────────────────────────────────────────────────────────

def split_match_name(name: str) -> tuple[str, str]:
    """'BEL vs IRN' -> ('Belgium','Iran') via FIFA map."""
    home_raw, away_raw = (name.split(" vs ", 1) + [""])[:2]
    m = spc.FIFA_CODE_TO_NAME
    return m.get(home_raw.strip(), home_raw.strip()), m.get(away_raw.strip(), away_raw.strip())


def _norm(s: str) -> str:
    return re.sub(r"[^a-z]", "", (s or "").lower())


# ── odds ingest ─────────────────────────────────────────────────────────────────

def fetch_odds_anchors(home: str, away: str) -> dict:
    """Return {fav_side, fav_team, p_home, p_draw, p_away, over_prob, over_line} or {} if no event."""
    ev = odds.get_odds(WC_SPORT, regions="us", markets="h2h,totals")
    want = {_norm(home), _norm(away)}
    match = next((e for e in ev if {_norm(e.get("home_team")), _norm(e.get("away_team"))} == want), None)
    if not match:
        return {}
    # consensus medians
    agg: dict = {}
    for b in match.get("bookmakers", []):
        for m in b.get("markets", []):
            for oc in m.get("outcomes", []):
                agg.setdefault((m["key"], oc.get("name"), oc.get("point")), []).append(oc.get("price"))
    med = {k: st.median(v) for k, v in agg.items()}
    # h2h (decimal) -> de-vig
    eh = match.get("home_team")
    h = med.get(("h2h", eh, None))
    d = med.get(("h2h", "Draw", None))
    a = next((v for (mk, nm, pt), v in med.items() if mk == "h2h" and nm not in (eh, "Draw")), None)
    out: dict = {}
    if h and d and a:
        # map event home/away to our home/away (event home may differ)
        ph_ev, pd, pa_ev = c.devig_three_way(1/h, 1/d, 1/a)
        if _norm(eh) == _norm(home):
            p_home, p_away = ph_ev, pa_ev
        else:
            p_home, p_away = pa_ev, ph_ev
        out.update(p_home=p_home, p_draw=pd, p_away=p_away)
        out["fav_side"] = "home" if p_home >= p_away else "away"
        out["fav_team"] = home if p_home >= p_away else away
        out["fav_strength"] = max(p_home, p_away)
    # main total line (most-quoted point)
    over_pts = [(pt, v) for (mk, nm, pt), v in med.items() if mk == "totals" and nm == "Over"]
    und_pts = {pt: v for (mk, nm, pt), v in med.items() if mk == "totals" and nm == "Under"}
    if over_pts:
        line, ov = sorted(over_pts, key=lambda x: -agg[("totals", "Over", x[0])].__len__())[0]
        un = und_pts.get(line)
        if un:
            out["over_prob"] = c.devig_two_way(1/ov, 1/un)
            out["over_line"] = line
    return out


# ── dispatch ────────────────────────────────────────────────────────────────────

def _role(target: str, fav_side: str) -> str:
    if target in ("home", "away"):
        return "favorite" if target == fav_side else "underdog"
    return "neutral"


def _subject_is_home(n: dict) -> bool:
    """For a 'who has more X' question, which team is the SUBJECT (the 'will X have more')?
    It's the team named first in the raw question. Comparison handlers must answer
    P(subject > other), not the fixed P(home > away)."""
    q = (n.get("raw_question") or "").lower()
    home = (n.get("home_team") or "").lower()
    away = (n.get("away_team") or "").lower()
    ih = q.find(home) if home else -1
    ia = q.find(away) if away else -1
    if ih == -1 and ia == -1:
        return True  # default to home if neither found
    if ia == -1:
        return True
    if ih == -1:
        return False
    return ih <= ia


def forecast_question(n: dict, ctx: dict) -> c.Forecast:
    fam, sub = n["question_family"], n["question_subtype"]
    fav = ctx.get("fav_strength", 0.6)
    fav_side = ctx.get("fav_side", "home")
    N = n.get("threshold_value")

    # match result
    if fam == "match_result" and sub == "team_win":
        tgt = n["target_team_or_side"]
        p = ctx.get("p_home" if tgt == "home" else "p_away")
        if p is None:
            return c.fc(0.5, "no h2h odds", "no market", "base_rate")
        return c.fc(p, f"3-way de-vig of h2h ({tgt})", "market move/late news", "market")

    # halftime favorite leading
    if fam == "halftime" and sub == "halftime_team_winning":
        tgt = n["target_team_or_side"]
        p_win = ctx.get("p_home" if tgt == "home" else "p_away", fav)
        f = priors.get("halftime_lead_factor")
        return c.fc(p_win * f, f"P(lead@HT) = {f} x P(win) {p_win:.2f}", "1H cagey / early goal swing", "base_rate")

    # BTTS and 3+ goals
    if fam == "goals_totals" and sub == "btts_and_over":
        btts = ctx.get("btts")
        if btts is None:
            # model from over line: scale to a BTTS estimate, flag
            ov = ctx.get("over_prob", 0.5)
            btts = max(0.30, min(0.62, ov - 0.07))  # rough; weaker attack lowers BTTS
            ev_txt, gr = f"BTTS modeled from over {ctx.get('over_line')} (no BTTS market — PASTE)", "base_rate"
        else:
            ev_txt, gr = f"P(BTTS)={btts:.2f} market", "market+composition"
        return c.fc(c.compose_btts_and_over(btts), ev_txt, "favorite clean sheet", gr)

    # total goals under threshold (e.g., "2 or fewer")
    if fam == "goals_totals" and sub in ("total_goals_under", "total_goals_over"):
        over_prob = ctx.get("over_prob")
        over_line = ctx.get("over_line")
        if over_prob is not None and N is not None:
            # If asking for "≤ N", and market is over L, compute P(≤N) from P(>L)
            # Assume N < L (e.g., N=2, L=2.5), so P(≤2) ≈ 1 - P(>2.5) = under_prob
            if sub == "total_goals_under" and N <= over_line:
                under_prob = 1 - over_prob
                return c.fc(under_prob, f"Market under {over_line:.1f} = {under_prob:.2f}", "margin swing", "market")
        return c.fc(0.5, f"UNHANDLED goals_totals/{sub}", "needs market data", "base_rate")

    # shots-on-target comparison (2H) — use shrunk team rates instead of favorite-scaling
    if fam == "shots" and sub == "shots_comparison":
        try:
            tr = team_loo_rates.load()
            home = n.get("home_team", "")
            away = n.get("away_team", "")
            home_sot, nh = tr.get_team_rate(home, None, "sot_2h", "for", shrink=True)
            away_sot, na = tr.get_team_rate(away, None, "sot_2h", "for", shrink=True)
            min_n = min(nh, na)
            if min_n >= 4:  # both teams have enough history
                subj_home = _subject_is_home(n)
                p = (c.poisson_p_a_greater_b(home_sot, away_sot) if subj_home
                     else c.poisson_p_a_greater_b(away_sot, home_sot))
                prov = f"{tr.source_tag(home)}/{tr.source_tag(away)}"
                return c.fc(p, f"2H SoT: {home} {home_sot:.2f} vs {away} {away_sot:.2f} ({min_n} g, {prov})",
                            "teammate variance", "team_data")
        except Exception:
            pass
        # fallback to base rate if team data unavailable
        base = priors.get("dominant_more_2h_sot", "favorite")
        p = c.prior_with_favorite_scaling(base, fav)
        return c.fc(p, f"SB 2H-SoT dominance {base:.2f}, fav-scaled (fav {fav:.2f})",
                    "game-state easing / 2H tie", "base_rate")

    # total shots on target over (full or 2H) — use matchup signal
    if fam == "shots" and sub == "total_shots_over":
        stat = "sot_2h" if n.get("time_scope") == "second_half" else "sot_tot"
        try:
            tr = team_loo_rates.load()
            home = n.get("home_team", "")
            away = n.get("away_team", "")
            mu, min_n = tr.matchup_mean(home, away, stat)
            if min_n >= 4:  # both teams have enough history
                p = c._pois_sf(int(N), mu)
                prov = f"{tr.source_tag(home)}/{tr.source_tag(away)}"
                return c.fc(p, f"Poisson(for+against={mu:.2f}) P(>={int(N)}) ({min_n} g, {prov})",
                            "defensive intensity", "team_data")
        except Exception:
            pass
        # fallback to base rate if team data unavailable
        mean = priors.get("mean_2h_sot" if n.get("time_scope") == "second_half" else "mean_total_sot")
        p = c._pois_sf(int(N), mean)
        return c.fc(p, f"Poisson(mean={mean}) P(>= {int(N)})", "compact match / few shots", "base_rate")

    # total corners over — use matchup signal
    if fam == "corners" and sub == "total_corners_over":
        try:
            tr = team_loo_rates.load()
            home = n.get("home_team", "")
            away = n.get("away_team", "")
            mu, min_n = tr.matchup_mean(home, away, "cor_tot")
            if min_n >= 4:  # both teams have enough history
                p = c._pois_sf(int(N), mu)
                prov = f"{tr.source_tag(home)}/{tr.source_tag(away)}"
                return c.fc(p, f"Poisson(for+against={mu:.2f}) P(>={int(N)}) ({min_n} g, {prov})",
                            "attacking style", "team_data")
        except Exception:
            pass
        # fallback to base rate if team data unavailable
        mean = priors.get("mean_total_corners")
        p = c._pois_sf(int(N), mean)
        return c.fc(p, f"Poisson(mean={mean}) P(>= {int(N)} corners) [PASTE corner mkt to sharpen]",
                    "low-tempo match", "base_rate")

    # corners comparison 2H — use shrunk team rates instead of favorite-scaling
    if fam == "corners" and sub == "corners_comparison":
        try:
            tr = team_loo_rates.load()
            home = n.get("home_team", "")
            away = n.get("away_team", "")
            home_cor, nh = tr.get_team_rate(home, None, "cor_2h", "for", shrink=True)
            away_cor, na = tr.get_team_rate(away, None, "cor_2h", "for", shrink=True)
            min_n = min(nh, na)
            if min_n >= 4:  # both teams have enough history
                subj_home = _subject_is_home(n)
                p = (c.poisson_p_a_greater_b(home_cor, away_cor) if subj_home
                     else c.poisson_p_a_greater_b(away_cor, home_cor))
                prov = f"{tr.source_tag(home)}/{tr.source_tag(away)}"
                return c.fc(p, f"2H corners: {home} {home_cor:.2f} vs {away} {away_cor:.2f} ({min_n} g, {prov})",
                            "game-state variance", "team_data")
        except Exception:
            pass
        # fallback to base rate if team data unavailable
        base = priors.get("dominant_more_2h_corners", "favorite")
        raw = c.prior_with_favorite_scaling(base, fav)
        return c.fc(c.temper_2h_dominance(raw, fav), "2H corner dominance, tempered", "game-state easing", "base_rate")

    # fouls comparison — use shrunk team rates instead of favorite-scaling
    if fam == "fouls" and sub == "fouls_comparison":
        try:
            tr = team_loo_rates.load()
            home = n.get("home_team", "")
            away = n.get("away_team", "")
            home_fouls, nh = tr.get_team_rate(home, None, "foul", "for", shrink=True)
            away_fouls, na = tr.get_team_rate(away, None, "foul", "for", shrink=True)
            min_n = min(nh, na)
            if min_n >= 4:  # both teams have enough history
                subj_home = _subject_is_home(n)
                p = (c.poisson_p_a_greater_b(home_fouls, away_fouls) if subj_home
                     else c.poisson_p_a_greater_b(away_fouls, home_fouls))
                prov = f"{tr.source_tag(home)}/{tr.source_tag(away)}"
                return c.fc(p, f"Fouls: {home} {home_fouls:.2f} vs {away} {away_fouls:.2f} ({min_n} g, {prov})",
                            "referee discretion", "team_data")
        except Exception:
            pass
        # fallback to base rate if team data unavailable
        tgt = n["target_team_or_side"]
        base = priors.get("underdog_more_fouls")
        subj_is_fav = (tgt == fav_side)
        p = (1 - base) if subj_is_fav else base
        return c.fc(p, f"underdog-fouls-more prior {base:.2f} (subj {'fav' if subj_is_fav else 'dog'})",
                    "referee/style variance", "base_rate")

    # discipline: total cards over (2H here) — use matchup signal
    if fam == "discipline" and sub == "total_cards_over":
        if n.get("time_scope") == "second_half":
            try:
                tr = team_loo_rates.load()
                home = n.get("home_team", "")
                away = n.get("away_team", "")
                mu, min_n = tr.matchup_mean(home, away, "card_2h")
                if min_n >= 4:  # both teams have enough history
                    p = c._pois_sf(int(N), mu)
                    prov = f"{tr.source_tag(home)}/{tr.source_tag(away)}"
                    return c.fc(p, f"Poisson(for+against={mu:.2f}) P(>={int(N)}) ({min_n} g, {prov})",
                                "referee temperament", "team_data")
            except Exception:
                pass
        # fallback to base rate if team data unavailable
        mean = priors.get("mean_2h_cards") if n.get("time_scope") == "second_half" else 3.8
        p = c._pois_sf(int(N), mean)
        return c.fc(p, f"Poisson(mean={mean}) P(>= {int(N)} cards) 2026 surge", "calm game / lenient ref", "base_rate")

    # discipline: penalty or red
    if fam == "discipline" and sub == "penalty_or_red_card":
        p = priors.get("penalty_or_red")
        return c.fc(p, "SB pen 0.42 + 2026 red ~0.30 -> ~0.56", "clean composed match", "base_rate")

    # offsides
    if fam == "offsides":
        tgt = n["target_team_or_side"]
        role = _role(tgt, fav_side)
        p = priors.get("offside_2plus", role if role != "neutral" else "neutral")
        return c.fc(p, f"SB offside>=2 {role} {p:.2f}", "deep block / vertical attack", "base_rate")

    # player props (deferrable)
    if fam == "player_markets" and sub == "player_shot_on_target":
        p = priors.get("player_sot_midfielder")
        return c.fc(p, "placeholder midfielder 1+ SoT (DEFER / paste prop)", "lineup/role unknown", "base_rate")
    if fam == "player_markets" and sub in ("player_goal_or_assist", "player_goal"):
        p = priors.get("player_goal_or_assist_keyfwd")
        return c.fc(p, "placeholder key-forward G+A (DEFER / paste prop)", "lineup/role unknown", "base_rate")

    # fallback
    return c.fc(0.5, f"UNHANDLED {fam}/{sub}", "needs manual classification", "base_rate")


# ── pull + render ───────────────────────────────────────────────────────────────

def build_worksheet(lobby_id: str, match: dict) -> dict:
    mid, name = match["id"], match["name"]
    home, away = split_match_name(name)
    markets = json.loads(_tool("list_markets", {"lobby_id": lobby_id, "match_id": mid}))
    ctx = fetch_odds_anchors(home, away)
    rows = []
    for mk in markets:
        q = mk.get("question") or mk.get("title") or ""
        n = normalize_market({"question": q}, {"home_team": home, "away_team": away})
        # normalize_market does not echo the team names; the forecaster's team-rate
        # lookups read n["home_team"]/["away_team"], so inject them here or every
        # comparison/threshold question silently falls back to base rate.
        n["home_team"], n["away_team"] = home, away
        n["raw_question"] = q
        f = forecast_question(n, ctx)
        rows.append({"market_id": mk["id"], "question": q, "family": n["question_family"],
                     "prob": f.prob, "low": f.low, "high": f.high,
                     "evidence": f.evidence, "main_risk": f.main_risk, "grounding": f.grounding})
    # preserve SportsPredict native market order (matches the platform UI)
    return {"match": name, "home": home, "away": away, "ctx": ctx, "rows": rows}


def render_md(ws: dict) -> str:
    ctx = ws["ctx"]
    anchor = (f"Belgium/home {ctx.get('p_home', float('nan')):.2f} / draw {ctx.get('p_draw', float('nan')):.2f} / "
              f"away {ctx.get('p_away', float('nan')):.2f}; over {ctx.get('over_line')} = {ctx.get('over_prob', float('nan')):.2f}"
              if ctx else "NO ODDS — manual paste required")
    lines = [f"# {ws['match']} — forecast worksheet",
             f"\n**Odds anchors:** {anchor}\n",
             "| Q | prob | range | grounding | evidence | main risk |",
             "|---|------|-------|-----------|----------|-----------|"]
    for r in ws["rows"]:
        lines.append(f"| {r['question']} | **{int(r['prob'])}** | {int(r['low'])}–{int(r['high'])} | "
                     f"{r['grounding']} | {r['evidence']} | {r['main_risk']} |")
    lines.append("\n_NO auto-submit. Review, paste gap markets (BTTS / corners / player props), then submit manually._")
    return "\n".join(lines)


def write(ws: dict) -> tuple[Path, Path]:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "_", ws["match"].lower()).strip("_")
    md = OUTDIR / f"{slug}.md"
    md.write_text(render_md(ws), encoding="utf-8")
    import csv
    cp = OUTDIR / f"{slug}.csv"
    with cp.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(ws["rows"][0].keys()))
        w.writeheader(); w.writerows(ws["rows"])
    return md, cp
