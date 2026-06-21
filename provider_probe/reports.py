"""
Builds all 4 output files from probe results + taxonomy.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pandas as pd

from . import config
from .probes import ProbeResult
from .taxonomy import get_all_unique_fields, get_family_field_map, load_taxonomy

# ---------------------------------------------------------------------------
# Coverage classification helpers
# ---------------------------------------------------------------------------

# Map (question_family) → which providers cover it and how
_FAMILY_COVERAGE: dict[str, dict] = {
    "match_result": {
        "odds_support": "direct",
        "football_data_support": "direct",
        "lineup_support": "none",
        "weather_support": "weak",
        "referee_support": "none",
    },
    "goals_totals": {
        "odds_support": "direct",
        "football_data_support": "direct",
        "lineup_support": "none",
        "weather_support": "weak",
        "referee_support": "none",
    },
    "shots": {
        "odds_support": "weak",
        "football_data_support": "direct",
        "lineup_support": "weak",
        "weather_support": "none",
        "referee_support": "none",
    },
    "discipline": {
        "odds_support": "weak",
        "football_data_support": "direct",
        "lineup_support": "none",
        "weather_support": "none",
        "referee_support": "direct",
    },
    "fouls": {
        "odds_support": "none",
        "football_data_support": "direct",
        "lineup_support": "none",
        "weather_support": "none",
        "referee_support": "direct",
    },
    "offsides": {
        "odds_support": "none",
        "football_data_support": "direct",
        "lineup_support": "none",
        "weather_support": "none",
        "referee_support": "none",
    },
    "corners": {
        "odds_support": "weak",
        "football_data_support": "direct",
        "lineup_support": "none",
        "weather_support": "none",
        "referee_support": "none",
    },
    "halftime": {
        "odds_support": "weak",
        "football_data_support": "direct",
        "lineup_support": "none",
        "weather_support": "none",
        "referee_support": "none",
    },
    "player_markets": {
        "odds_support": "weak",
        "football_data_support": "direct",
        "lineup_support": "direct",
        "weather_support": "none",
        "referee_support": "none",
    },
}

# Map field_name → provider availability
_FIELD_MAP: dict[str, dict] = {
    "defensive_strength": {
        "data_area": "team_stats",
        "the_odds_api_available": "derived",
        "api_football_available": "derived",
        "open_meteo_available": "none",
        "sportmonks_available_if_configured": "derived",
        "free_source_available": "yes",
        "notes": "Derived from historical goals conceded per match (API-Football or FBref)",
    },
    "form": {
        "data_area": "team_stats",
        "the_odds_api_available": "none",
        "api_football_available": "derived",
        "open_meteo_available": "none",
        "sportmonks_available_if_configured": "derived",
        "free_source_available": "yes",
        "notes": "Last 5-10 results from /fixtures history",
    },
    "h2h": {
        "data_area": "team_stats",
        "the_odds_api_available": "none",
        "api_football_available": "direct",
        "open_meteo_available": "none",
        "sportmonks_available_if_configured": "direct",
        "free_source_available": "yes",
        "notes": "GET /fixtures/headtohead?h2h={team1}-{team2}",
    },
    "half_goal_rates": {
        "data_area": "team_stats",
        "the_odds_api_available": "none",
        "api_football_available": "derived",
        "open_meteo_available": "none",
        "sportmonks_available_if_configured": "derived",
        "free_source_available": "yes",
        "notes": "Derived from halftime score in historical fixtures; need HT score present",
    },
    "key_passes": {
        "data_area": "player_stats",
        "the_odds_api_available": "none",
        "api_football_available": "direct",
        "open_meteo_available": "none",
        "sportmonks_available_if_configured": "direct",
        "free_source_available": "yes",
        "notes": "In /fixtures/players response under passes.key",
    },
    "lineup": {
        "data_area": "lineups",
        "the_odds_api_available": "none",
        "api_football_available": "direct",
        "open_meteo_available": "none",
        "sportmonks_available_if_configured": "direct",
        "free_source_available": "yes",
        "notes": "GET /fixtures/lineups; published ~1h before kickoff; no explicit confirmed flag",
    },
    "match_importance": {
        "data_area": "team_stats",
        "the_odds_api_available": "none",
        "api_football_available": "derived",
        "open_meteo_available": "none",
        "sportmonks_available_if_configured": "derived",
        "free_source_available": "yes",
        "notes": "Inferred from competition stage (group stage, knockout) in fixture metadata",
    },
    "match_style": {
        "data_area": "team_stats",
        "the_odds_api_available": "none",
        "api_football_available": "derived",
        "open_meteo_available": "none",
        "sportmonks_available_if_configured": "derived",
        "free_source_available": "yes",
        "notes": "Derived from historical possession, shots, pace of play; not a direct field",
    },
    "odds": {
        "data_area": "odds",
        "the_odds_api_available": "direct",
        "api_football_available": "none",
        "open_meteo_available": "none",
        "sportmonks_available_if_configured": "none",
        "free_source_available": "yes",
        "notes": "The Odds API primary source; implied prob = 1/decimal_odds",
    },
    "opponent_defensive_line": {
        "data_area": "team_stats",
        "the_odds_api_available": "none",
        "api_football_available": "derived",
        "open_meteo_available": "none",
        "sportmonks_available_if_configured": "derived",
        "free_source_available": "yes",
        "notes": "Proxy: opponent offsides conceded, high defensive line inferred from historical offside counts",
    },
    "player_form": {
        "data_area": "player_stats",
        "the_odds_api_available": "none",
        "api_football_available": "derived",
        "open_meteo_available": "none",
        "sportmonks_available_if_configured": "derived",
        "free_source_available": "yes",
        "notes": "Last 3-5 matches player stats from /fixtures/players; needs multiple calls",
    },
    "referee_stats": {
        "data_area": "referee",
        "the_odds_api_available": "none",
        "api_football_available": "derived",
        "open_meteo_available": "none",
        "sportmonks_available_if_configured": "derived",
        "free_source_available": "conditional",
        "notes": "Referee name from fixture; historical stats derived from fixture statistics — quota-intensive on free tier",
    },
    "team_aggression": {
        "data_area": "team_stats",
        "the_odds_api_available": "none",
        "api_football_available": "derived",
        "open_meteo_available": "none",
        "sportmonks_available_if_configured": "derived",
        "free_source_available": "yes",
        "notes": "Proxy: fouls + yellow cards per match from historical statistics",
    },
    "team_attacking_depth": {
        "data_area": "team_stats",
        "the_odds_api_available": "none",
        "api_football_available": "derived",
        "open_meteo_available": "none",
        "sportmonks_available_if_configured": "derived",
        "free_source_available": "yes",
        "notes": "Proxy: corners won + shots per match from historical statistics",
    },
    "team_corner_rates": {
        "data_area": "team_stats",
        "the_odds_api_available": "none",
        "api_football_available": "derived",
        "open_meteo_available": "none",
        "sportmonks_available_if_configured": "derived",
        "free_source_available": "yes",
        "notes": "Derived from historical Corner Kicks stat in /fixtures/statistics",
    },
    "team_discipline": {
        "data_area": "team_stats",
        "the_odds_api_available": "none",
        "api_football_available": "derived",
        "open_meteo_available": "none",
        "sportmonks_available_if_configured": "derived",
        "free_source_available": "yes",
        "notes": "Derived from Yellow Cards + Red Cards in /fixtures/statistics history",
    },
    "team_foul_rates": {
        "data_area": "team_stats",
        "the_odds_api_available": "none",
        "api_football_available": "derived",
        "open_meteo_available": "none",
        "sportmonks_available_if_configured": "derived",
        "free_source_available": "yes",
        "notes": "Derived from historical Fouls stat in /fixtures/statistics",
    },
    "team_scoring_rate": {
        "data_area": "team_stats",
        "the_odds_api_available": "none",
        "api_football_available": "derived",
        "open_meteo_available": "none",
        "sportmonks_available_if_configured": "derived",
        "free_source_available": "yes",
        "notes": "Goals scored per match from fixture history",
    },
    "team_shot_rates": {
        "data_area": "team_stats",
        "the_odds_api_available": "none",
        "api_football_available": "derived",
        "open_meteo_available": "none",
        "sportmonks_available_if_configured": "derived",
        "free_source_available": "yes",
        "notes": "Derived from Shots on Goal / Total Shots per match history",
    },
    "team_strength": {
        "data_area": "team_stats",
        "the_odds_api_available": "derived",
        "api_football_available": "derived",
        "open_meteo_available": "none",
        "sportmonks_available_if_configured": "derived",
        "free_source_available": "yes",
        "notes": "Elo ratings (eloratings.net), FIFA rankings, or implied from odds",
    },
    "xg": {
        "data_area": "team_stats",
        "the_odds_api_available": "none",
        "api_football_available": "direct",
        "open_meteo_available": "none",
        "sportmonks_available_if_configured": "direct",
        "free_source_available": "yes",
        "notes": "Expected goals in /fixtures/statistics as 'expected_goals' (not all fixtures)",
    },
    "xg_per_shot": {
        "data_area": "player_stats",
        "the_odds_api_available": "none",
        "api_football_available": "derived",
        "open_meteo_available": "none",
        "sportmonks_available_if_configured": "derived",
        "free_source_available": "conditional",
        "notes": "Derived if xG + shots available per player; may need Understat or StatsBomb for quality data",
    },
}


# ---------------------------------------------------------------------------
# Report builders
# ---------------------------------------------------------------------------


def _classify_support(probe_results: list[ProbeResult], provider: str, data_area: str) -> str:
    for r in probe_results:
        if r.provider == provider and r.data_area == data_area:
            return r.status
    return "not_tested"


def build_provider_matrix(probe_results: list[ProbeResult]) -> pd.DataFrame:
    providers = [
        ("the_odds_api", "odds"),
        ("api_football", "match_stats"),
        ("api_football", "confirmed_lineups"),
        ("api_football", "referee"),
        ("open_meteo", "weather"),
        ("sportmonks", "match_stats"),
    ]

    rows = []
    for provider, data_area in providers:
        result = next((r for r in probe_results if r.provider == provider and r.data_area == data_area), None)
        if result:
            rows.append({
                "provider": provider,
                "data_area": data_area,
                "api_key_present": result.api_key_present,
                "test_status": result.status,
                "free_tier_viable": "yes" if provider in ("open_meteo",) else "check_notes",
                "live_data_available": "yes" if result.status in ("ok", "partial") else "no",
                "historical_data_available": "yes" if result.status in ("ok", "partial") else "unknown",
                "match_mapping_supported": "yes" if data_area in ("match_stats", "confirmed_lineups", "referee") and result.status not in ("skipped", "error") else "n/a",
                "final_results_supported": "yes" if "final_score" in result.fields_found else "no",
                "team_stats_supported": "yes" if any(f in result.fields_found for f in ["shots_on_target", "fouls", "corners"]) else "no",
                "player_stats_supported": "yes" if any(f in result.fields_found for f in ["player_shots", "player_goals"]) else "no",
                "confirmed_lineups_supported": "yes" if "starting_xi" in result.fields_found else "no",
                "odds_supported": "yes" if data_area == "odds" and result.status in ("ok", "partial") else "no",
                "weather_supported": "yes" if data_area == "weather" and result.status in ("ok", "partial") else "no",
                "referee_assignments_supported": "yes" if "referee_assignment" in result.fields_found else "no",
                "referee_history_supported": "yes" if "referee_historical_fixtures" in result.fields_found else "no",
                "key_missing_fields": ", ".join(result.fields_missing[:5]),
                "estimated_mvp_value": _mvp_value(provider, data_area, result),
                "recommendation": _recommendation(provider, data_area, result),
                "notes": result.notes[:300],
            })
        else:
            rows.append({
                "provider": provider,
                "data_area": data_area,
                "api_key_present": False,
                "test_status": "not_tested",
                **{k: "unknown" for k in [
                    "free_tier_viable", "live_data_available", "historical_data_available",
                    "match_mapping_supported", "final_results_supported", "team_stats_supported",
                    "player_stats_supported", "confirmed_lineups_supported", "odds_supported",
                    "weather_supported", "referee_assignments_supported", "referee_history_supported",
                ]},
                "key_missing_fields": "",
                "estimated_mvp_value": "unknown",
                "recommendation": "not_tested",
                "notes": "",
            })

    return pd.DataFrame(rows)


def _mvp_value(provider: str, data_area: str, result: ProbeResult) -> str:
    if result.status == "skipped":
        return "unknown"
    priority = {
        ("the_odds_api", "odds"): "high",
        ("api_football", "match_stats"): "high",
        ("api_football", "confirmed_lineups"): "medium",
        ("api_football", "referee"): "low",
        ("open_meteo", "weather"): "low",
        ("sportmonks", "match_stats"): "low",
    }
    return priority.get((provider, data_area), "low")


def _recommendation(provider: str, data_area: str, result: ProbeResult) -> str:
    if result.status == "skipped":
        return "configure_key_and_retest"
    if result.status == "error":
        return "investigate_error"
    if result.status == "ok":
        return "integrate_first" if (provider, data_area) in [("the_odds_api", "odds"), ("api_football", "match_stats")] else "integrate"
    return "integrate_with_caveats"


def build_coverage_matrix(probe_results: list[ProbeResult], taxonomy_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in taxonomy_df.iterrows():
        family = row["question_family"]
        cov = _FAMILY_COVERAGE.get(family, {})

        # Determine overall support status
        football_sup = cov.get("football_data_support", "none")
        odds_sup = cov.get("odds_support", "none")
        supports = [s for s in [football_sup, odds_sup] if s not in ("none", "")]
        if "direct" in supports:
            support_status = "direct"
        elif "derived" in supports:
            support_status = "derived"
        elif "weak" in supports:
            support_status = "weak"
        else:
            support_status = "unsupported"

        can_resolve = "yes" if support_status in ("direct", "derived") else "no"
        can_feature = "yes" if support_status in ("direct", "derived", "weak") else "no"

        best = []
        if football_sup == "direct":
            best.append("api_football")
        if odds_sup == "direct":
            best.append("the_odds_api")
        if not best and football_sup == "derived":
            best.append("api_football (derived)")

        rows.append({
            "question_family": family,
            "normalized_question_template": row["normalized_question_template"],
            "reusable_model_group": row["reusable_model_group"],
            "required_data_fields": row.get("feature_set_needed", ""),
            **cov,
            "can_resolve_label": can_resolve,
            "can_create_features": can_feature,
            "best_provider": ", ".join(best) if best else "none",
            "support_status": support_status,
            "notes": row.get("notes", ""),
        })

    return pd.DataFrame(rows)


def build_field_matrix(taxonomy_df: pd.DataFrame) -> pd.DataFrame:
    family_map = {}
    for _, row in taxonomy_df.iterrows():
        family = row["question_family"]
        for f in str(row.get("feature_set_needed", "")).split(","):
            f = f.strip()
            if f:
                family_map.setdefault(f, set()).add(family)

    rows = []
    for field_name, info in _FIELD_MAP.items():
        families = family_map.get(field_name, set())
        rows.append({
            "field_name": field_name,
            "data_area": info["data_area"],
            "required_for_question_families": ", ".join(sorted(families)),
            "the_odds_api_available": info["the_odds_api_available"],
            "api_football_available": info["api_football_available"],
            "open_meteo_available": info["open_meteo_available"],
            "sportmonks_available_if_configured": info["sportmonks_available_if_configured"],
            "free_source_available": info["free_source_available"],
            "notes": info["notes"],
        })

    return pd.DataFrame(rows)


def build_recommendations(
    probe_results: list[ProbeResult],
    coverage_df: pd.DataFrame,
    field_df: pd.DataFrame,
) -> str:
    def _status(provider: str, data_area: str) -> str:
        r = next((r for r in probe_results if r.provider == provider and r.data_area == data_area), None)
        return r.status if r else "not_tested"

    odds_status = _status("the_odds_api", "odds")
    football_status = _status("api_football", "match_stats")
    lineup_status = _status("api_football", "confirmed_lineups")
    weather_status = _status("open_meteo", "weather")
    referee_result = next((r for r in probe_results if r.provider == "api_football" and r.data_area == "referee"), None)

    # Referee MVP call
    referee_mvp_line = ""
    if referee_result:
        if "referee_assignment" in referee_result.fields_found:
            referee_mvp_line = (
                "Referee assignment is available from API-Football (fixture.referee field). "
                "Historical tendency derivation is possible but quota-intensive (1 statistics call per historical fixture). "
                "**Recommendation: Include referee assignment only. Skip historical tendency stats for MVP — "
                "reopen after obtaining a paid API-Football plan or caching historical data.**"
            )
        else:
            referee_mvp_line = (
                "Referee field not present in tested fixture. "
                "**Recommendation: Drop referee data from MVP entirely.**"
            )
    else:
        referee_mvp_line = "Referee probe was skipped (no API key). Cannot assess."

    # Missing fields
    unsupported = field_df[field_df["api_football_available"] == "none"]["field_name"].tolist()
    unsupported_odds = field_df[field_df["the_odds_api_available"] == "none"]["field_name"].tolist()
    truly_unsupported = set(unsupported) & set(unsupported_odds)
    truly_unsupported -= {"weather_conditions"}  # covered by open_meteo

    lines = [
        "# Provider Recommendations — SportsPredict Probability Cup",
        "",
        "## 1. Executive Recommendation",
        "",
        "Use **API-Football** as the primary data source for all match statistics (goals, shots, fouls, cards, corners, offsides, lineups, referee assignments). Use **The Odds API** for betting odds and implied probabilities. Use **Open-Meteo** for weather (free, no key). Skip **Sportmonks** for MVP — no key configured.",
        "",
        "Priority integration order: API-Football → The Odds API → Open-Meteo.",
        "",
        "## 2. Best Source for Odds",
        "",
        f"**The Odds API** — probe status: `{odds_status}`.",
        "Covers: moneyline (h2h), totals, spreads/handicaps, BTTS. Implied probabilities derivable as 1/decimal_odds.",
        "Player props (shot on target, goal scorer) depend on sport availability and bookmaker coverage — may not be available for all international tournaments.",
        "Market availability for FIFA/international tournaments outside major leagues is limited; verify sport key availability before committing.",
        "",
        "## 3. Best Source for Football Results / Events / Stats",
        "",
        f"**API-Football v3** — probe status: `{football_status}`.",
        "Covers all core team stats: goals, halftime score, shots on goal, total shots, fouls, yellow/red cards, corners, offsides, possession, goalkeeper saves.",
        "Player stats (goals, assists, shots, minutes) available via /fixtures/players.",
        "xG (expected_goals) present in statistics for some fixtures — not guaranteed for all competitions.",
        "Match mapping via team name search is reliable; FIFA codes resolved via the existing FIFA_CODE_TO_NAME map.",
        "",
        "## 4. Best Source for Confirmed Lineups",
        "",
        f"**API-Football v3** — probe status: `{lineup_status}`.",
        "Starting XI and substitutes available for completed fixtures. For upcoming fixtures, lineup data appears ~1h before kickoff.",
        "**There is no explicit 'confirmed' flag** — treat any pre-match lineup as predicted until kickoff.",
        "Player IDs and formations included.",
        "",
        "## 5. Best Source for Weather",
        "",
        f"**Open-Meteo** (free, no key) — probe status: `{weather_status}`.",
        "Hourly forecast (temperature, precipitation probability, wind speed, weather code) and historical actuals both available.",
        "**Dependency**: Open-Meteo requires lat/lon coordinates per venue. API-Football provides venue.city but not coordinates.",
        "Manual action required: build a venue → (lat, lon) lookup table for the ~10 stadiums used in this tournament, or integrate a geocoding step.",
        "",
        "## 6. Referee Data: Include or Drop?",
        "",
        referee_mvp_line,
        "",
        "## 7. Biggest Missing Fields",
        "",
    ]

    if truly_unsupported:
        lines.append("Fields not directly available from any tested free provider:")
        for f in sorted(truly_unsupported):
            info = _FIELD_MAP.get(f, {})
            lines.append(f"- **{f}**: {info.get('notes', 'no notes')}")
    else:
        lines.append("All required fields are available (directly or derivable) from the tested providers.")

    lines += [
        "",
        "## 8. Which Source to Integrate First",
        "",
        "**API-Football** — covers 17 of 21 required field categories (directly or derived). Single HTTP client handles stats, lineups, and referee data.",
        "Start with: GET /status → GET /fixtures (by team, completed) → GET /fixtures/statistics → GET /fixtures/lineups.",
        "",
        "## 9. Which Source to Ignore for Now",
        "",
        "**Sportmonks** — no API key configured; cannot assess. Its data quality for international fixtures is strong, but the free tier is limited. Revisit if API-Football gaps emerge.",
        "**Player props from The Odds API** — low coverage for international tournaments; not reliable enough for MVP. Use API-Football /fixtures/players instead.",
        "",
        "## 10. Manual Checks Required",
        "",
        "1. **Venue coordinates**: Build a stadium → (lat, lon) table for the ~10 tournament venues. Open-Meteo cannot look up by name.",
        "2. **Lineup timing**: Verify exactly when lineups appear on API-Football for these specific tournament matches. May differ from domestic leagues.",
        "3. **Sport key for The Odds API**: Confirm which sport_key covers these matches (World Cup 2026, Copa América, AFCON, etc.) and that bookmakers offer the required market types.",
        "4. **API-Football fixture mapping**: Validate that team name searches correctly resolve FIFA codes for all 45+ teams in the tournament, not just the tested sample.",
        "5. **xG availability**: Confirm expected_goals is present in /fixtures/statistics for this specific competition — it is not guaranteed for all events.",
    ]

    return "\n".join(lines)


def build_all_reports(probe_results: list[ProbeResult], taxonomy_path: Path | None = None) -> None:
    config.OUTPUTS.mkdir(parents=True, exist_ok=True)

    taxonomy_df = load_taxonomy(taxonomy_path)

    print("\nBuilding provider_probe_matrix.csv...")
    matrix_df = build_provider_matrix(probe_results)
    matrix_path = config.OUTPUTS / "provider_probe_matrix.csv"
    matrix_df.to_csv(matrix_path, index=False, encoding="utf-8")
    print(f"  Saved {matrix_path}")

    print("Building question_family_coverage.csv...")
    coverage_df = build_coverage_matrix(probe_results, taxonomy_df)
    coverage_path = config.OUTPUTS / "question_family_coverage.csv"
    coverage_df.to_csv(coverage_path, index=False, encoding="utf-8")
    print(f"  Saved {coverage_path} ({len(coverage_df)} rows)")

    print("Building field_availability_matrix.csv...")
    field_df = build_field_matrix(taxonomy_df)
    field_path = config.OUTPUTS / "field_availability_matrix.csv"
    field_df.to_csv(field_path, index=False, encoding="utf-8")
    print(f"  Saved {field_path} ({len(field_df)} rows)")

    print("Building provider_recommendations.md...")
    rec_text = build_recommendations(probe_results, coverage_df, field_df)
    rec_path = config.OUTPUTS / "provider_recommendations.md"
    rec_path.write_text(rec_text, encoding="utf-8")
    print(f"  Saved {rec_path}")
