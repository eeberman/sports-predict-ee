"""Try event-level endpoint for more market types (cards, corners, penalty)."""
import re
import sys
sys.path.insert(0, ".")
from provider_probe.clients import the_odds_api as odds_client

def is_bih(s):
    n = re.sub(r"[^a-z]", "", (s or "").lower())
    return "bosni" in n and "herz" in n

def is_qat(s):
    return "qat" in re.sub(r"[^a-z]", "", (s or "").lower())

# Get event ID first
events = odds_client._get("/sports/soccer_fifa_world_cup/events/", {"regions": "us"})
bih_qat = None
for e in events:
    ht = e.get("home_team", "")
    at = e.get("away_team", "")
    if (is_bih(ht) and is_qat(at)) or (is_qat(ht) and is_bih(at)):
        bih_qat = e
        break

if not bih_qat:
    print("No BIH/QAT event found")
    for e in events[:5]:
        print(f"  {e.get('home_team')} vs {e.get('away_team')} id={e.get('id')}")
    sys.exit(1)

event_id = bih_qat["id"]
print(f"Event ID: {event_id} — {bih_qat.get('home_team')} vs {bih_qat.get('away_team')}")

# Try specific market types
extra_markets = [
    "btts",
    "alternate_totals",
    "player_props",
    "cards",
    "corners",
    "h2h_h1,h2h_h2",
    "h2h_h2",
    "alternate_spreads",
    "outrights",
]

for mkt in extra_markets:
    try:
        resp = odds_client._get(
            f"/sports/soccer_fifa_world_cup/events/{event_id}/odds/",
            {"regions": "us", "markets": mkt}
        )
        books = resp.get("bookmakers", [])
        if books:
            print(f"\n--- market={mkt} ({len(books)} books) ---")
            for b in books[:3]:
                print(f"  Book: {b['key']}")
                for mk in b.get("markets", []):
                    outcomes = ", ".join(
                        f"{o['name']}={o['price']}" + (f"@{o['point']}" if o.get("point") else "")
                        for o in mk.get("outcomes", [])
                    )
                    print(f"    {mk['key']}: {outcomes}")
        else:
            print(f"market={mkt}: no bookmakers")
    except Exception as exc:
        print(f"market={mkt} ERROR: {exc}")
