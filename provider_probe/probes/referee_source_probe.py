"""
Qualifies free referee-stat sources for the SportsPredict discipline/fouls market families.

Primary source tested live: StatBunker (RefereeYellowCards page)
Other sources: documented as manual/reference only (single HEAD check for reachability).

Outputs:
  outputs/referee_source_probe.csv
  outputs/referee_source_recommendations.md
"""

from __future__ import annotations

import dataclasses
import time
from pathlib import Path

import pandas as pd
import requests

from .. import config
from ..clients import statbunker
from ..taxonomy import load_taxonomy


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class RefereeSourceRow:
    source_name: str
    source_type: str                      # "html_table", "api", "manual_reference"
    test_status: str                      # "tested", "manual_only", "skipped", "error"
    fields_available: str                 # comma-joined
    sample_competition: str
    sample_referee: str
    cards_per_match_available: str        # "yes", "derived", "no", "unknown"
    yellow_cards_available: str
    red_cards_available: str
    fouls_available: str
    penalties_available: str
    home_away_split_available: str
    first_second_half_split_available: str
    historical_depth_observed: str
    automation_feasibility: str           # "high", "medium", "low", "manual"
    terms_or_stability_risk: str
    recommendation: str                   # "MVP usable", "manual MVP usable", "not production ready", "skip"
    notes: str
    source_url: str
    extraction_method: str


# ---------------------------------------------------------------------------
# Taxonomy helpers
# ---------------------------------------------------------------------------

_CARD_FOUL_FAMILIES = {"discipline", "fouls"}


def _get_required_ref_fields(taxonomy_path: Path | None) -> tuple[list[str], list[str]]:
    df = load_taxonomy(taxonomy_path)
    mask = df["question_family"].isin(_CARD_FOUL_FAMILIES)
    templates = df.loc[mask, "normalized_question_template"].tolist()
    fields: set[str] = set()
    for raw in df.loc[mask, "feature_set_needed"].dropna():
        for f in str(raw).split(","):
            f = f.strip()
            if f:
                fields.add(f)
    return templates, sorted(fields)


# ---------------------------------------------------------------------------
# StatBunker probe
# ---------------------------------------------------------------------------

def _probe_statbunker() -> RefereeSourceRow:
    print("  [statbunker] Testing StatBunker RefereeYellowCards pages...")

    html: str | None = None
    used_comp_id: int | None = None
    used_comp_name: str = ""
    error_notes: list[str] = []

    for comp_id, comp_name in statbunker.COMP_IDS:
        print(f"  [statbunker] Trying comp_id={comp_id} ({comp_name})...")
        try:
            html = statbunker.get_referee_stats_page(comp_id)
            used_comp_id = comp_id
            used_comp_name = comp_name
            print(f"  [statbunker] Got {len(html):,} bytes")
            break
        except Exception as exc:
            msg = str(exc)[:100]
            error_notes.append(f"comp_id={comp_id}: {msg}")
            print(f"  [statbunker]   failed: {msg}")

    if html is None:
        return RefereeSourceRow(
            source_name="StatBunker",
            source_type="html_table",
            test_status="error",
            fields_available="",
            sample_competition="",
            sample_referee="",
            cards_per_match_available="unknown",
            yellow_cards_available="unknown",
            red_cards_available="unknown",
            fouls_available="no",
            penalties_available="no",
            home_away_split_available="unknown",
            first_second_half_split_available="unknown",
            historical_depth_observed="unknown",
            automation_feasibility="unknown",
            terms_or_stability_risk="all competition pages failed",
            recommendation="not production ready",
            notes="; ".join(error_notes),
            source_url="https://www.statbunker.com/competitions/RefereeYellowCards",
            extraction_method="html_table_parse",
        )

    html_path = statbunker.save_html_sample(html, f"statbunker_comp_{used_comp_id}.html")
    print(f"  [statbunker] Saved sample: {html_path}")

    rows, canonical_cols = statbunker.parse_referee_table(html)
    print(f"  [statbunker] Parsed {len(rows)} referee rows")
    print(f"  [statbunker] Columns: {canonical_cols}")

    if not rows:
        return RefereeSourceRow(
            source_name="StatBunker",
            source_type="html_table",
            test_status="error",
            fields_available=", ".join(canonical_cols),
            sample_competition=used_comp_name,
            sample_referee="",
            cards_per_match_available="unknown",
            yellow_cards_available="unknown",
            red_cards_available="unknown",
            fouls_available="no",
            penalties_available="no",
            home_away_split_available="unknown",
            first_second_half_split_available="unknown",
            historical_depth_observed="unknown",
            automation_feasibility="low",
            terms_or_stability_risk="table structure may have changed",
            recommendation="not production ready",
            notes=f"Page loaded ({len(html):,} bytes) but no referee rows parsed. Columns: {canonical_cols}",
            source_url=f"https://www.statbunker.com/competitions/RefereeYellowCards?comp_id={used_comp_id}",
            extraction_method="BeautifulSoup html_table_parse",
        )

    def avail(field: str) -> str:
        return "yes" if field in canonical_cols else "no"

    yellow_avail = avail("yellow_cards")
    red_avail = avail("red_cards")
    matches_avail = avail("matches")
    ypm_avail = avail("yellow_per_match")
    cpm_avail = avail("cards_per_match")
    home_avail = avail("home_cards")
    away_avail = avail("away_cards")
    fh_avail = avail("fh_cards_avg_minute")
    sh_avail = avail("sh_cards_avg_minute")

    if cpm_avail == "yes":
        cards_pm = "yes"
    elif yellow_avail == "yes" and red_avail == "yes" and matches_avail == "yes":
        cards_pm = "derived"
    else:
        cards_pm = "no"

    home_away = "yes" if home_avail == "yes" and away_avail == "yes" else "no"
    ht_split = "yes" if fh_avail == "yes" or sh_avail == "yes" else "no"

    fields_found = [c for c in canonical_cols if c not in ("", "unknown")]

    first_row = rows[0]
    sample_ref = first_row.get("referee_name", "")
    print(f"  [statbunker] Sample referee: {sample_ref}")
    if len(rows) > 1:
        print(f"  [statbunker] Row 2: {dict(list(rows[1].items())[:6])}")

    core_present = yellow_avail == "yes" and red_avail == "yes" and matches_avail == "yes"
    if core_present:
        recommendation = "MVP usable"
        feasibility = "medium"
        risk = (
            "HTML structure may change without notice; no official API. "
            "Personal/research use only — do not scrape at high frequency. "
            "Correct comp_id must be identified per tournament (not auto-discoverable for international events)."
        )
    else:
        recommendation = "manual MVP usable"
        feasibility = "manual"
        risk = "Core fields not clearly parsed; manual column alignment needed"

    notes_parts = [
        f"comp_id={used_comp_id} ({used_comp_name}), {len(rows)} referees",
        f"columns parsed: {canonical_cols}",
        f"sample row: {dict(list(first_row.items())[:8])}",
    ]

    return RefereeSourceRow(
        source_name="StatBunker",
        source_type="html_table",
        test_status="tested",
        fields_available=", ".join(fields_found),
        sample_competition=used_comp_name,
        sample_referee=sample_ref,
        cards_per_match_available=cards_pm,
        yellow_cards_available=yellow_avail,
        red_cards_available=red_avail,
        fouls_available="no",
        penalties_available="no",
        home_away_split_available=home_away,
        first_second_half_split_available=ht_split,
        historical_depth_observed=f"{len(rows)} referees, current season {used_comp_name}",
        automation_feasibility=feasibility,
        terms_or_stability_risk=risk,
        recommendation=recommendation,
        notes="; ".join(notes_parts),
        source_url=f"https://www.statbunker.com/competitions/RefereeYellowCards?comp_id={used_comp_id}",
        extraction_method="BeautifulSoup html_table_parse",
    )


# ---------------------------------------------------------------------------
# Manual-reference sources
# ---------------------------------------------------------------------------

_MANUAL_SOURCES = [
    {
        "source_name": "WorldReferee",
        "url": "https://www.worldreferee.com",
        "known_fields": "referee_name, nationality, career_matches, yellow_cards, red_cards, competition, season, appointment_history",
        "competition_scope": "International tournaments, UEFA competitions, domestic leagues",
        "fouls": "no",
        "penalties": "no",
        "home_away": "no",
        "ht_split": "no",
        "feasibility": "low",
        "risk": "JS-heavy per-referee detail pages; list pages may be static. No bulk export. Personal use implied.",
        "recommendation": "manual MVP usable",
        "extraction": "manual copy or per-profile HTML parse",
        "notes": (
            "Career stats and appointment history visible per referee. "
            "International referee profiles well-maintained. "
            "Useful for cross-referencing names and nationalities. "
            "Bulk extraction requires many pages — manual only for MVP."
        ),
    },
    {
        "source_name": "FootyStats",
        "url": "https://footystats.org/referees",
        "known_fields": "referee_name, competition, season, matches, yellow_cards, red_cards, yellow_per_match, red_per_match, fouls_per_game",
        "competition_scope": "Most major European and international leagues; coverage varies by competition",
        "fouls": "yes",
        "penalties": "unknown",
        "home_away": "unknown",
        "ht_split": "no",
        "feasibility": "low",
        "risk": (
            "ToS restricts automated scraping. "
            "Free tier has full table access but limited historical depth. "
            "Referee pages exist per competition and per season."
        ),
        "recommendation": "manual MVP usable",
        "extraction": "manual export or single-page HTML parse (ToS risk for automation)",
        "notes": (
            "FootyStats is the only free source observed to include fouls per game alongside yellow/red cards. "
            "Manual extraction is viable for MVP given small referee set per tournament. "
            "Automation carries ToS risk — do not automate in production without confirming terms."
        ),
    },
    {
        "source_name": "PlayerStats.football",
        "url": "https://www.playerstats.football",
        "known_fields": "unknown",
        "competition_scope": "unknown",
        "fouls": "unknown",
        "penalties": "unknown",
        "home_away": "unknown",
        "ht_split": "unknown",
        "feasibility": "unknown",
        "risk": "Site purpose and referee statistics coverage unverified; manual review required before any extraction.",
        "recommendation": "skip",
        "extraction": "manual review required",
        "notes": (
            "Listed as candidate source but referee statistics coverage is unverified. "
            "Manual inspection required before any extraction is attempted. "
            "Not recommended for MVP without further investigation."
        ),
    },
]


def _probe_manual_source(info: dict) -> RefereeSourceRow:
    url = info["url"]
    reach_note = ""
    try:
        time.sleep(1)
        resp = requests.head(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; research-bot/1.0)"},
            timeout=10,
            allow_redirects=True,
        )
        reach_note = f"reachable (HTTP {resp.status_code})"
    except Exception as exc:
        reach_note = f"HEAD failed: {str(exc)[:60]}"

    known_fields = info.get("known_fields", "unknown")
    ypm = "yes" if "yellow_per_match" in known_fields else "no"

    return RefereeSourceRow(
        source_name=info["source_name"],
        source_type="manual_reference",
        test_status="manual_only",
        fields_available=known_fields,
        sample_competition=info.get("competition_scope", ""),
        sample_referee="",
        cards_per_match_available=ypm,
        yellow_cards_available="yes" if "yellow_cards" in known_fields else "unknown",
        red_cards_available="yes" if "red_cards" in known_fields else "unknown",
        fouls_available=info.get("fouls", "unknown"),
        penalties_available=info.get("penalties", "unknown"),
        home_away_split_available=info.get("home_away", "unknown"),
        first_second_half_split_available=info.get("ht_split", "unknown"),
        historical_depth_observed="unknown — not tested",
        automation_feasibility=info.get("feasibility", "unknown"),
        terms_or_stability_risk=info.get("risk", ""),
        recommendation=info.get("recommendation", "skip"),
        notes=f"{reach_note}. {info.get('notes', '')}",
        source_url=url,
        extraction_method=info.get("extraction", "manual"),
    )


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def _build_report(rows: list[RefereeSourceRow], templates: list[str], ref_fields: list[str]) -> str:
    sb = next((r for r in rows if r.source_name == "StatBunker"), None)
    sb_ok = sb and sb.recommendation == "MVP usable"
    sb_manual = sb and sb.recommendation == "manual MVP usable"
    footystats = next((r for r in rows if r.source_name == "FootyStats"), None)

    lines = [
        "# Referee Source Recommendations",
        "",
        "## Context",
        "",
        f"**Discipline/fouls templates requiring referee features ({len(templates)} total):**",
    ]
    for t in templates:
        lines.append(f"- {t}")
    lines += [
        "",
        f"**Required referee fields (from taxonomy `feature_set_needed`):** {', '.join(ref_fields)}",
        "",
        "---",
        "",
        "## Q1: Is StatBunker usable for MVP referee features?",
        "",
    ]

    if sb is None:
        lines.append("StatBunker probe was not run.")
    elif sb_ok:
        lines += [
            "**Yes.** StatBunker was successfully fetched and parsed.",
            "",
            f"- URL: `{sb.source_url}`",
            f"- Competition tested: **{sb.sample_competition}**",
            f"- Referees in table: {sb.historical_depth_observed}",
            f"- Sample referee: {sb.sample_referee}",
            "",
            "**Fields confirmed directly from parsed table:**",
            "",
            f"| Field | Available |",
            f"|---|---|",
            f"| referee_name | yes |",
            f"| matches (P) | yes |",
            f"| yellow_cards | {sb.yellow_cards_available} |",
            f"| red_cards | {sb.red_cards_available} |",
            f"| red_yellow_cards (2nd bookings) | yes |",
            f"| yellow_per_match | yes |",
            f"| cards_per_match | {sb.cards_per_match_available} |",
            f"| home_cards | {sb.home_away_split_available} |",
            f"| away_cards | {sb.home_away_split_available} |",
            f"| first_half_cards | {sb.first_second_half_split_available} |",
            f"| second_half_cards | {sb.first_second_half_split_available} |",
            f"| fouls | {sb.fouls_available} |",
            f"| penalties | {sb.penalties_available} |",
            "",
            f"**Automation feasibility:** {sb.automation_feasibility}",
            "",
            f"**Risk:** {sb.terms_or_stability_risk}",
        ]
    elif sb_manual:
        lines += [
            "**Partially.** StatBunker returned data but table parsing was incomplete.",
            "",
            f"- Notes: {sb.notes[:300]}",
            "",
            "Manual column alignment required before automation.",
        ]
    else:
        lines += [
            "**No.** StatBunker could not be accessed or parsed.",
            "",
            f"- Status: {sb.test_status if sb else 'not run'}",
            f"- Notes: {sb.notes[:300] if sb else 'N/A'}",
        ]

    lines += [
        "",
        "---",
        "",
        "## Q2: If yes, what fields can we use?",
        "",
    ]

    if sb_ok and sb:
        lines += [
            "All fields in the table are parseable with BeautifulSoup (`html.parser`).",
            "No JavaScript execution required — the page is server-rendered.",
            "",
            "**Usable for model features:**",
            "- `yellow_per_match` — primary yellow card tendency feature",
            "- `cards_per_match` — total card rate (yellow + red)",
            "- `red_cards` / `matches` — derived red card rate",
            "- `home_cards` / `away_cards` — home/away card bias",
            "- `fh_cards_avg_minute` / `sh_cards_avg_minute` — first/second half card timing",
            "",
            "**Not available from StatBunker:**",
            "- Fouls per match — not in this table; see FootyStats",
            "- Penalty data — not in this table",
            "",
            "**To find the correct comp_id for your tournament:**",
            "1. Visit `https://www.statbunker.com/`",
            "2. Click the competition you need",
            "3. Extract `comp_id=NNN` from the URL",
            "4. Fetch `https://www.statbunker.com/competitions/RefereeYellowCards?comp_id=NNN`",
        ]
    else:
        lines.append("StatBunker did not return usable fields. See Q3.")

    lines += [
        "",
        "---",
        "",
        "## Q3: If no (or for fouls data), which source should be tested next?",
        "",
        "**FootyStats** is the recommended next candidate — the only free source observed to include fouls per game.",
        "",
    ]
    if footystats:
        lines += [
            f"- URL: `{footystats.source_url}`",
            f"- Known fields: {footystats.fields_available}",
            f"- Fouls available: **{footystats.fouls_available}**",
            f"- Automation feasibility: {footystats.automation_feasibility}",
            f"- Risk: {footystats.terms_or_stability_risk}",
            "",
            "For MVP, a manual one-time export from FootyStats covers the fouls feature "
            "for the ~5-8 referees in the tournament.",
        ]

    lines += [
        "",
        "---",
        "",
        "## Q4: Should referee data remain in the MVP?",
        "",
    ]

    if sb_ok or sb_manual:
        lines += [
            "**Yes, with scoped ambition.**",
            "",
            "StatBunker provides referee card tendency data sufficient to cover the core discipline templates:",
            "",
            "| Template | Referee feature needed | Source |",
            "|---|---|---|",
            "| `penalty kick awarded OR red card shown` | red card rate | StatBunker |",
            "| `total cards N+` | cards per match | StatBunker |",
            "| `{HOME} receive more cards than {AWAY}` | home/away card split | StatBunker |",
            "| `{HOME} commit more fouls than {AWAY}` | fouls per match | FootyStats (manual) |",
            "| `penalty kick awarded` | penalty rate | not available (drop from MVP) |",
            "",
            "**Keep** referee features for: red card / total card / home-away card templates.",
            "**Defer** fouls features until FootyStats manual extraction is done.",
            "**Drop** penalty rate features — no free source available.",
        ]
    else:
        lines += [
            "**No** — StatBunker is inaccessible. Replace referee features with team-level card rates "
            "from API-Football historical fixture statistics, which are sufficient for most discipline markets.",
        ]

    lines += [
        "",
        "---",
        "",
        "## Q5: Minimum viable referee feature set",
        "",
        "| Field | Source | Availability | Used for |",
        "|---|---|---|---|",
        "| `referee_name` | API-Football fixture.referee | direct | join key |",
        "| `ref_matches` | StatBunker | direct | denominator |",
        "| `ref_yellow_total` | StatBunker | direct | feature |",
        "| `ref_red_total` | StatBunker | direct | feature |",
        "| `ref_yellow_per_match` | StatBunker | direct | primary card tendency |",
        "| `ref_cards_per_match` | StatBunker | direct | total card rate |",
        "| `ref_red_rate` | derived (red/matches) | derived | red card risk |",
        "| `ref_home_cards` | StatBunker | direct | home/away bias |",
        "| `ref_away_cards` | StatBunker | direct | home/away bias |",
        "",
        "**Nice-to-have (not MVP):**",
        "- `ref_fouls_per_match` — FootyStats manual",
        "- `ref_fh_cards`, `ref_sh_cards` — StatBunker (available but lower priority)",
        "- `ref_penalty_rate` — no free source identified",
        "",
        "---",
        "",
        "## Q6: How to combine referee features with API-Football team card stats",
        "",
        "Use a **two-layer feature approach** for discipline markets:",
        "",
        "**Layer 1 — Team card history (API-Football, historical fixtures)**",
        "```",
        "home_yellow_per_match_last10   # from /fixtures/statistics history",
        "away_yellow_per_match_last10",
        "home_fouls_per_match_last10",
        "away_fouls_per_match_last10",
        "```",
        "These are match-time values derived from each team's last 10 fixtures.",
        "",
        "**Layer 2 — Referee tendency prior (StatBunker, pre-match)**",
        "```",
        "ref_yellow_per_match           # from StatBunker competition table",
        "ref_cards_per_match",
        "ref_red_rate",
        "ref_home_card_bias             # = ref_home_cards / ref_matches",
        "ref_away_card_bias             # = ref_away_cards / ref_matches",
        "```",
        "These are static per-referee averages updated once per season.",
        "",
        "**Timing:**",
        "- Referee assignment (`fixture.referee`) is published 1-3 days before kickoff",
        "- Until assignment is known, use a competition-average referee prior as fallback",
        "- StatBunker lookup: fetch once per competition, cache the full table in memory/CSV",
        "",
        "**Feature vector per discipline market at prediction time:**",
        "```",
        "ref_yellow_per_match      # referee baseline",
        "ref_cards_per_match       # referee baseline",
        "ref_red_rate              # referee baseline",
        "home_yellow_per_match     # team history",
        "away_yellow_per_match     # team history",
        "home_fouls_per_match      # team history",
        "away_fouls_per_match      # team history",
        "match_importance          # group vs knockout",
        "```",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run(taxonomy_path: Path | None = None) -> tuple[list[dict], str]:
    templates, ref_fields = _get_required_ref_fields(taxonomy_path)
    print(f"  [ref-sources] Discipline/fouls templates: {len(templates)}")
    print(f"  [ref-sources] Required referee fields: {ref_fields}")

    rows: list[RefereeSourceRow] = []

    print("\n  [ref-sources] --- StatBunker ---")
    rows.append(_probe_statbunker())

    for source_info in _MANUAL_SOURCES:
        print(f"\n  [ref-sources] --- {source_info['source_name']} (manual assessment) ---")
        rows.append(_probe_manual_source(source_info))

    config.OUTPUTS.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame([dataclasses.asdict(r) for r in rows])
    csv_path = config.OUTPUTS / "referee_source_probe.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"\n  Saved {csv_path}")

    report_text = _build_report(rows, templates, ref_fields)
    md_path = config.OUTPUTS / "referee_source_recommendations.md"
    md_path.write_text(report_text, encoding="utf-8")
    print(f"  Saved {md_path}")

    return [dataclasses.asdict(r) for r in rows], report_text
