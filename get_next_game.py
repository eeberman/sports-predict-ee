"""Fetch next game and its markets from SportsPredict, then pull odds anchors."""
import json
import sys
from datetime import datetime, timezone

sys.path.insert(0, ".")
from provider_probe.clients.sportspredict import _tool
from provider_probe.clients import the_odds_api as odds_client
from sportspredict_inventory.normalize import normalize_market
from sportspredict_inventory import config as spc
import re

def norm_name(s):
    return re.sub(r"[^a-z]", "", (s or "").lower())

events = json.loads(_tool("list_events", {}))
pc = [e for e in events if "probability cup" in (e.get("title") or e.get("name") or "").lower()]
ev = pc[0] if pc else events[0]
print("Event:", ev.get("name") or ev.get("title"), " id:", ev["id"])

lobbies = json.loads(_tool("list_lobbies", {"event_id": ev["id"]}))
lid = lobbies[0]["id"]
print("Lobby id:", lid)

try:
    _tool("join_lobby", {"lobby_id": lid})
except Exception:
    pass

matches = json.loads(_tool("list_matches", {"event_id": ev["id"], "lobby_id": lid}))
now = datetime.now(timezone.utc)
upcoming = []
for m in matches:
    ot = m.get("opening_time", "")
    try:
        dt = datetime.fromisoformat(ot.replace("Z", "+00:00"))
    except Exception:
        continue
    if dt > now:
        upcoming.append((dt, m))
upcoming.sort(key=lambda x: x[0])
print(f"Upcoming: {len(upcoming)} matches")
for dt, m in upcoming[:8]:
    print(f"  {dt.isoformat()}  {m['name']}  mkts={m.get('open_market_count','?')}")

if not upcoming:
    print("No upcoming matches found")
    sys.exit(0)

# Take the next game
kick_dt, next_match = upcoming[0]
mid = next_match["id"]
name = next_match["name"]
print(f"\n=== NEXT GAME: {name} (kicks off {kick_dt.isoformat()}) ===\n")

# Split teams
home_raw, away_raw = (name.split(" vs ", 1) + [""])[:2]
fifa_map = spc.FIFA_CODE_TO_NAME
home = fifa_map.get(home_raw.strip(), home_raw.strip())
away = fifa_map.get(away_raw.strip(), away_raw.strip())
print(f"Home: {home}   Away: {away}")

# Pull markets
markets_text = _tool("list_markets", {"lobby_id": lid, "match_id": mid})
markets = json.loads(markets_text)
print(f"\n{len(markets)} markets:\n")
for i, mk in enumerate(markets, 1):
    q = mk.get("question") or mk.get("title") or ""
    n = normalize_market({"question": q}, {"home_team": home, "away_team": away})
    fam = n.get("question_family", "?")
    sub = n.get("question_subtype", "?")
    tgt = n.get("target_team_or_side", "")
    thresh = n.get("threshold_value", "")
    scope = n.get("time_scope", "")
    meta = " | ".join(x for x in [fam, sub, tgt, f"thr={thresh}" if thresh else "", scope] if x)
    print(f"  {i:2}. [{mk['id']}] {q}")
    print(f"       -> {meta}")

# Pull odds
print("\n=== ODDS ANCHORS ===\n")
WC_SPORT = "soccer_fifa_world_cup"
try:
    ev_odds = odds_client.get_odds(WC_SPORT, regions="us", markets="h2h,totals,btts")
    want = {norm_name(home), norm_name(away)}
    match_ev = next((e for e in ev_odds if {norm_name(e.get("home_team","")), norm_name(e.get("away_team",""))} == want), None)
    if match_ev:
        print(f"Odds event found: {match_ev.get('home_team')} vs {match_ev.get('away_team')}")
        for b in match_ev.get("bookmakers", [])[:3]:
            print(f"  Bookmaker: {b['key']}")
            for mk in b.get("markets", []):
                outcomes_str = ", ".join(f"{o['name']}={o['price']}" + (f"@{o['point']}" if o.get('point') else "") for o in mk.get("outcomes", []))
                print(f"    {mk['key']}: {outcomes_str}")
    else:
        print(f"No odds found for {home} vs {away} in {WC_SPORT}")
        print(f"Available events ({len(ev_odds)}):")
        for e in ev_odds[:5]:
            print(f"  {e.get('home_team')} vs {e.get('away_team')}")
except Exception as exc:
    print(f"Odds fetch failed: {exc}")
