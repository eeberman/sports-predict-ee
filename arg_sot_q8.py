"""Q8: P(ARG >= 6 SoT) — fit Poisson to the full team SoT ladder, de-vig."""
import sys
sys.path.insert(0, ".")
from forecasting import compute as c

def am(o):
    o = float(o)
    return 100.0/(o+100.0) if o > 0 else (-o)/(-o+100.0)

# Argentina team "X or more SoT" ladder (cumulative, with vig)
arg_sot = {
    3: -1500,
    4: -500,
    5: -220,
    6: -110,
    7: 175,
    8: 330,
    9: 600,
    10: 1100,
    11: 2000,
    12: 3500,
}

print("Raw implied P(>=N) (with vig):")
raw = {}
for n, o in arg_sot.items():
    raw[n] = am(o)
    print(f"  >= {n}: {raw[n]:.3f}")

# Fit Poisson mean to the survival ladder
thr = list(raw.keys())
probs = list(raw.values())
mu = c.fit_poisson_mean_from_ladder(thr, probs)
print(f"\nFitted Poisson mean (raw, vig-inflated): {mu:.2f}")
print(f"  Poisson P(>=6 | mu={mu:.2f}) = {c._pois_sf(6, mu):.3f}")

# The raw ladder is vig-inflated. Estimate hold from the fact a fair survival
# function must be internally consistent; a Poisson fit absorbs some vig.
# Cross-check: the single 6+ line at -110 raw = 0.524.
print(f"\nSingle-rung read: 6+ at -110 = {am(-110):.3f} raw implied")

# De-vig estimate: typical 2-way SoT prop holds ~6-8%. If No side ~ -110 too,
# fair ~0.50. Shave ~3-4 pts off raw 0.524 -> ~0.49-0.50.
print("De-vigged estimate P(ARG >= 6 SoT): ~0.48-0.50")
