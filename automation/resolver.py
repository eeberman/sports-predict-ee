"""Market-only SportsPredict question resolver for email automation."""

from __future__ import annotations

import math
import re
from typing import Any

from . import config
from .models import Decision
from .odds import MarketBook, norm_name


def _round_pct(p: float) -> int:
    return int(round(max(0.0, min(1.0, p)) * 100))


def _raw_minus_haircut(price: float) -> float:
    return max(0.01, min(0.99, (1.0 / price) - config.ONE_SIDED_PROP_HAIRCUT_PCT / 100.0))


def _devig_proportional(raw_probs: list[float]) -> list[float]:
    total = sum(raw_probs)
    if total <= 0:
        raise ValueError("sum of raw probabilities must be positive")
    return [p / total for p in raw_probs]


def _devig_odds_ratio(raw_probs: list[float]) -> list[float]:
    odds_ratios = [p / (1.0 - p) for p in raw_probs]

    def total(c: float) -> float:
        out = 0.0
        for odds_ratio in odds_ratios:
            fair_or = odds_ratio / c
            out += fair_or / (1.0 + fair_or)
        return out

    lo, hi = 1.0, 2.0
    while total(hi) > 1.0 and hi < 1e9:
        hi *= 2.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if total(mid) > 1.0:
            lo = mid
        else:
            hi = mid
    c = (lo + hi) / 2.0
    return [(odds_ratio / c) / (1.0 + odds_ratio / c) for odds_ratio in odds_ratios]


def _safe_devig(raw_probs: list[float]) -> list[float]:
    try:
        return _devig_odds_ratio(raw_probs)
    except Exception:
        return _devig_proportional(raw_probs)


def _poisson_sf(k: int, mu: float) -> float:
    return 1.0 - sum(math.exp(-mu) * mu**i / math.factorial(i) for i in range(k))


def _fit_poisson_mean_from_ladder(thresholds: list[int], probs: list[float]) -> float:
    best_mu, best_err = 1.0, float("inf")
    mu = 0.1
    while mu <= 20.0:
        err = sum((_poisson_sf(t, mu) - p) ** 2 for t, p in zip(thresholds, probs))
        if err < best_err:
            best_mu, best_err = mu, err
        mu += 0.05
    return round(best_mu, 3)


def _poisson_p_a_greater_b(mu_a: float, mu_b: float, kmax: int = 30) -> float:
    total = 0.0
    for kb in range(kmax + 1):
        pb = math.exp(-mu_b) * mu_b**kb / math.factorial(kb)
        if pb < 1e-9 and kb > mu_b:
            break
        total += pb * _poisson_sf(kb + 1, mu_a)
    return total


def _which_subject_team(question: str, home: str, away: str) -> str:
    q = question.lower()
    ih = q.find(home.lower())
    ia = q.find(away.lower())
    if ih == -1 and ia == -1:
        return "home"
    if ia == -1:
        return "home"
    if ih == -1:
        return "away"
    return "home" if ih <= ia else "away"


def _target_team_name(normalized: dict[str, Any], home: str, away: str) -> str | None:
    target = normalized.get("target_team_or_side")
    if target == "home":
        return home
    if target == "away":
        return away
    return None


def _team_total_prob(book: MarketBook, team: str, threshold: int) -> tuple[float, str, str] | None:
    point = threshold - 0.5
    for market in ("team_totals", "alternate_team_totals"):
        pair = book.two_way_prices(market, point=point, description=team)
        if pair:
            over, under = pair
            p = _safe_devig([1 / over, 1 / under])[0]
            return p, f"{market} {team} O{point:g}/{point:g}U {over:g}/{under:g} -> {p*100:.1f}%", f"{market}:{norm_name(team)}:{point}"
        one_sided = book.preferred_prop_price(market, "Over", point=point, description=team)
        if one_sided:
            p = _raw_minus_haircut(one_sided.price)
            return p, f"{one_sided.bookmaker} {market} {team} O{point:g} {one_sided.price:g}; one-sided haircut {config.ONE_SIDED_PROP_HAIRCUT_PCT:g} pts -> {p*100:.1f}%", f"{market}:{norm_name(team)}:{point}:{one_sided.bookmaker}"
    return None


def _total_goals_prob(book: MarketBook, subtype: str, threshold: float | None) -> tuple[float, str, str] | None:
    if threshold is None:
        return None
    point = threshold - 0.5 if subtype == "total_goals_over" else threshold + 0.5
    pair = book.two_way_prices("totals", point=point)
    if not pair:
        return None
    over, under = pair
    p_over = _safe_devig([1 / over, 1 / under])[0]
    if subtype == "total_goals_under":
        p = 1 - p_over
        return p, f"Totals U{point:g}: O/U {over:g}/{under:g}; de-vig under = {p*100:.1f}%", f"totals:{point}:under"
    return p_over, f"Totals O{point:g}: O/U {over:g}/{under:g}; de-vig over = {p_over*100:.1f}%", f"totals:{point}:over"


def _btts_and_over(book: MarketBook) -> tuple[float, str, str] | None:
    pair = book.two_way_prices("btts")
    if not pair:
        return None
    yes, no = pair
    p_btts = _safe_devig([1 / yes, 1 / no])[0]
    p = p_btts * config.BTTS_NOT_1_1_FACTOR
    return p, f"BTTS fair {p_btts*100:.1f}% times non-1-1 conditional {config.BTTS_NOT_1_1_FACTOR*100:.0f}% = {p*100:.1f}%", "btts_and_over"


def _match_win(book: MarketBook, target: str) -> tuple[float, str, str] | None:
    prices = book.h2h_prices()
    if not prices:
        return None
    home_price, draw_price, away_price = prices
    fair_home, fair_draw, fair_away = _safe_devig([1 / home_price, 1 / draw_price, 1 / away_price])
    p = fair_home if target == "home" else fair_away
    return p, f"Match 1X2 median {home_price:g}/{draw_price:g}/{away_price:g}; de-vig {target} win = {p*100:.1f}%", "h2h"


def _halftime_result(book: MarketBook, subtype: str, target: str | None) -> tuple[float, str, str] | None:
    home = book.consensus_price("h2h_h1", book.home)
    draw = book.consensus_price("h2h_h1", "Draw")
    away = book.consensus_price("h2h_h1", book.away)
    if not (home and draw and away):
        return None
    fair_home, fair_draw, fair_away = _safe_devig([1 / home, 1 / draw, 1 / away])
    if subtype == "halftime_tied":
        return fair_draw, f"1H 1X2 median {home:g}/{draw:g}/{away:g}; de-vig halftime draw = {fair_draw*100:.1f}%", "h2h_h1:draw"
    p = fair_home if target == "home" else fair_away
    return p, f"1H 1X2 median {home:g}/{draw:g}/{away:g}; de-vig {target} HT lead = {p*100:.1f}%", f"h2h_h1:{target}"


def _player_name(question: str) -> str:
    prefix = re.sub(r"^\s*will\s+", "", question, flags=re.IGNORECASE).strip()
    return re.split(r"\s+have at least|\s+score or assist|\s+score a goal", prefix, flags=re.IGNORECASE)[0].strip()


def _player_sot(book: MarketBook, question: str, time_scope: str) -> tuple[int | None, str, str, str | None]:
    player = _player_name(question)
    if time_scope != "regulation":
        return (
            None,
            "STAY AWAY",
            "No pullable market path for player 1+ SoT in this time scope.",
            None,
        )
    pair = book.two_way_prices("player_shots_on_target", point=0.5, description=player)
    if pair:
        over, under = pair
        p = _safe_devig([1 / over, 1 / under])[0]
        return _round_pct(p), "Direct", f"Player SoT O/U 0.5 {over:g}/{under:g}; de-vig = {p*100:.1f}%.", f"player_sot:{norm_name(player)}:0.5"
    one_sided = book.preferred_prop_price("player_shots_on_target", "Over", point=0.5, description=player)
    if one_sided:
        p = _raw_minus_haircut(one_sided.price)
        return _round_pct(p), "Direct", f"{one_sided.bookmaker} player SoT O0.5 {one_sided.price:g}; one-sided haircut {config.ONE_SIDED_PROP_HAIRCUT_PCT:g} pts -> {p*100:.1f}%.", f"player_sot:{norm_name(player)}:0.5:{one_sided.bookmaker}"
    return (
        config.MISSING_PLAYER_SOT_FALLBACK_PCT,
        "Fallback",
        "No pullable player SoT market found; default missing-line player SoT probability = 15%. Verify lineup/status before submitting.",
        f"missing_player_sot:{norm_name(player)}",
    )


def _team_sot_ladder_mu(book: MarketBook, team: str) -> tuple[float, str] | None:
    thresholds: list[int] = []
    probs: list[float] = []
    for point in book.available_points("team_shots_on_target", description=team):
        threshold = int(point + 0.5)
        pair = book.two_way_prices("team_shots_on_target", point=point, description=team)
        if pair:
            over, under = pair
            p = _safe_devig([1 / over, 1 / under])[0]
        else:
            pp = book.preferred_prop_price("team_shots_on_target", "Over", point=point, description=team)
            if not pp:
                continue
            p = _raw_minus_haircut(pp.price)
        thresholds.append(threshold)
        probs.append(p)
    if not thresholds:
        return None
    mu = _fit_poisson_mean_from_ladder(thresholds, probs)
    return mu, f"{team} SoT ladder mu={mu:.2f}"


def _shots_comparison_2h(book: MarketBook, question: str) -> tuple[float, str, str] | None:
    subj = _which_subject_team(question, book.home, book.away)
    home_fit = _team_sot_ladder_mu(book, book.home)
    away_fit = _team_sot_ladder_mu(book, book.away)
    if not home_fit or not away_fit:
        return None
    home_mu, home_txt = home_fit
    away_mu, away_txt = away_fit
    home_2h = home_mu * config.SECOND_HALF_SOT_SHARE
    away_2h = away_mu * config.SECOND_HALF_SOT_SHARE
    p_home_gt = _poisson_p_a_greater_b(home_2h, away_2h)
    p = p_home_gt if subj == "home" else 1 - p_home_gt - _poisson_draw_prob(home_2h, away_2h)
    who = book.home if subj == "home" else book.away
    return p, f"SoT ladder fit: {home_txt}, {away_txt}; scale to 2H at {config.SECOND_HALF_SOT_SHARE*100:.0f}%; Poisson {who} > opponent = {p*100:.1f}%.", "team_sot_ladders:2h_comparison"


def _poisson_draw_prob(mu_a: float, mu_b: float, kmax: int = 30) -> float:
    total = 0.0
    for k in range(kmax + 1):
        total += math.exp(-mu_a) * mu_a**k / math.factorial(k) * math.exp(-mu_b) * mu_b**k / math.factorial(k)
    return total


def resolve_question(item: dict[str, Any], book: MarketBook) -> Decision:
    n = item["normalized"]
    question = item["question"]
    number = item["number"]
    fam = n.get("question_family")
    sub = n.get("question_subtype")
    target = n.get("target_team_or_side")
    threshold = n.get("threshold_value")
    time_scope = n.get("time_scope")

    result: tuple[float, str, str] | None = None
    tier = "Direct"

    if fam == "match_result" and sub == "team_win" and target in {"home", "away"}:
        result = _match_win(book, target)
    elif fam == "halftime" and sub in {"halftime_tied", "halftime_team_winning"}:
        result = _halftime_result(book, sub, target)
    elif fam == "goals_totals" and sub in {"total_goals_over", "total_goals_under"}:
        result = _total_goals_prob(book, sub, threshold)
    elif fam == "goals_totals" and sub == "btts_and_over":
        result = _btts_and_over(book)
        tier = "Derived"
    elif fam == "goals_totals" and sub == "team_scores":
        team = _target_team_name(n, book.home, book.away)
        if team:
            result = _team_total_prob(book, team, 1)
    elif fam == "goals_totals" and sub == "team_score_in_second_half":
        team = _target_team_name(n, book.home, book.away)
        if team:
            base = _team_total_prob(book, team, 1)
            if base:
                p, evidence, signature = base
                p2 = p * config.SECOND_HALF_GOAL_SHARE
                result = p2, f"{evidence}; 2H share {config.SECOND_HALF_GOAL_SHARE*100:.0f}% -> {p2*100:.1f}%", signature + ":2h"
                tier = "Derived"
    elif fam == "shots" and sub == "shots_comparison" and time_scope == "second_half":
        result = _shots_comparison_2h(book, question)
        tier = "Derived"
    elif fam == "player_markets" and sub == "player_shot_on_target":
        prob, source_tier, derivation, signature = _player_sot(book, question, time_scope)
        return Decision(number, question, prob, source_tier, derivation, signature)
    elif fam == "player_markets" and sub in {"player_goal_or_assist", "player_goal"}:
        return Decision(number, question, None, "STAY AWAY", "No pullable player goal/goal-or-assist market found.", None)
    elif fam == "fouls":
        return Decision(number, question, None, "STAY AWAY", "No true fouls market found; bookings proxy is intentionally not used.", None)
    elif fam == "offsides":
        return Decision(number, question, None, "STAY AWAY", "No true offsides market found.", None)

    if result:
        p, evidence, signature = result
        return Decision(number, question, _round_pct(p), tier, evidence, signature)
    return Decision(number, question, None, "STAY AWAY", f"No pullable market path for {fam}/{sub}.", None)


def apply_disappeared_line_review(decisions: list[Decision], previous_snapshot: dict[str, Any] | None) -> list[Decision]:
    if not previous_snapshot:
        return decisions
    previous_by_question = {d.get("question"): d for d in previous_snapshot.get("decisions", [])}
    for decision in decisions:
        prev = previous_by_question.get(decision.question)
        if not prev:
            continue
        prev_tier = prev.get("source_tier")
        if decision.source_tier == "STAY AWAY" and prev_tier in {"Direct", "Derived"} and prev.get("prob") is not None:
            decision.prob = prev.get("prob")
            decision.source_tier = "REVIEW"
            decision.derivation = (
                f"LINE DISAPPEARED after {previous_snapshot.get('snapshot_time', 'prior snapshot')}; "
                f"prior pulled price implied {prev.get('prob')}%. Verify before submitting. Previous derivation: {prev.get('derivation')}"
            )
            decision.signature = prev.get("signature")
    return decisions


def resolve_questions(questions: list[dict[str, Any]], book: MarketBook, previous_snapshot: dict[str, Any] | None = None) -> list[Decision]:
    decisions = [resolve_question(q, book) for q in questions]
    return apply_disappeared_line_review(decisions, previous_snapshot)
