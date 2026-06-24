"""Pull gap markets for BIH vs QAT: cards, penalty, red card, corners."""
import re
import sys
sys.path.insert(0, ".")
from provider_probe.clients import the_odds_api as odds_client

def norm(s):
    return re.sub(r"[^a-z]", "", (s or "").lower())

# Bosnia matches on "bosni" + "herz"; Qatar on "qat"
def is_bih(s):
    n = norm(s)
    return "bosni" in n and "herz" in n

def is_qat(s):
    return "qat" in norm(s)

def find_match(data):
    for e in data:
        ht = e.get("home_team", "")
        at = e.get("away_team", "")
        if (is_bih(ht) and is_qat(at)) or (is_qat(ht) and is_bih(at)):
            return e
    return None

# First: show all events for h2h to confirm names
print("=== All events (h2h/us) ===")
data = odds_client.get_odds("soccer_fifa_world_cup", regions="us", markets="h2h")
for e in data:
    print(f"  {e.get('home_team')} vs {e.get('away_team')}")

match_ev = find_match(data)
if not match_ev:
    print("\nStill no match found — check names above")
    sys.exit(0)

print(f"\n=== MATCH: {match_ev.get('home_team')} vs {match_ev.get('away_team')} ===")

# Now pull additional markets
for mkt in ["h2h", "totals"]:
    try:
        data2 = odds_client.get_odds("soccer_fifa_world_cup", regions="us", markets=mkt)
        ev = find_match(data2)
        if ev:
            print(f"\n--- market={mkt} ---")
            for b in ev.get("bookmakers", []):
                print(f"  Book: {b['key']}")
                for mk in b.get("markets", []):
                    outcomes = ", ".join(
                        f"{o['name']}={o['price']}" + (f"@{o['point']}" if o.get("point") else "")
                        for o in mk.get("outcomes", [])
                    )
                    print(f"    {mk['key']}: {outcomes}")
    except Exception as exc:
        print(f"market={mkt} ERROR: {exc}")
