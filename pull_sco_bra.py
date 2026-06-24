"""One-shot pull of all standard markets for SCO vs BRA."""
import sys, json, re, time
sys.path.insert(0, ".")
from provider_probe.clients import the_odds_api as oc

def norm(s):
    return re.sub(r"[^a-z]", "", (s or "").lower())

sk = oc.find_active_sport_key()
print("Sport key:", sk)

# 1. Featured markets
time.sleep(1)
events = oc._get(f"/sports/{sk}/odds/", {"regions": "eu", "markets": "h2h,totals,spreads"})
want = {norm("Scotland"), norm("Brazil")}
ev = next((e for e in events if {norm(e.get("home_team", "")), norm(e.get("away_team", ""))} == want), None)
if not ev:
    print("Event NOT found. Available:")
    for e in events[:8]:
        print(" ", e.get("home_team"), "vs", e.get("away_team"))
    sys.exit(1)

print(f"Found: {ev.get('home_team')} vs {ev.get('away_team')}  id: {ev['id']}")
event_id = ev["id"]

for b in ev.get("bookmakers", [])[:3]:
    print(f"  Bookmaker: {b['key']}")
    for mk in b.get("markets", []):
        outs = ", ".join(
            f"{o['name']}={o['price']}" + (f"@{o['point']}" if o.get("point") else "")
            for o in mk.get("outcomes", [])
        )
        print(f"    {mk['key']}: {outs}")

# 2. Per-event richer markets
richer_markets = [
    "btts", "totals_h2", "h2h_h2", "team_totals",
    "alternate_totals", "alternate_team_totals", "player_shots_on_target",
]
print("\n--- Per-event markets ---")
for mkt in richer_markets:
    try:
        time.sleep(0.7)
        data = oc._get(f"/sports/{sk}/events/{event_id}/odds/", {"regions": "eu", "markets": mkt})
        bms = data.get("bookmakers", []) if isinstance(data, dict) else []
        if bms:
            print(f"\n[{mkt}]")
            for b in bms[:3]:
                print(f"  BM: {b['key']}")
                for mk in b.get("markets", []):
                    outs = ", ".join(
                        f"{o['name']}={o['price']}" + (f"@{o['point']}" if o.get("point") else "")
                        for o in mk.get("outcomes", [])
                    )
                    print(f"    {mk['key']}: {outs}")
        else:
            print(f"[{mkt}] — no bookmakers")
    except Exception as exc:
        print(f"[{mkt}] error: {exc}")
