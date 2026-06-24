"""Compute all fair probabilities for SCO vs BRA (2026-06-24)."""
import sys, math
sys.path.insert(0, ".")
from forecasting.compute import (
    devig_method, devig_all_methods, implied_margin,
    devig_odds_ratio, devig_shin, devig,
    fit_poisson_mean_from_ladder, _pois_sf, poisson_p_a_greater_b,
    american_to_prob, cents_to_prob, decimal_to_prob,
    prior_with_favorite_scaling,
)

print("=" * 65)
print("SCO vs BRA — de-vig worksheet | 2026-06-24")
print("=" * 65)

# ─── Q4: Corners 3-way (Pinnacle) ────────────────────────────────
print("\n── Q4: Brazil more corners than Scotland ──")
raw_c = [1/4.73, 1/9.19, 1/1.289]        # [SCO, Draw, BRA]
hold_c = implied_margin(raw_c)
fair_c = devig_method(raw_c)              # odds_ratio default
print(f"  Raw: SCO={raw_c[0]:.3f} Draw={raw_c[1]:.3f} BRA={raw_c[2]:.3f}  hold={hold_c:.1%}")
print(f"  OR de-vig: SCO={fair_c[0]:.3f} Draw={fair_c[1]:.3f} BRA={fair_c[2]:.3f}")
print(f"  => P(Brazil more corners) = {fair_c[2]:.1%}")

# ─── Q5: Scotland score 1+ (team_totals O@0.5, pool Pinnacle+BetOnline) ──
print("\n── Q5: Scotland score at least 1 goal ──")
# Pool raw probs before de-vigging (avg then de-vig)
raw_o5 = (1/2.10 + 1/2.10) / 2
raw_u5 = (1/1.75 + 1/1.77) / 2
raw5 = [raw_o5, raw_u5]
hold5 = implied_margin(raw5)
fair5 = devig_method(raw5)
print(f"  Raw pool: O={raw_o5:.4f} U={raw_u5:.4f}  hold={hold5:.1%}")
print(f"  OR de-vig: P(Scotland scores) = {fair5[0]:.1%}")
lam_sco = -math.log(fair5[1])
print(f"  Implied λ_SCO (Poisson) = {lam_sco:.3f}")

# ─── Q6: 3+ total goals (pool pmu_fr, unibet, pinnacle, onexbet alt O@2.5) ──
print("\n── Q6: 3+ total goals ──")
books_o6 = [1/1.70, 1/1.74, 1/1.85, 1/1.82]   # Over@2.5
books_u6 = [1/2.00, 1/2.04, 1/2.07, 1/2.05]   # Under@2.5
raw_o6 = sum(books_o6) / len(books_o6)
raw_u6 = sum(books_u6) / len(books_u6)
raw6 = [raw_o6, raw_u6]
hold6 = implied_margin(raw6)
fair6 = devig_method(raw6)
print(f"  Raw pool: O={raw_o6:.4f} U={raw_u6:.4f}  hold={hold6:.1%}")
print(f"  OR de-vig: P(3+ goals) = {fair6[0]:.1%}")

# Fit total λ from fair P(>2.5)
p3plus = fair6[0]
lam_lo, lam_hi = 0.1, 20.0
for _ in range(200):
    mid = (lam_lo + lam_hi) / 2
    (lam_lo, lam_hi) = (mid, lam_hi) if _pois_sf(3, mid) < p3plus else (lam_lo, mid)
lam_total = (lam_lo + lam_hi) / 2
print(f"  Implied λ_total (Poisson) = {lam_total:.3f}")

# Brazil λ from team_totals Brazil O@2.5 (pool pinnacle+betonline)
raw_bra_o = (1/2.55 + 1/2.55) / 2
raw_bra_u = (1/1.53 + 1/1.57) / 2
raw_bra = [raw_bra_o, raw_bra_u]
fair_bra = devig_method(raw_bra)
p_bra_3plus = fair_bra[0]
lam_lo2, lam_hi2 = 0.1, 20.0
for _ in range(200):
    mid2 = (lam_lo2 + lam_hi2) / 2
    (lam_lo2, lam_hi2) = (mid2, lam_hi2) if _pois_sf(3, mid2) < p_bra_3plus else (lam_lo2, mid2)
lam_bra = (lam_lo2 + lam_hi2) / 2
lam_sco2 = lam_total - lam_bra
print(f"  P(BRA ≥3) fair={p_bra_3plus:.1%}  λ_BRA={lam_bra:.3f}  λ_SCO_implied={lam_sco2:.3f}")
# Use average of two λ_SCO estimates
lam_sco_best = (lam_sco + lam_sco2) / 2
lam_bra_best = lam_total - lam_sco_best
print(f"  Best λ_SCO={lam_sco_best:.3f}  λ_BRA={lam_bra_best:.3f}")

# ─── Q8: 4+ total cards (Pinnacle O@3.5) ────────────────────────
print("\n── Q8: 4+ total cards ──")
raw8 = [1/2.40, 1/1.564]
hold8 = implied_margin(raw8)
fair8 = devig_method(raw8)
print(f"  Raw: O={raw8[0]:.4f} U={raw8[1]:.4f}  hold={hold8:.1%}")
print(f"  OR de-vig: P(4+ cards) = {fair8[0]:.1%}")

# ─── Q9: McTominay 1+ SoT (pool onexbet + WH O@0.5) ─────────────
print("\n── Q9: McTominay 1+ SoT ──")
# One-sided; use pooled raw and assume ~7% total hold
raw_mct_o = (1/2.00 + 1/1.91) / 2    # pool onexbet + WH
assumed_hold = 0.07
# raw_O + raw_U = 1 + hold → raw_U = 1 + hold - raw_O
raw_u9 = 1 + assumed_hold - raw_mct_o
raw9 = [raw_mct_o, raw_u9]
fair9 = devig_method(raw9)
print(f"  Pool raw O@0.5: onexbet=0.500 WH=0.524 avg={raw_mct_o:.4f}")
print(f"  Assumed hold {assumed_hold:.0%} → implied raw_U={raw_u9:.4f}")
print(f"  OR de-vig: P(McTominay 1+ SoT) = {fair9[0]:.1%}")
# Also Poisson fit from WH ladder
thresholds_mct = [1, 2]
raw_probs_mct = [1/1.91, 1/4.80]    # WH O@0.5 and O@1.0
lam_mct = fit_poisson_mean_from_ladder(thresholds_mct, raw_probs_mct)
print(f"  Poisson fit from WH ladder (O@0.5={1/1.91:.3f}, O@1.0={1/4.80:.3f}): λ={lam_mct:.3f}")
print(f"  Poisson P(SoT>=1; λ={lam_mct:.3f}) = {_pois_sf(1, lam_mct):.1%}")

# ─── Q10: Brazil score in 1H (FD 3-way ladder) ────────────────────
print("\n── Q10: Brazil score in first half ──")
raw10 = [
    american_to_prob(145),   # Brazil 0 goals 1H  (+145)
    american_to_prob(135),   # Brazil 1 goal 1H   (+135)
    american_to_prob(240),   # Brazil 2+ goals 1H (+240)
]
hold10 = implied_margin(raw10)
fair10 = devig_method(raw10)
print(f"  Raw: P0={raw10[0]:.4f} P1={raw10[1]:.4f} P2+={raw10[2]:.4f}  hold={hold10:.1%}")
print(f"  OR de-vig: P0={fair10[0]:.3f} P1={fair10[1]:.3f} P2+={fair10[2]:.3f}")
p_bra_1h = fair10[1] + fair10[2]
p_bra_0_1h = fair10[0]
print(f"  P(Brazil scores in 1H) = {p_bra_1h:.1%}")
lam_bra_1h = -math.log(p_bra_0_1h)
print(f"  λ_BRA_1H = {lam_bra_1h:.3f}")

# Kalshi cross-check
print(f"\n  Kalshi cross-check:")
kalshi_bra_wins_1h = cents_to_prob(56)
kalshi_tie_1h = cents_to_prob(36)
kalshi_sco_wins_1h = cents_to_prob(10)
kalshi_btts_1h = cents_to_prob(15)
sum_kalshi = kalshi_bra_wins_1h + kalshi_tie_1h + kalshi_sco_wins_1h
# de-vig the 3-way (2% hold)
fair_k = devig([kalshi_bra_wins_1h, kalshi_tie_1h, kalshi_sco_wins_1h])
print(f"  1H 3-way: BRA={fair_k[0]:.3f} Tie={fair_k[1]:.3f} SCO={fair_k[2]:.3f}  hold={sum_kalshi-1:.1%}")
p_bra_1h_kalshi = fair_k[0] + fair_k[1] * (kalshi_btts_1h / (kalshi_btts_1h + fair_k[1]))  # approx
# Simpler: P(BRA scores 1H) ≈ P(BRA wins 1H) + P(BTTS 1H)
p_bra_1h_kalshi2 = fair_k[0] + cents_to_prob(15)   # BRA wins + BTTS 1H
print(f"  P(BRA scores 1H) ≈ P(BRA wins) + P(BTTS): {fair_k[0]:.3f} + {cents_to_prob(15):.3f} = {p_bra_1h_kalshi2:.1%}")
p_bra_1h_final = (p_bra_1h + p_bra_1h_kalshi2) / 2
print(f"  Blended P(Brazil 1H score): FD={p_bra_1h:.1%}  Kalshi≈{p_bra_1h_kalshi2:.1%}  blend={p_bra_1h_final:.1%}")

# ─── Q7: Brazil score in 2H (derived from 1H Poisson + total λ) ──
print("\n── Q7: Brazil score in 2H ──")
lam_bra_2h = lam_bra_best - lam_bra_1h
p_bra_2h = _pois_sf(1, lam_bra_2h)
print(f"  λ_BRA total={lam_bra_best:.3f}  λ_BRA_1H={lam_bra_1h:.3f}  λ_BRA_2H={lam_bra_2h:.3f}")
print(f"  P(Brazil scores in 2H) = {p_bra_2h:.1%}")

# ─── Q3: Scotland first goal AND Brazil scores in 2H ──────────────
print("\n── Q3: Scotland scores first goal AND Brazil scores in 2H ──")
p_sco_first = lam_sco_best / (lam_sco_best + lam_bra_best)
p_q3 = p_sco_first * p_bra_2h
print(f"  P(SCO first goal) = λ_SCO / (λ_SCO + λ_BRA) = {lam_sco_best:.3f}/{lam_sco_best+lam_bra_best:.3f} = {p_sco_first:.1%}")
print(f"  P(BRA 2H score) = {p_bra_2h:.1%}")
print(f"  P(Q3, independence approx) = {p_q3:.1%}")

# ─── Q1: Brazil more SoT in 2H (base-rate + fav scaling) ─────────
print("\n── Q1: Brazil more SoT in 2H (base rate) ──")
# h2h de-vig to get Brazil win prob
raw_h2h = [1/1.30, 1/10.50, 1/5.75]    # BRA, SCO, Draw (averaged over books)
# Pool 3 books
raw_h2h_pool = [
    (1/1.30 + 1/1.30 + 1/1.28)/3,  # BRA
    (1/10.50 + 1/11.00 + 1/11.00)/3,  # SCO
    (1/5.75 + 1/5.80 + 1/5.50)/3,  # Draw
]
hold_h2h = implied_margin(raw_h2h_pool)
fair_h2h = devig_method(raw_h2h_pool)
fav_strength = fair_h2h[0]
print(f"  h2h pool: BRA={raw_h2h_pool[0]:.3f} SCO={raw_h2h_pool[1]:.3f} D={raw_h2h_pool[2]:.3f}  hold={hold_h2h:.1%}")
print(f"  OR de-vig: BRA={fair_h2h[0]:.3f} SCO={fair_h2h[1]:.3f} D={fair_h2h[2]:.3f}")
base_2h_sot = 0.64
p_q1 = prior_with_favorite_scaling(base_2h_sot, fav_strength)
print(f"  fav_strength={fav_strength:.3f}  base_rate=0.64")
print(f"  P(Brazil more 2H SoT) = {p_q1:.1%}  (base_rate + 0.21*(fav-0.5))")

# ─── Q2: Scotland 2+ offsides (base rate, underdog) ───────────────
print("\n── Q2: Scotland 2+ offsides (base rate, underdog) ──")
print("  base_rate_priors: offside_2plus, underdog = 0.40")
p_q2 = 0.40

# ─── Summary table ──────────────────────────────────────────────────
print("\n" + "=" * 65)
print("FINAL TABLE")
print("=" * 65)
results = [
    (1, "Brazil more SoT in 2H",         p_q1,     None,          "base-rate (fav scaling)",     "Low"),
    (2, "Scotland 2+ offsides",           p_q2,     None,          "base-rate (underdog)",        "Low"),
    (3, "Scotland first & BRA 2H score",  p_q3,     None,          "derived (Poisson decomp)",    "Low"),
    (4, "Brazil more corners",            fair_c[2], fair_c[2],    "direct 3-way (Pinnacle)",     "High"),
    (5, "Scotland scores 1+ goal",        fair5[0],  fair5[0],     "direct 2-way (team_totals)",  "High"),
    (6, "3+ total goals",                 fair6[0],  fair6[0],     "direct 2-way (pooled 4 bks)", "High"),
    (7, "Brazil score in 2H",             p_bra_2h,  None,         "derived (Poisson λ_BRA_2H)",  "Low"),
    (8, "4+ total cards",                 fair8[0],  fair8[0],     "direct 2-way (Pinnacle)",     "High"),
    (9, "McTominay 1+ SoT",              fair9[0],  fair9[0],     "ladder fit (pooled)",         "Medium"),
    (10,"Brazil score in 1H",            p_bra_1h_final, p_bra_1h_final, "direct 3-way (FD blend)", "Medium"),
]
print(f"{'#':>2}  {'Question':<35} {'Our%':>6} {'Crowd%':>7} {'Pick':>4}  {'Conf':<8}  Method")
print("-" * 110)
for q, desc, our, crowd, method, conf in results:
    pick = "YES" if our > 0.50 else "NO"
    crowd_s = f"{crowd:.1%}" if crowd is not None else "  —   "
    print(f"{q:>2}  {desc:<35} {our:>6.1%} {crowd_s:>7} {pick:>4}  {conf:<8}  {method}")
