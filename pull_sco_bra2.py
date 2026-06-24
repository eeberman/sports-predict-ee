"""Pull corners, cards markets + inspect player SoT raw for SCO vs BRA."""
import sys, json, re, time
sys.path.insert(0, ".")
from provider_probe.clients import the_odds_api as oc

def norm(s):
    return re.sub(r"[^a-z]", "", (s or "").lower())

sk = oc.find_active_sport_key()
event_id = "885ba95805db310a7bcc3fb1a7a6dd28"

extra_markets = [
    "player_pass_attempts",
    "player_cards",
    "alternate_spreads",
]

print("=== Player SoT RAW (onexbet, first 3 outcomes) ===")
try:
    time.sleep(0.7)
    data = oc._get(f"/sports/{sk}/events/{event_id}/odds/", {"regions": "eu", "markets": "player_shots_on_target"})
    bms = data.get("bookmakers", []) if isinstance(data, dict) else []
    for b in bms[:2]:
        print(f"BM: {b['key']}")
        for mk in b.get("markets", []):
            print(f"  Market: {mk['key']}")
            for o in mk.get("outcomes", [])[:20]:
                print(f"    {json.dumps(o)}")
except Exception as exc:
    print(f"Error: {exc}")

print("\n=== Team totals FULL (corners) ===")
# Try corners via alternate spreads or specific market name
corner_markets = ["team_totals_h2", "h2h_3_way", "spreads"]
for mkt in ["team_totals_h2", "h2h_lay", "spreads_h2"]:
    try:
        time.sleep(0.7)
        data = oc._get(f"/sports/{sk}/events/{event_id}/odds/", {"regions": "eu", "markets": mkt})
        bms = data.get("bookmakers", []) if isinstance(data, dict) else []
        if bms:
            print(f"\n[{mkt}]")
            for b in bms[:2]:
                print(f"  BM: {b['key']}")
                for mk in b.get("markets", []):
                    outs = ", ".join(
                        f"{o.get('name','?')}={o['price']}" + (f"@{o['point']}" if o.get("point") else "")
                        for o in mk.get("outcomes", [])
                    )
                    print(f"    {mk['key']}: {outs}")
        else:
            print(f"[{mkt}] — no bookmakers")
    except Exception as exc:
        print(f"[{mkt}] error: {exc}")

# Try to get full events listing with all markets
print("\n=== Available markets for this event ===")
try:
    time.sleep(1)
    # Get featured odds with all available markets
    data = oc._get(f"/sports/{sk}/events/{event_id}/odds/", {"regions": "eu", "markets": "h2h,totals,btts,spreads"})
    bms = data.get("bookmakers", []) if isinstance(data, dict) else []
    for b in bms[:1]:
        print(f"BM: {b['key']}")
        for mk in b.get("markets", []):
            outs = ", ".join(
                f"{o.get('name','?')}={o['price']}" + (f"@{o['point']}" if o.get("point") else "")
                for o in mk.get("outcomes", [])
            )
            print(f"  {mk['key']}: {outs}")
except Exception as exc:
    print(f"Error: {exc}")
