"""
Next-kickoff-first worksheet runner.

  python -m forecasting.cli            # list today's un-started matches
  python -m forecasting.cli --next     # worksheet for the next match
  python -m forecasting.cli --n 3      # worksheets for the next 3 matches
  python -m forecasting.cli --all-today

NO auto-submit. Generates review worksheets only.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from provider_probe.clients.sportspredict import _tool
from forecasting import worksheet as ws


def get_slate(today_only: bool = True) -> tuple[str, list[dict]]:
    events = json.loads(_tool("list_events", {}))
    pc = [e for e in events if "probability cup" in (e.get("title") or e.get("name") or "").lower()]
    ev = pc[0] if pc else events[0]
    eid = ev["id"]
    lobbies = json.loads(_tool("list_lobbies", {"event_id": eid}))
    lid = lobbies[0]["id"]
    try:
        _tool("join_lobby", {"lobby_id": lid})
    except Exception:
        pass
    matches = json.loads(_tool("list_matches", {"event_id": eid, "lobby_id": lid}))
    now = datetime.now(timezone.utc)
    out = []
    for m in matches:
        ot = m.get("opening_time", "")
        try:
            dt = datetime.fromisoformat(ot.replace("Z", "+00:00"))
        except Exception:
            continue
        if dt <= now:
            continue
        if today_only and dt.date() != now.date():
            # keep matches whose kickoff is within the current UTC day OR next ~12h
            if (dt - now).total_seconds() > 12 * 3600:
                continue
        out.append({**m, "_kick": dt})
    out.sort(key=lambda x: x["_kick"])
    return lid, out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--next", action="store_true")
    ap.add_argument("--n", type=int, default=0)
    ap.add_argument("--all-today", action="store_true")
    args = ap.parse_args()

    lid, slate = get_slate(today_only=not args.all_today)
    print(f"Un-started matches (next-kickoff-first): {len(slate)}")
    for m in slate:
        print(f"  {m['_kick'].isoformat()}  {m['name']}  ({m.get('open_market_count','?')} mkts)")

    n = 1 if args.next else (args.n if args.n else (len(slate) if args.all_today else 0))
    if not n:
        print("\n(no worksheets requested — use --next / --n K / --all-today)")
        return
    for m in slate[:n]:
        wsd = ws.build_worksheet(lid, m)
        md, cp = ws.write(wsd)
        print(f"\n=== {m['name']} ===")
        print(ws.render_md(wsd))
        print(f"written: {md}")


if __name__ == "__main__":
    main()
