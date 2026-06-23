"""De-vig every market-backed question for ARG vs AUT to a clean fair probability."""
import sys
sys.path.insert(0, ".")
from forecasting import compute as c

def am(o):
    o = float(o)
    return 100.0/(o+100.0) if o > 0 else (-o)/(-o+100.0)

print("=" * 78)
print("ARG vs AUT — de-vigged fair probabilities")
print("=" * 78)

# ── Q5: Argentina win — H2H 3-way (EU decimal: ARG 1.450 / Draw 4.500 / AUT 7.925)
print("\nQ5  Argentina win  [H2H 3-way]")
ph, pd, pa = c.devig_three_way(1/1.450, 1/4.500, 1/7.925)
hold = (1/1.450 + 1/4.500 + 1/7.925 - 1) * 100
print(f"     raw: ARG {1/1.450:.3f}  Draw {1/4.500:.3f}  AUT {1/7.925:.3f}  (hold {hold:.1f}%)")
print(f"     fair: ARG {ph:.3f}  Draw {pd:.3f}  AUT {pa:.3f}")
print(f"     -> P(ARG win) = {ph*100:.0f}%")

# ── Q6: <=2 total goals — O/U 2.5 (Over -108 / Under -112)
print("\nQ6  Match <=2 total goals  [O/U 2.5]")
o, u = am(-108), am(-112)
hold = (o + u - 1) * 100
p_under = c.devig_two_way(u, o)
print(f"     raw: Over {o:.3f}  Under {u:.3f}  (hold {hold:.1f}%)")
print(f"     fair: P(Under 2.5 = <=2 goals) = {p_under:.3f}  -> {p_under*100:.0f}%")

# ── Q3: 2H more goals than 1H — Half with Most Goals 3-way (1H +205 / 2H +114 / Tie +250)
print("\nQ3  2H more goals than 1H  [Half with Most Goals 3-way]")
r1h, r2h, rtie = am(205), am(114), am(250)
tot = r1h + r2h + rtie
hold = (tot - 1) * 100
p2h = r2h / tot
print(f"     raw: 1H {r1h:.3f}  2H {r2h:.3f}  Tie {rtie:.3f}  (hold {hold:.1f}%)")
print(f"     fair: P(2H most) = {p2h:.3f}  -> {p2h*100:.0f}%")

# ── Q8: ARG >=6 SoT — fit Poisson to full de-vigged-ish ladder
print("\nQ8  ARG >=6 SoT  [team SoT ladder]")
arg_sot = {3:-1500,4:-500,5:-220,6:-110,7:175,8:330,9:600,10:1100,11:2000,12:3500}
thr = list(arg_sot.keys()); probs=[am(o) for o in arg_sot.values()]
mu = c.fit_poisson_mean_from_ladder(thr, probs)
p6 = c._pois_sf(6, mu)
# single-rung de-vig assuming symmetric ~ -110/-110 no side -> shave half the per-rung vig
raw6 = am(-110)
print(f"     ladder Poisson mean {mu:.2f} -> P(>=6) {p6:.3f};  single rung raw {raw6:.3f}")
print(f"     -> P(ARG >=6 SoT) ~ {(p6+ (raw6-0.025))/2*100:.0f}% (call ~49%)")

# ── Q9: ARG score in 2H — derive from de-vigged ARG goal lines
print("\nQ9  ARG score in 2H  [derived from ARG goal markets]")
# P(ARG scores match): Home O/U 0.5 (Over -1000 / Under +560)
p_match = c.devig_two_way(am(-1000), am(560))
# P(ARG scores 1H): Home 1H O/U 0.5 (Over -166 / Under +130)
p_1h = c.devig_two_way(am(-166), am(130))
# P(ARG both halves): "To Score in Both Halves" ARG +146 (yes only -> shave ~5% vig)
p_both_raw = am(146)
p_both = p_both_raw - 0.04
p_2h = p_match - (p_1h - p_both)   # = scores - 1H_only
print(f"     P(scores match) {p_match:.3f}  P(1H) {p_1h:.3f}  P(both halves) ~{p_both:.3f}")
print(f"     P(1H only) {p_1h - p_both:.3f}  ->  P(2H) = {p_2h:.3f}  -> {p_2h*100:.0f}%")

# ── Q4: Austria more corners — Poisson from de-vigged team corner ladders (computed earlier)
print("\nQ4  Austria more corners than ARG  [team corner ladders]")
print("     ARG mu 5.15  AUT mu 3.25  ->  P(AUT>ARG) = 20%  (P(ARG more) 69%, tie 11%)")

# ── Q10: Sabitzer >=1 SoT — player prop (-105 yes only, no side not given)
print("\nQ10 Sabitzer >=1 SoT  [player prop -105]")
raw_s = am(-105)
print(f"     raw {raw_s:.3f} (yes only); typical prop hold ~6-8% -> fair ~{(raw_s-0.025)*100:.0f}%")

print("\n" + "=" * 78)
print("FINAL TABLE (de-vigged)")
print("=" * 78)
rows = [
    (3, "2H more goals than 1H", p2h, "direct 3-way"),
    (4, "Austria more corners than ARG", 0.20, "derived ladders"),
    (5, "Argentina win", ph, "direct 3-way"),
    (6, "Match <=2 total goals", p_under, "direct 2-way"),
    (8, "ARG >=6 SoT", 0.49, "ladder fit"),
    (9, "ARG score in 2H", p_2h, "derived"),
    (10,"Sabitzer >=1 SoT", raw_s-0.025, "prop (est)"),
]
for n,q,p,src in sorted(rows):
    print(f"  Q{n:<2} {q:<32} {p*100:>4.0f}%   {src}")
print("\n  Q1 offside, Q2 2H SoT h2h, Q7 cards: NO MARKET")
