"""
Land raw API-Football national-team match data to R2 for the extended team-rate pool.

For each missing WC2026 team (today's slate first), fetch:
  - recent fixtures (last N, all competitions)   -> 1 call/team
  - per fixture: /fixtures/statistics             -> N calls/team
  - per fixture: /fixtures/events (for 2H cards)  -> N calls/team
plus 1 team-search call. ~ (2 + 2N) calls/team.

Free tier is 100 calls/day. A budget guard checks /status (which does NOT count
against quota) before each team and stops cleanly at a team boundary, deferring the
rest to tomorrow. Raw JSON is uploaded immutably to R2 and tracked in raw_manifest.csv;
nothing derived is written locally.

Run:  python -m raw_landing.sources.api_football_natl [--last N] [--dry-run] [--teams A,B]
"""
from __future__ import annotations

import json
import sys
import time
from datetime import date
from uuid import uuid4

from .. import config, manifest, r2
from provider_probe.clients import api_football as af

SOURCE = "api_football"
ENTITY = "national_match"
DEFAULT_LAST = 8          # fixtures per team (keeps 5-team run under the 100/day cap)
DEFAULT_SEASON = 2024     # most recent season the Free plan allows (spans into late 2025)
SAFETY_MARGIN = 4         # leave this many calls unspent
THROTTLE = 6              # extra seconds/call: Free plan caps at 10 req/min (client adds ~1s)


def _throttle() -> None:
    time.sleep(THROTTLE)


def _slug(canon: str) -> str:
    return canon.lower().replace(" ", "_").replace("ü", "u").replace("ç", "c").replace("'", "")


def _key(canon: str, leaf: str, season: int) -> str:
    """Stable key (no run_id / date) so per-fixture data dedups across runs and days —
    avoids re-spending API budget on a multi-day backfill. Fixture ids are unique."""
    return f"raw/{SOURCE}/national/season={season}/team={_slug(canon)}/{leaf}"


def _upload(key: str, obj, run_id: str, src_url: str, note: str, rows: list, dry_run: bool) -> None:
    if dry_run:
        rows.append(manifest.ManifestRow(run_id=run_id, source_name=SOURCE, entity_name=ENTITY,
                                         source_url=src_url, r2_key=key, r2_uri=r2.r2_uri(key),
                                         status="dry_run", notes=note))
        return
    if manifest.already_uploaded(key):
        rows.append(manifest.ManifestRow(run_id=run_id, source_name=SOURCE, entity_name=ENTITY,
                                         source_url=src_url, r2_key=key, r2_uri=r2.r2_uri(key),
                                         status="skipped", notes=note))
        return
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    n = r2.upload_bytes(key, data, "application/json")
    row = manifest.ManifestRow(run_id=run_id, source_name=SOURCE, entity_name=ENTITY,
                               source_url=src_url, r2_key=key, r2_uri=r2.r2_uri(key),
                               bytes_uploaded=n, notes=note)
    manifest.append_row(row)
    rows.append(row)


def _pick_national(results: list[dict], canon_name: str) -> dict | None:
    from forecasting.team_canon import canon
    want = canon(canon_name).lower()
    nat = [r for r in results if r.get("team", {}).get("national")]
    for r in nat:
        if canon(r["team"].get("name", "")).lower() == want:
            return r["team"]
    return nat[0]["team"] if nat else (results[0]["team"] if results else None)


def fetch_team(team_name: str, last: int, season: int, run_id: str, rows: list, dry_run: bool) -> str:
    """Fetch + land one team. Returns a status string."""
    base = "https://v3.football.api-sports.io"
    res = af.search_team(team_name)
    _throttle()
    team = _pick_national(res, team_name)
    if not team:
        return f"{team_name}: NOT FOUND"
    tid = team["id"]
    fixtures = af.recent_finished(tid, season, last)
    _throttle()
    _upload(_key(team_name, "fixtures.json", season), {"team": team, "response": fixtures},
            run_id, f"{base}/fixtures?team={tid}&season={season}", f"team_id={tid}, {len(fixtures)} fixtures",
            rows, dry_run)
    for fx in fixtures:
        fid = fx.get("fixture", {}).get("id")
        if fid is None:
            continue
        stk = _key(team_name, f"fixture={fid}_statistics.json", season)
        evk = _key(team_name, f"fixture={fid}_events.json", season)
        if not (manifest.already_uploaded(stk) and manifest.already_uploaded(evk)):
            stats = af.get_fixture_statistics(fid)
            _throttle()
            _upload(stk, {"fixture": fx, "response": stats}, run_id,
                    f"{base}/fixtures/statistics?fixture={fid}", f"fid={fid}", rows, dry_run)
            events = af.get_fixture_events(fid)
            _throttle()
            _upload(evk, {"response": events}, run_id,
                    f"{base}/fixtures/events?fixture={fid}", f"fid={fid}", rows, dry_run)
    return f"{team_name}: {len(fixtures)} fixtures landed"


def run(run_id: str | None = None, last: int = DEFAULT_LAST, season: int = DEFAULT_SEASON,
        dry_run: bool = False, teams: list[str] | None = None) -> list[manifest.ManifestRow]:
    config.load_env_file(config.PROJECT_ROOT.parent / ".env")  # R2 creds live at repo root
    from forecasting.team_canon import priority_teams
    run_id = run_id or uuid4().hex[:8]
    fetch_list = teams or priority_teams()
    rows: list[manifest.ManifestRow] = []
    per_team_cost = 2 + 2 * last

    print(f"  [af_natl] run_id={run_id} last={last} season={season} dry_run={dry_run}")
    print(f"  [af_natl] fetch order: {fetch_list}")

    completed, deferred = [], []
    for tname in fetch_list:
        if not dry_run:
            try:
                used, limit = af.requests_remaining()
            except Exception as exc:
                print(f"  [af_natl] budget check failed ({str(exc)[:60]}); proceeding cautiously")
                used, limit = 0, 0
            if limit and (limit - used) < (per_team_cost + SAFETY_MARGIN):
                print(f"  [af_natl] daily budget low ({used}/{limit}); deferring rest")
                deferred.extend([t for t in fetch_list[fetch_list.index(tname):]])
                break
        print(f"  [af_natl] {'DRY ' if dry_run else ''}fetching {tname} (~{per_team_cost} calls)")
        try:
            print("    " + fetch_team(tname, last, season, run_id, rows, dry_run))
            completed.append(tname)
        except Exception as exc:
            print(f"    FAILED {tname}: {str(exc)[:140]}")
            deferred.append(tname)

    if not dry_run:
        used, limit = af.requests_remaining()
        print(f"  [af_natl] budget: {used}/{limit} used")
    print(f"  [af_natl] completed: {completed}")
    if deferred:
        print(f"  [af_natl] DEFERRED (budget/error): {deferred}")
    return rows


if __name__ == "__main__":
    args = sys.argv[1:]
    dry = "--dry-run" in args
    last_n = DEFAULT_LAST
    season_n = DEFAULT_SEASON
    teams_arg = None
    for i, a in enumerate(args):
        if a == "--last" and i + 1 < len(args):
            last_n = int(args[i + 1])
        if a == "--season" and i + 1 < len(args):
            season_n = int(args[i + 1])
        if a == "--teams" and i + 1 < len(args):
            teams_arg = [t.strip() for t in args[i + 1].split(",")]
    run(last=last_n, season=season_n, dry_run=dry, teams=teams_arg)
