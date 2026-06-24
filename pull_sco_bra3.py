"""Pull team_totals raw + corners + cards + HT markets for SCO vs BRA."""
import sys, json, re, time
sys.path.insert(0, ".")
from provider_probe.clients import the_odds_api as oc

sk = oc.find_active_sport_key()
event_id = "885ba95805db310a7bcc3fb1a7a6dd28"

targets = {
    "team_totals": "team_totals",
    "corners": "player_pass_attempts",  # not a thing; see below
    "h2": "h2h_h2",
}

# Team totals RAW
print("=== team_totals RAW ===")
try:
    time.sleep(0.7)
    data = oc._get(f"/sports/{sk}/events/{event_id}/odds/", {"regions": "eu", "markets": "team_totals"})
    bms = data.get("bookmakers", []) if isinstance(data, dict) else []
    for b in bms[:2]:
        print(f"BM: {b['key']}")
        for mk in b.get("markets", []):
            print(f"  Market: {mk['key']}")
            for o in mk.get("outcomes", []):
                print(f"    {json.dumps(o)}")
except Exception as exc:
    print(f"Error: {exc}")

# HT result (to infer 1H Brazil score)
print("\n=== h2h_1h / h2h_lay / spreads RAW ===")
for mkt in ["h2h_1h", "spreads", "alternate_spreads"]:
    try:
        time.sleep(0.7)
        data = oc._get(f"/sports/{sk}/events/{event_id}/odds/", {"regions": "eu", "markets": mkt})
        bms = data.get("bookmakers", []) if isinstance(data, dict) else []
        if bms:
            print(f"\n[{mkt}]")
            for b in bms[:2]:
                print(f"  BM: {b['key']}")
                for mk in b.get("markets", []):
                    for o in mk.get("outcomes", [])[:6]:
                        print(f"    {json.dumps(o)}")
        else:
            print(f"[{mkt}] — no data")
    except Exception as exc:
        print(f"[{mkt}] error: {exc}")
