"""Fetch WC 2026 odds and map to ARG vs AUT markets."""
import sys, re, json, statistics as st
sys.path.insert(0, ".")
from provider_probe.clients import the_odds_api as odds_client
from forecasting import compute as c

def norm(s): return re.sub(r"[^a-z]", "", (s or "").lower())

home, away = "Argentina", "Austria"

# Pull h2h + totals + btts
try:
    ev_odds = odds_client.get_odds("soccer_fifa_world_cup", regions="us", markets="h2h,totals,btts")
    print(f"h2h+totals+btts: {len(ev_odds)} events")
except Exception as exc:
    print("h2h+totals+btts failed:", exc)
    ev_odds = []

if not ev_odds:
    try:
        ev_odds = odds_client.get_odds("soccer_fifa_world_cup", regions="eu", markets="h2h,totals")
        print(f"eu fallback: {len(ev_odds)} events")
    except Exception as exc:
        print("eu fallback failed:", exc)
        sys.exit(1)

print("\nAll events in feed:")
for e in ev_odds:
    print(f"  {e.get('home_team')} vs {e.get('away_team')}  t={e.get('commence_time')}")

want = {norm(home), norm(away)}
match_ev = next((e for e in ev_odds if {norm(e.get("home_team","")), norm(e.get("away_team",""))} == want), None)

if not match_ev:
    print(f"\nNo exact match for {home} vs {away}")
    sys.exit(0)

print(f"\nFound: {match_ev['home_team']} vs {match_ev['away_team']}")

# Aggregate across bookmakers -> median
agg = {}
for b in match_ev.get("bookmakers", []):
    for mk in b.get("markets", []):
        for oc in mk.get("outcomes", []):
            key = (mk["key"], oc.get("name"), oc.get("point"))
            agg.setdefault(key, []).append(oc.get("price"))

med = {k: st.median(v) for k, v in agg.items()}

print("\n--- H2H (decimal odds, median across books) ---")
eh = match_ev["home_team"]
for (mk, nm, pt), v in sorted(med.items()):
    if mk == "h2h":
        print(f"  {nm}: {v:.3f}  (implied {1/v:.3f})")

h = med.get(("h2h", eh, None))
d = med.get(("h2h", "Draw", None))
a_names = [nm for (mk, nm, pt) in med if mk == "h2h" and nm not in (eh, "Draw")]
a = med.get(("h2h", a_names[0], None)) if a_names else None

if h and d and a:
    ph_ev, pd, pa_ev = c.devig_three_way(1/h, 1/d, 1/a)
    if norm(eh) == norm(home):
        p_home, p_away = ph_ev, pa_ev
    else:
        p_home, p_away = pa_ev, ph_ev
    print(f"\n  De-vigged: ARG={p_home:.3f}  Draw={pd:.3f}  AUT={p_away:.3f}")
    fav_side = "home" if p_home >= p_away else "away"
    fav_strength = max(p_home, p_away)
    print(f"  Favorite: {fav_side} (ARG={p_home:.3f}), fav_strength={fav_strength:.3f}")

print("\n--- TOTALS ---")
over_entries = [(pt, v, len(agg[("totals","Over",pt)])) for (mk,nm,pt),v in med.items() if mk=="totals" and nm=="Over"]
for pt, v, cnt in sorted(over_entries, key=lambda x: -x[2]):
    un = med.get(("totals","Under",pt))
    if un:
        p_over = c.devig_two_way(1/v, 1/un)
        print(f"  Over {pt}: {v:.3f}  Under {pt}: {un:.3f}  -> P(over)={p_over:.3f}  ({cnt} books)")

print("\n--- BTTS ---")
btts_yes = med.get(("btts","Yes",None))
btts_no = med.get(("btts","No",None))
if btts_yes and btts_no:
    p_btts = c.devig_two_way(1/btts_yes, 1/btts_no)
    print(f"  BTTS Yes: {btts_yes:.3f}  No: {btts_no:.3f}  -> P(btts)={p_btts:.3f}")
else:
    print("  BTTS not available in feed")
