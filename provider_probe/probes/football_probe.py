"""
Probe API-Football for match stats coverage.
"""

from __future__ import annotations

from .. import config
from ..clients import api_football as client
from ..clients import sportspredict as sp_client
from . import ProbeResult

# These type names appear in API-Football's statistics response
STAT_TYPES_NEEDED = [
    "Shots on Goal",
    "Shots off Goal",
    "Total Shots",
    "Fouls",
    "Yellow Cards",
    "Red Cards",
    "Corner Kicks",
    "Offsides",
    "Ball Possession",
    "Goalkeeper Saves",
]

# Map API-Football stat names → our field names
STAT_FIELD_MAP = {
    "Shots on Goal": "shots_on_target",
    "Shots off Goal": "shots_off_target",
    "Total Shots": "total_shots",
    "Fouls": "fouls",
    "Yellow Cards": "yellow_cards",
    "Red Cards": "red_cards",
    "Corner Kicks": "corners",
    "Offsides": "offsides",
    "Ball Possession": "possession",
    "Goalkeeper Saves": "goalkeeper_saves",
}

# Known completed international fixture for fallback (Tunisia vs Japan, 2022 WC group)
FALLBACK_FIXTURE_ID = 855751


def _find_fixture() -> tuple[int | None, str]:
    """Try to map a SportsPredict match → API-Football fixture. Returns (id, note)."""
    sp_match = sp_client.get_sample_match()
    if sp_match:
        match_name = sp_match.get("name", "")
        print(f"  [football] SportsPredict sample match: {match_name}")

        if " vs " in match_name:
            from sportspredict_inventory import config as sp_config
            home_code, away_code = match_name.split(" vs ", 1)
            home_name = sp_config.FIFA_CODE_TO_NAME.get(home_code.strip(), home_code.strip())
            away_name = sp_config.FIFA_CODE_TO_NAME.get(away_code.strip(), away_code.strip())
            print(f"  [football] Resolved: {home_name} vs {away_name}")

            teams_home = client.search_team(home_name)
            if teams_home:
                team_id = teams_home[0]["team"]["id"]
                # Look for recent completed fixtures for this team
                for season in [2026, 2025, 2024]:
                    fixtures = client.get_fixtures_by_team(team_id, season, last=10)
                    completed = [
                        f for f in fixtures
                        if f.get("fixture", {}).get("status", {}).get("short") in ("FT", "AET", "PEN")
                    ]
                    if completed:
                        fid = completed[0]["fixture"]["id"]
                        note = f"Mapped {match_name} → fixture {fid} via {home_name} (season {season})"
                        return fid, note

    print(f"  [football] Falling back to known fixture {FALLBACK_FIXTURE_ID}")
    return FALLBACK_FIXTURE_ID, f"Used fallback fixture {FALLBACK_FIXTURE_ID} (TUN vs JPN, 2022 WC)"


def run() -> ProbeResult:
    key_present = bool(config.FOOTBALL_DATA_API_KEY)
    if not key_present:
        print("  [football] FOOTBALL_DATA_API_KEY missing — skipping")
        return ProbeResult(
            provider="api_football",
            data_area="match_stats",
            status="skipped",
            api_key_present=False,
            notes="FOOTBALL_DATA_API_KEY not configured",
        )

    # Status check
    print("  [football] Checking API status...")
    try:
        status_data = client.get_status()
        sample_path = client.save_sample(status_data, "api_football_status.json")
        print(f"  [football] Status: {client.ping()['message']}")
    except Exception as exc:
        return ProbeResult(
            provider="api_football",
            data_area="match_stats",
            status="error",
            api_key_present=True,
            notes=f"Status check failed: {exc}",
        )

    # Find a fixture
    fixture_id, mapping_note = _find_fixture()
    print(f"  [football] {mapping_note}")

    fields_found: list[str] = []
    fields_missing: list[str] = []
    notes_parts: list[str] = [mapping_note]
    raw_path: str | None = None

    # Fetch fixture root (score, halftime score, referee)
    print(f"  [football] Fetching fixture {fixture_id}...")
    try:
        fixture = client.get_fixture(fixture_id)
        client.save_sample(fixture, "api_football_fixture.json")

        f = fixture.get("fixture", {})
        score = fixture.get("score", {})
        goals = fixture.get("goals", {})

        if goals.get("home") is not None:
            fields_found.append("final_score")
        else:
            fields_missing.append("final_score")

        ht = score.get("halftime", {})
        if ht.get("home") is not None:
            fields_found.append("halftime_score")
        else:
            fields_missing.append("halftime_score")

        referee = f.get("referee")
        if referee:
            fields_found.append("referee_name")
            notes_parts.append(f"referee={referee}")
        else:
            fields_missing.append("referee_name")

        status_short = f.get("status", {}).get("short", "")
        notes_parts.append(f"fixture_status={status_short}")

    except Exception as exc:
        notes_parts.append(f"fixture fetch failed: {exc}")
        fields_missing.extend(["final_score", "halftime_score", "referee_name"])

    # Fetch statistics
    print(f"  [football] Fetching statistics for fixture {fixture_id}...")
    try:
        stats = client.get_fixture_statistics(fixture_id)
        raw_path = str(client.save_sample(stats, "api_football_statistics.json"))

        found_stat_types: set[str] = set()
        has_ht_breakdown = False
        for team_stats in stats:
            for stat in team_stats.get("statistics", []):
                stype = stat.get("type", "")
                found_stat_types.add(stype)
                if stat.get("period"):
                    has_ht_breakdown = True

        print(f"  [football] Stat types found: {sorted(found_stat_types)}")

        for stat_name, field_name in STAT_FIELD_MAP.items():
            if stat_name in found_stat_types:
                fields_found.append(field_name)
            else:
                fields_missing.append(field_name)

        if has_ht_breakdown:
            fields_found.append("halftime_stats_breakdown")
            notes_parts.append("half-time period breakdown: yes")
        else:
            # Check if halftime score from fixture root was found
            if "halftime_score" in fields_found:
                fields_found.append("halftime_score_available")
                notes_parts.append("halftime score from fixture root: yes; per-stat HT breakdown: no")
            else:
                fields_missing.append("halftime_stats_breakdown")
                notes_parts.append("half-time breakdown: not detected")

    except Exception as exc:
        notes_parts.append(f"statistics fetch failed: {exc}")
        fields_missing.extend(list(STAT_FIELD_MAP.values()))

    # Also fetch player stats briefly
    print(f"  [football] Fetching player stats for fixture {fixture_id}...")
    try:
        players = client.get_fixture_players(fixture_id)
        client.save_sample(players[:1] if players else players, "api_football_players.json")
        if players:
            p = players[0].get("players", [{}])[0].get("statistics", [{}])[0] if players[0].get("players") else {}
            player_fields = list(p.keys()) if p else []
            if "shots" in str(player_fields).lower() or any("shot" in k for k in player_fields):
                fields_found.append("player_shots")
            if "goals" in str(player_fields).lower():
                fields_found.append("player_goals")
            notes_parts.append(f"player stat keys sample: {player_fields[:8]}")
        else:
            notes_parts.append("player stats: empty response")
            fields_missing.extend(["player_shots", "player_goals"])
    except Exception as exc:
        notes_parts.append(f"player stats fetch failed: {exc}")

    status = "ok" if not fields_missing else ("partial" if fields_found else "error")

    return ProbeResult(
        provider="api_football",
        data_area="match_stats",
        status=status,
        api_key_present=True,
        fields_found=fields_found,
        fields_missing=fields_missing,
        notes="; ".join(notes_parts),
        raw_sample_path=raw_path,
    )
