"""
Probe API-Football for referee data coverage.
"""

from __future__ import annotations

from .. import config
from ..clients import api_football as client
from . import ProbeResult

COMPLETED_FIXTURE_ID = 855751


def run() -> ProbeResult:
    key_present = bool(config.FOOTBALL_DATA_API_KEY)
    if not key_present:
        print("  [referee] FOOTBALL_DATA_API_KEY missing — skipping")
        return ProbeResult(
            provider="api_football",
            data_area="referee",
            status="skipped",
            api_key_present=False,
            notes="FOOTBALL_DATA_API_KEY not configured",
        )

    fields_found: list[str] = []
    fields_missing: list[str] = []
    notes_parts: list[str] = []
    raw_path: str | None = None

    # Step 1: Check referee field in fixture
    print(f"  [referee] Checking referee field in fixture {COMPLETED_FIXTURE_ID}...")
    referee_name: str | None = None
    try:
        fixture = client.get_fixture(COMPLETED_FIXTURE_ID)
        ref = fixture.get("fixture", {}).get("referee")
        if ref:
            fields_found.append("referee_assignment")
            referee_name = ref.split(",")[0].strip()  # strip country suffix if present
            notes_parts.append(f"referee field present: '{ref}'")
            print(f"  [referee] Found referee: {ref}")
        else:
            fields_missing.append("referee_assignment")
            notes_parts.append("referee field: null in this fixture")
            print("  [referee] No referee field in fixture")

    except Exception as exc:
        notes_parts.append(f"fixture fetch failed: {exc}")
        fields_missing.append("referee_assignment")

    # Step 2: Try historical fixtures by referee name
    if referee_name:
        print(f"  [referee] Searching historical fixtures for referee '{referee_name}'...")
        try:
            hist_fixtures = client.get_fixtures_by_referee(referee_name, season=2024)
            raw_path = str(client.save_sample(hist_fixtures[:3], "api_football_referee_history.json"))

            if hist_fixtures:
                fields_found.append("referee_historical_fixtures")
                count = len(hist_fixtures)
                notes_parts.append(f"historical fixtures for '{referee_name}': {count} found (season 2024)")
                print(f"  [referee] {count} historical fixture(s) found")

                # Assess whether per-match stats are needed
                # To get fouls/cards/penalties per referee, we'd need get_fixture_statistics() per fixture
                # That's 1 extra call per fixture × N fixtures × M referees = expensive
                notes_parts.append(
                    f"To derive referee tendency stats (fouls/cards/penalties per match), "
                    f"need 1 statistics call per fixture. "
                    f"For {count} fixtures × many referees → high API quota cost on free tier. "
                    f"Feasible only if referee set is small (<5) or paid plan."
                )

                # Try pulling stats for just one to verify feasibility
                if hist_fixtures:
                    sample_fid = hist_fixtures[0]["fixture"]["id"]
                    try:
                        sample_stats = client.get_fixture_statistics(sample_fid)
                        if sample_stats:
                            stat_types = {s["type"] for ts in sample_stats for s in ts.get("statistics", [])}
                            if "Fouls" in stat_types and "Yellow Cards" in stat_types:
                                fields_found.extend(["referee_fouls_per_match", "referee_cards_per_match"])
                                notes_parts.append("stats derivable per fixture (fouls, yellow cards confirmed)")
                            if "Red Cards" in stat_types:
                                fields_found.append("referee_red_cards_per_match")
                    except Exception as exc:
                        notes_parts.append(f"sample stats call failed: {exc}")
            else:
                fields_missing.append("referee_historical_fixtures")
                notes_parts.append(f"no historical fixtures found for referee '{referee_name}' in 2024")

        except Exception as exc:
            notes_parts.append(f"referee history search failed: {exc}")
            fields_missing.append("referee_historical_fixtures")
    else:
        fields_missing.extend(["referee_historical_fixtures", "referee_fouls_per_match", "referee_cards_per_match"])

    # MVP recommendation
    if "referee_assignment" in fields_found and "referee_historical_fixtures" in fields_found:
        mvp_rec = "INCLUDE (with caution): referee assignment available, history queryable, but stats derivation is quota-intensive. Viable on paid plan; manual for free tier."
    elif "referee_assignment" in fields_found:
        mvp_rec = "WEAK: assignment available but history lookup failed. Can note referee name only; no tendency stats."
    else:
        mvp_rec = "DROP from MVP: referee assignment not reliably available in tested fixture."

    notes_parts.append(f"MVP recommendation: {mvp_rec}")
    print(f"  [referee] {mvp_rec}")

    status = "ok" if "referee_assignment" in fields_found else "partial" if fields_found else "error"

    return ProbeResult(
        provider="api_football",
        data_area="referee",
        status=status,
        api_key_present=True,
        fields_found=fields_found,
        fields_missing=fields_missing,
        notes="; ".join(notes_parts),
        raw_sample_path=raw_path,
    )
