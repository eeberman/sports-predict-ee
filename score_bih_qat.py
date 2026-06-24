"""Step 3 scoring for BIH vs QAT. All de-vig + Poisson fits."""
import sys
sys.path.insert(0, ".")
from forecasting.compute import (
    american_to_prob, decimal_to_prob, cents_to_prob,
    devig_method, devig_all_methods, implied_margin,
    fit_poisson_mean_from_ladder, poisson_p_a_greater_b, _pois_sf
)

def pct(p): return round(p * 100, 1)

sep = "-" * 60

# ── Q7: BIH win (Kalshi 1X2) ────────────────────────────────
print(sep); print("Q7: BIH win — Kalshi 1X2 (hold ~2%)")
raw7 = [cents_to_prob(71), cents_to_prob(19), cents_to_prob(12)]
print(f"  raw: BIH={pct(raw7[0])} Draw={pct(raw7[1])} QAT={pct(raw7[2])}  hold={pct(implied_margin(raw7))}")
all7 = devig_all_methods(raw7)
for m, v in all7.items():
    print(f"  {m:14} BIH={pct(v[0])} Draw={pct(v[1])} QAT={pct(v[2])}")
fair7 = devig_method(raw7)
print(f"  >>> DEFAULT (odds_ratio): BIH = {pct(fair7[0])}%")

# cross-check FD h2h decimal
raw7fd = [decimal_to_prob(1.37), decimal_to_prob(5.2), decimal_to_prob(7.0)]
fair7fd = devig_method(raw7fd)
print(f"  >>> FD cross-check (odds_ratio): BIH = {pct(fair7fd[0])}%")

# ── Q2: BIH more goals in 2H (Kalshi 2H ML) ────────────────
print(sep); print("Q2: BIH score more goals in 2H — Kalshi 2H moneyline (hold ~1%)")
raw2 = [cents_to_prob(60), cents_to_prob(28), cents_to_prob(13)]
print(f"  raw: BIH={pct(raw2[0])} Draw={pct(raw2[1])} QAT={pct(raw2[2])}  hold={pct(implied_margin(raw2))}")
fair2 = devig_method(raw2)
all2 = devig_all_methods(raw2)
for m, v in all2.items():
    print(f"  {m:14} BIH={pct(v[0])} Draw={pct(v[1])} QAT={pct(v[2])}")
print(f"  >>> DEFAULT (odds_ratio): BIH = {pct(fair2[0])}%")

# cross-check BetRivers h2h_h2 decimal
raw2br = [decimal_to_prob(1.71), decimal_to_prob(3.15), decimal_to_prob(5.6)]
fair2br = devig_method(raw2br)
print(f"  >>> BetRivers 2H ML cross-check (odds_ratio): BIH = {pct(fair2br[0])}%")

# ── Q8: total goals ≤ 2 (Under 2.5) ────────────────────────
print(sep); print("Q8: Match 2-or-fewer total goals (Under 2.5)")
raw8 = [american_to_prob(-158), american_to_prob(128)]  # Over, Under
print(f"  FD: raw Over={pct(raw8[0])} Under={pct(raw8[1])}  hold={pct(implied_margin(raw8))}")
all8 = devig_all_methods(raw8)
for m, v in all8.items():
    print(f"  {m:14} Under={pct(v[1])}")
fair8 = devig_method(raw8)
print(f"  >>> DEFAULT (odds_ratio): Under = {pct(fair8[1])}%")

# cross-check BetRivers 2.5
raw8br = [decimal_to_prob(1.55), decimal_to_prob(2.40)]
fair8br = devig_method(raw8br)
print(f"  >>> BetRivers 2.5 cross-check: Under = {pct(fair8br[1])}%")

# cross-check FD BTTS (used later to anchor total goals logic)
raw_btts = [decimal_to_prob(1.94), decimal_to_prob(1.82)]  # Yes, No
fair_btts = devig_method(raw_btts)
print(f"\n  BTTS (FD): raw Yes={pct(raw_btts[0])} No={pct(raw_btts[1])} hold={pct(implied_margin(raw_btts))}")
print(f"  BTTS fair (odds_ratio): Yes={pct(fair_btts[0])}% No={pct(fair_btts[1])}%")

# ── Q9: Džeko 1+ SoT (FD -450, one-sided) ──────────────────
print(sep); print("Q9: Džeko 1+ SoT — FD -450 (one-sided, est hold 8%)")
raw9 = american_to_prob(-450)
print(f"  Raw implied: {pct(raw9)}%")
est_hold = 0.08
fair9 = raw9 / (1 + est_hold)
print(f"  Shave half-hold (8% assumed): {pct(raw9 - est_hold/2):.1f}%")
print(f"  Proportional est (raw/1.08):  {pct(fair9):.1f}%")
print(f"  >>> USE: {pct(raw9 - est_hold/2):.1f}% (conservative mid-point)")

# Validate with FD 2+ SoT ladder
raw9_2plus = american_to_prob(105)
print(f"\n  Džeko 2+ SoT raw: {pct(raw9_2plus)}% (sanity: 1+ must be >> 2+)")

# ── Q3: QAT more SoT than BIH in 2H ────────────────────────
print(sep); print("Q3: QAT more SoT than BIH in 2H — FD Team Most SoT (full match proxy)")
# Full-match "Team Most SoT": BIH -600, Draw +1000, QAT +700
raw3 = [american_to_prob(-600), american_to_prob(1000), american_to_prob(700)]
print(f"  raw: BIH={pct(raw3[0])} Draw={pct(raw3[1])} QAT={pct(raw3[2])}  hold={pct(implied_margin(raw3))}")
fair3 = devig_method(raw3)
all3 = devig_all_methods(raw3)
for m, v in all3.items():
    print(f"  {m:14} BIH={pct(v[0])} Draw={pct(v[1])} QAT={pct(v[2])}")
print(f"  >>> DEFAULT full-match (odds_ratio): QAT = {pct(fair3[2])}%")

# Now fit BIH and QAT SoT Poisson means from FD team ladders for 2H derivation
print("\n  BIH SoT Poisson fit (full match):")
bih_sot_thresh = [3,4,5,6,7,8,9,10,11,12,13]
bih_sot_raw = [american_to_prob(-2500), american_to_prob(-700), american_to_prob(-300),
               american_to_prob(-155), american_to_prob(125), american_to_prob(230),
               american_to_prob(420), american_to_prob(750), american_to_prob(1400),
               american_to_prob(2500), american_to_prob(4500)]
mu_bih_sot = fit_poisson_mean_from_ladder(bih_sot_thresh, bih_sot_raw)
print(f"  λ_BIH_SoT = {mu_bih_sot}")

print("\n  QAT SoT Poisson fit (full match):")
qat_sot_thresh = [3, 4]
qat_sot_raw = [american_to_prob(-130), american_to_prob(200)]
mu_qat_sot = fit_poisson_mean_from_ladder(qat_sot_thresh, qat_sot_raw)
print(f"  λ_QAT_SoT = {mu_qat_sot}")

# 2H halved
mu_bih_sot_2h = mu_bih_sot / 2
mu_qat_sot_2h = mu_qat_sot / 2
print(f"\n  Halved for 2H: λ_BIH={mu_bih_sot_2h:.3f}  λ_QAT={mu_qat_sot_2h:.3f}")
p_qat_more_2h = poisson_p_a_greater_b(mu_qat_sot_2h, mu_bih_sot_2h)
print(f"  P(QAT > BIH SoT in 2H) independent Poisson = {pct(p_qat_more_2h):.1f}%")

# ── Q1: BIH more corners than QAT in 2H ────────────────────
print(sep); print("Q1: BIH more corners than QAT in 2H")

# BIH home corner ladder
print("\n  BIH home corner Poisson fit:")
bih_c_thresh = [3,4,5,6,7,8,9,10,11,12,13]
bih_c_raw = [american_to_prob(-2200), american_to_prob(-650), american_to_prob(-275),
             american_to_prob(-138), american_to_prob(118), american_to_prob(225),
             american_to_prob(390), american_to_prob(630), american_to_prob(920),
             american_to_prob(1400), american_to_prob(2200)]
mu_bih_c = fit_poisson_mean_from_ladder(bih_c_thresh, bih_c_raw)
print(f"  λ_BIH_corners = {mu_bih_c}")

# QAT away corner ladder
print("\n  QAT away corner Poisson fit:")
qat_c_thresh = [3, 4, 5, 6, 7]
qat_c_raw = [american_to_prob(-192), american_to_prob(134), american_to_prob(265),
             american_to_prob(520), american_to_prob(920)]
mu_qat_c = fit_poisson_mean_from_ladder(qat_c_thresh, qat_c_raw)
print(f"  λ_QAT_corners = {mu_qat_c}")

# 2H halved
mu_bih_c_2h = mu_bih_c / 2
mu_qat_c_2h = mu_qat_c / 2
print(f"\n  Halved for 2H: λ_BIH={mu_bih_c_2h:.3f}  λ_QAT={mu_qat_c_2h:.3f}")
p_bih_more_c_2h = poisson_p_a_greater_b(mu_bih_c_2h, mu_qat_c_2h)
print(f"  P(BIH > QAT corners in 2H) independent Poisson = {pct(p_bih_more_c_2h):.1f}%")

# cross-check with Most Corners in Each Half market
# Bosnia +120 (each half), Qatar +1600
raw_mc_each = [american_to_prob(120), american_to_prob(1600)]  # BIH wins both halves, QAT wins both halves
print(f"\n  'Most Corners in Each Half' — BIH wins BOTH halves: +120 raw={pct(american_to_prob(120))}%")
# This is P(BIH wins corners in EACH half) = P(BIH 1H) * P(BIH 2H) ≈ p_bih_c_2h^2
# So P(BIH 2H corners) ≈ sqrt(raw_bih_each_half / 100) ... rough
raw_bih_each = american_to_prob(120)
print(f"  BIH wins BOTH halves raw (no de-vig) = {pct(raw_bih_each):.1f}%")
print(f"  If symmetric halves: P(BIH wins one half) ≈ sqrt({pct(raw_bih_each):.1f}%) = {pct(raw_bih_each**0.5):.1f}%")

# Also validate with total corners
print("\n  Total corners O/U 10.5: Over=+270, Under=-400")
raw_total_ou = [american_to_prob(270), american_to_prob(-400)]
fair_total = devig_method(raw_total_ou)
print(f"  Fair Over 10.5 = {pct(fair_total[0]):.1f}%  → implied total mean")
total_thresh = [6,7,8,9,10,11,12,13,14,15]
# Total corners from "Number of Corners" ladder (Under side gives P(X<N) = P(X≤N-1))
# Under 9 = P(total ≤ 8) → P(X≥9) = 1 - P(total ≤ 8)
# Use Over ladder directly:
total_over_thresh = [5,6,7,8,9,10,11,12,13,14,15]
total_over_raw = [american_to_prob(-1250), american_to_prob(-600), american_to_prob(-300),
                  american_to_prob(-175), american_to_prob(-105), american_to_prob(160),
                  american_to_prob(250), american_to_prob(420), american_to_prob(700),
                  american_to_prob(1100), american_to_prob(1800)]
mu_total_c = fit_poisson_mean_from_ladder(total_over_thresh, total_over_raw)
print(f"  Total corners Poisson fit: λ_total = {mu_total_c}")
print(f"  Implied λ_BIH + λ_QAT = {mu_bih_c} + {mu_qat_c} = {round(mu_bih_c + mu_qat_c, 3)}")

# ── Base rates for Q4, Q5, Q6, Q10 ─────────────────────────
print(sep); print("Base rates")
print("  Q4 Penalty OR red card: 0.56 (composed from base rates)")
print("  Q5 QAT commit more fouls than BIH: ~0.56 (underdog_more_fouls)")
print("  Q10 QAT offside 2+: 0.40 (underdog base rate)")

# Q6 BIH more cards than QAT — derive from base rates
# No direct market. "X more cards than Y" - no market available.
# Base rate for underdog-more-cards is not directly in priors.
# In football, the less disciplined/more aggressive team tends to get more cards.
# BIH (home favorite) vs QAT (underdog). In WC 2026, BIH is favorite.
# Typically favorites get fewer cards (they control the ball, don't need to foul as much).
# But we don't have a prior. Let's say 40% that BIH get more cards (slight lean toward QAT getting more).
print("  Q6 BIH more cards than QAT: ~0.40 (base rate, no prior; underdog typically commits more fouls/cards)")
