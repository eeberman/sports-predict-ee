"""
Probe API-Football for lineup data availability.
"""

from __future__ import annotations

from .. import config
from ..clients import api_football as client
from . import ProbeResult

# Known completed fixture (Tunisia vs Japan, 2022 WC group) — reuse from football_probe
COMPLETED_FIXTURE_ID = 855751


def _find_upcoming_fixture() -> int | None:
    """Return an upcoming fixture ID by searching recent fixtures and finding a future one."""
    try:
        from sportspredict_inventory import config as sp_config
        # Pick any team from the tournament
        teams = client.search_team("Tunisia")
        if teams:
            team_id = teams[0]["team"]["id"]
            for season in [2026, 2025]:
                fixtures = client.get_fixtures_by_team(team_id, season, last=10)
                upcoming = [
                    f for f in fixtures
                    if f.get("fixture", {}).get("status", {}).get("short") in ("NS", "TBD", "SUSP")
                ]
                if upcoming:
                    return upcoming[0]["fixture"]["id"]
    except Exception:
        pass
    return None


def run() -> ProbeResult:
    key_present = bool(config.FOOTBALL_DATA_API_KEY)
    if not key_present:
        print("  [lineups] FOOTBALL_DATA_API_KEY missing — skipping")
        return ProbeResult(
            provider="api_football",
            data_area="confirmed_lineups",
            status="skipped",
            api_key_present=False,
            notes="FOOTBALL_DATA_API_KEY not configured",
        )

    fields_found: list[str] = []
    fields_missing: list[str] = []
    notes_parts: list[str] = []
    raw_path: str | None = None

    # Test completed fixture (lineups should be available)
    print(f"  [lineups] Fetching lineups for completed fixture {COMPLETED_FIXTURE_ID}...")
    try:
        lineups = client.get_fixture_lineups(COMPLETED_FIXTURE_ID)
        raw_path = str(client.save_sample(lineups, "api_football_lineups_completed.json"))

        if lineups:
            team_lineup = lineups[0]
            start_xi = team_lineup.get("startXI", [])
            subs = team_lineup.get("substitutes", [])
            formation = team_lineup.get("formation")
            coach = team_lineup.get("coach", {})

            if start_xi:
                fields_found.append("starting_xi")
                print(f"  [lineups] startXI: {len(start_xi)} players")
            else:
                fields_missing.append("starting_xi")

            if subs:
                fields_found.append("substitutes")
            else:
                fields_missing.append("substitutes")

            if formation:
                fields_found.append("formation")
                notes_parts.append(f"formation: {formation}")
            else:
                fields_missing.append("formation")

            if coach.get("id"):
                fields_found.append("coach")

            # Check if any player has a position field
            if start_xi:
                p0 = start_xi[0].get("player", {})
                if p0.get("id"):
                    fields_found.append("player_id")
                if p0.get("pos"):
                    fields_found.append("player_position")

            # Check for confirmed flag
            confirmed_flag = team_lineup.get("confirmed") or team_lineup.get("is_confirmed")
            if confirmed_flag is not None:
                fields_found.append("confirmed_flag")
                notes_parts.append(f"confirmed flag present: {confirmed_flag}")
            else:
                notes_parts.append("no explicit 'confirmed' flag in lineup object")

            notes_parts.append(f"completed fixture {COMPLETED_FIXTURE_ID}: {len(lineups)} teams, startXI present={bool(start_xi)}")
        else:
            fields_missing.extend(["starting_xi", "substitutes", "formation", "player_id"])
            notes_parts.append(f"completed fixture {COMPLETED_FIXTURE_ID}: empty lineups response")

    except Exception as exc:
        notes_parts.append(f"completed fixture lineup fetch failed: {exc}")
        fields_missing.extend(["starting_xi", "substitutes", "formation"])

    # Test upcoming fixture (lineups may not be published yet)
    print("  [lineups] Searching for upcoming fixture to test pre-match lineup availability...")
    upcoming_id = _find_upcoming_fixture()
    if upcoming_id:
        print(f"  [lineups] Found upcoming fixture {upcoming_id}, checking lineups...")
        try:
            upcoming_lineups = client.get_fixture_lineups(upcoming_id)
            client.save_sample(upcoming_lineups, "api_football_lineups_upcoming.json")
            if upcoming_lineups:
                start_xi = upcoming_lineups[0].get("startXI", [])
                notes_parts.append(
                    f"upcoming fixture {upcoming_id}: lineup data available ({len(start_xi)} startXI entries) — possibly predicted"
                )
            else:
                notes_parts.append(f"upcoming fixture {upcoming_id}: empty lineups (not yet announced)")
        except Exception as exc:
            notes_parts.append(f"upcoming fixture lineup check failed: {exc}")
    else:
        notes_parts.append("no upcoming fixture found to test pre-match lineup timing")

    status = "ok" if "starting_xi" in fields_found else ("partial" if fields_found else "error")
    notes_parts.append(
        "Note: API-Football does not explicitly mark confirmed vs predicted lineups; "
        "treat any pre-match lineup data as predicted until ~1h before kickoff"
    )

    return ProbeResult(
        provider="api_football",
        data_area="confirmed_lineups",
        status=status,
        api_key_present=True,
        fields_found=fields_found,
        fields_missing=fields_missing,
        notes="; ".join(notes_parts),
        raw_sample_path=raw_path,
    )
