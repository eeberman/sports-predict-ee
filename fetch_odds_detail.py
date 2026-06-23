"""Check BTTS availability and pull team LOO rates for ARG vs AUT."""
import sys, re, json, statistics as st
sys.path.insert(0, ".")
from provider_probe.clients import the_odds_api as odds_client
from forecasting import team_loo_rates

# Check what market keys are actually available for WC
print("=== Checking additional market keys ===")
for mkt in ["btts", "both_teams_to_score", "team_totals", "alternate_totals"]:
    try:
        import time; time.sleep(1)
        ev = odds_client.get_odds("soccer_fifa_world_cup", regions="eu", markets=mkt)
        # Check if ARG vs AUT has this market
        for e in ev:
            if "argentina" in (e.get("home_team","") + e.get("away_team","")).lower():
                bks_with_mkt = [b for b in e.get("bookmakers",[]) if b.get("markets")]
                print(f"  {mkt}: found for ARG vs AUT, {len(bks_with_mkt)} books")
                if bks_with_mkt:
                    for mk in bks_with_mkt[0]["markets"][:2]:
                        outcomes_str = ", ".join(f"{o['name']}={o['price']}" + (f"@{o.get('point','')}" if o.get('point') else "") for o in mk.get("outcomes",[]))
                        print(f"    {mk['key']}: {outcomes_str}")
                break
        else:
            print(f"  {mkt}: not available or no ARG match in feed")
    except Exception as exc:
        print(f"  {mkt}: 422/error ({exc})")

# Team LOO rates for Argentina and Austria
print("\n=== Team LOO rates ===")
try:
    tr = team_loo_rates.load()
    for team in ["Argentina", "Austria"]:
        print(f"\n  {team}:")
        for stat in ["sot_tot", "sot_2h", "cor_tot", "cor_2h", "foul", "card_2h"]:
            for direction in ["for", "against"]:
                try:
                    rate, n = tr.get_team_rate(team, None, stat, direction, shrink=True)
                    tag = tr.source_tag(team)
                    print(f"    {stat} {direction}: {rate:.2f}  (n={n}, src={tag})")
                except Exception as exc:
                    print(f"    {stat} {direction}: error ({exc})")
except Exception as exc:
    print(f"  Failed to load team LOO rates: {exc}")
