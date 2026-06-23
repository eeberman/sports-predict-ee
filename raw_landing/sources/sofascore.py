"""
Land raw Sofascore national-team statistics to R2 — EXPERIMENTAL, flagged untested.

Sofascore is the only free source with true 1H/2H stat groups, but it is Cloudflare-
protected and returns 403 from server environments. This lander attempts the fetch and
**soft-fails**: on a block it records a status note and exits cleanly (no crash, no
partial corruption). Anything it does land is keyed under `raw/sofascore_untested/...`
and carries the `sofascore_untested` provenance downstream.

Run:  python -m raw_landing.sources.sofascore [--teams A,B] [--last N]
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from uuid import uuid4

from .. import config, manifest, r2
from provider_probe.clients import sofascore as ss

SOURCE = "sofascore_untested"
ENTITY = "national_match"


def _key(canon: str, leaf: str) -> str:
    slug = canon.lower().replace(" ", "_").replace("ü", "u").replace("ç", "c").replace("'", "")
    return f"raw/{SOURCE}/national/team={slug}/{leaf}"


def _status_note(detail: str) -> None:
    """Record the experiment outcome to R2 so the untested status is auditable."""
    key = f"raw/{SOURCE}/_status/probe_{date.today().isoformat()}.json"
    payload = json.dumps({
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "reachable": False, "detail": detail,
        "note": "Sofascore blocked from this environment; source remains UNTESTED.",
    }, ensure_ascii=False).encode("utf-8")
    try:
        r2.upload_bytes(key, payload, "application/json")
        print(f"  [sofascore] status note -> {r2.r2_uri(key)}")
    except r2.R2Error:
        pass  # key may already exist for today; fine


def run(last: int = 8, dry_run: bool = False, teams: list[str] | None = None) -> list[manifest.ManifestRow]:
    config.load_env_file(config.PROJECT_ROOT.parent / ".env")
    from forecasting.team_canon import priority_teams, canon
    run_id = uuid4().hex[:8]
    fetch_list = teams or priority_teams()
    rows: list[manifest.ManifestRow] = []

    ok, detail = ss.reachable()
    print(f"  [sofascore] reachable={ok} ({detail})")
    if not ok:
        print("  [sofascore] UNTESTED — blocked from this environment; recording status, skipping fetch.")
        _status_note(detail)
        return rows

    for tname in fetch_list:
        try:
            ents = ss.search_team(tname)
            nat = next((e for e in ents if e.get("national")), ents[0] if ents else None)
            if not nat:
                print(f"    {tname}: not found"); continue
            tid = nat["id"]
            events = ss.team_recent_events(tid)[-last:]
            ekey = _key(tname, "events.json")
            data = json.dumps({"team": nat, "events": events}, ensure_ascii=False).encode("utf-8")
            if not dry_run and not manifest.already_uploaded(ekey):
                n = r2.upload_bytes(ekey, data, "application/json")
                manifest.append_row(manifest.ManifestRow(
                    run_id=run_id, source_name=SOURCE, entity_name=ENTITY,
                    source_url=f"{ss.BASE}/team/{tid}/events/last/0", r2_key=ekey,
                    r2_uri=r2.r2_uri(ekey), bytes_uploaded=n, notes=f"{len(events)} events"))
            for ev in events:
                eid = ev.get("id")
                skey = _key(tname, f"event={eid}_statistics.json")
                if dry_run or manifest.already_uploaded(skey):
                    continue
                st = ss.event_statistics(eid)
                sd = json.dumps({"event": ev, "statistics": st}, ensure_ascii=False).encode("utf-8")
                n = r2.upload_bytes(skey, sd, "application/json")
                manifest.append_row(manifest.ManifestRow(
                    run_id=run_id, source_name=SOURCE, entity_name=ENTITY,
                    source_url=f"{ss.BASE}/event/{eid}/statistics", r2_key=skey,
                    r2_uri=r2.r2_uri(skey), bytes_uploaded=n, notes=f"event={eid}"))
            print(f"    {tname}: {len(events)} matches landed")
        except ss.SofascoreBlocked as exc:
            print(f"    {tname}: BLOCKED mid-run ({exc}); stopping.")
            _status_note(str(exc))
            break
        except Exception as exc:  # noqa: BLE001
            print(f"    {tname}: FAILED {str(exc)[:100]}")
    return rows


if __name__ == "__main__":
    args = sys.argv[1:]
    teams_arg = None
    last_n = 8
    for i, a in enumerate(args):
        if a == "--teams" and i + 1 < len(args):
            teams_arg = [t.strip() for t in args[i + 1].split(",")]
        if a == "--last" and i + 1 < len(args):
            last_n = int(args[i + 1])
    run(last=last_n, dry_run="--dry-run" in args, teams=teams_arg)
