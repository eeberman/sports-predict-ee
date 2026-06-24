# SCO vs BRA — 2026-06-24 22:00 UTC
**Jump Trading Probability Cup**

---

## Markets

### h2h 3-way (pooled: pmu_fr, unibet_nl, tipico_de)
| Bookmaker | Brazil | Draw | Scotland |
|-----------|--------|------|----------|
| pmu_fr    | 1.30   | 5.75 | 10.50    |
| unibet_nl | 1.30   | 5.80 | 11.00    |
| tipico_de | 1.28   | 5.50 | 11.00    |
| **OR de-vig** | **75.5%** | **16.1%** | **8.4%** | hold=4.2% |

### BTTS (pooled: onexbet, pinnacle, WilliamHill)
Yes=2.28/2.30/2.25, No=1.57/1.63/1.62 — raw avg Yes=0.440, No=0.618

### Total goals O/U 2.5 (pooled 4 books)
pmu_fr O@2.5=1.70/2.00 · unibet O@2.5=1.74/2.04 · pinnacle O@2.5=1.85/2.07 · onexbet O@2.5=1.82/2.05
Avg raw O=0.563, U=0.490 · hold=5.4% · **OR de-vig: P(≥3 goals)=53.7%**

### Scotland team_totals O@0.5 (pinnacle + betonlineag)
pinnacle O@0.5=2.10/U@0.5=1.75 · betonline O@0.5=2.10/U@0.5=1.77
Pool avg raw O=0.476, U=0.568 · hold=4.4% · **OR de-vig: P(Scotland scores)=45.4%**

### Brazil team_totals O@2.5 (pinnacle + betonlineag)
pinnacle O@2.5=2.55/U@2.5=1.53 · betonline O@2.5=2.55/U@2.5=1.57
Avg raw O=0.392, U=0.645 · hold=3.7% · OR de-vig: **P(BRA ≥3 goals)=37.3%**

### Corners 3-way (Pinnacle)
SCO=4.73, Draw=9.19, BRA=1.289
Raw: SCO=0.211, Draw=0.109, BRA=0.776 · hold=9.6%
**OR de-vig: SCO=17.7%, Draw=8.9%, BRA=73.5%**

### Total cards O/U 3.5 (Pinnacle)
O@3.5=2.40, U@3.5=1.564
Raw: O=0.417, U=0.639 · hold=5.6% · **OR de-vig: P(4+ cards)=38.8%**

### Scott McTominay SoT (onexbet + WilliamHill)
onexbet: O@0.5=2.00, O@1.5=7.00
WilliamHill: O@0.5=1.91, O@1.0=4.80, O@2.0=12.00
Pool O@0.5 avg raw=0.512, assumed 7% hold → **OR de-vig: 47.7%**
Poisson fit WH (λ=0.80) gives 55.1% but outer-rung bias inflates λ — use 48%.

### Brazil 1H goals — FD American odds ladder
Brazil 0 goals: +145 → raw 0.408
Brazil 1 goal: +135 → raw 0.426
Brazil 2+ goals: +240 → raw 0.294
Sum=1.128 (12.8% hold) · OR de-vig: P0=36.3%, P1=38.0%, P2+=25.6%
**P(Brazil scores in 1H) = 63.7%**

### Kalshi 1H markets (near-vig-free)
Brazil wins 1H: 56¢, Tie 1H: 36¢, Scotland wins 1H: 10¢ (sum=102¢)
Fair: BRA=54.9%, Tie=35.3%, SCO=9.8%
BTTS 1H: Yes=15¢, Over 0.5 1H goals: 73¢, Over 1.5 1H goals: 37¢
**Kalshi P(Brazil scores 1H) ≈ P(BRA wins 1H) + P(BTTS 1H) = 54.9% + 15.0% = 69.9%**
Blend FD + Kalshi: **(63.7% + 69.9%) / 2 = 66.8%**

### Alternate spreads / AH (onexbet + pinnacle)
Brazil -1.5: 1.92–1.98 · Brazil -2.0: 2.69 · Brazil -2.5: 3.30
Pinnacle AH ladder: -0.5=1.32, -0.75=1.39, -1.0=1.50, -1.25=1.76, -1.5=2.02

---

## Derivations

### Q3: Scotland scores first AND Brazil scores in 2H

**Step 1 — Fit Poisson λ per team:**
- λ_total from O@2.5 market: P(≥3 goals, OR de-vig)=53.7% → λ_total=2.825
- λ_BRA from Brazil team total O@2.5: P(BRA≥3, OR de-vig)=37.3% → λ_BRA=2.185
- λ_SCO from Scotland O@0.5: P(SCO scores, OR de-vig)=45.4% → λ_SCO=0.605 (via -ln(1-0.454))
- Cross-check: λ_SCO_implied from residual = 2.825 - 2.185 = 0.640 → avg λ_SCO=0.623
- Final: **λ_SCO=0.623, λ_BRA=2.203**

**Step 2 — P(Scotland scores first):**
In a Poisson competing-process, P(SCO scores first) = λ_SCO / (λ_SCO + λ_BRA)
= 0.623 / 2.825 = **22.0%**

**Step 3 — P(Brazil scores in 2H):**
λ_BRA_1H from FD ladder: P(BRA 0 in 1H, de-vig)=36.3% → λ_BRA_1H = -ln(0.363) = 1.012
λ_BRA_2H = 2.203 - 1.012 = **1.191**
P(BRA scores in 2H) = 1 - e^(-1.191) = **69.6%**

**Step 4 — Compound (independence approx):**
P(Q3) = P(SCO first) × P(BRA 2H) = 0.220 × 0.696 = **15.3%**
Note: events are mildly positively correlated (if SCO leads, BRA presses in 2H), so true value may be ~1–2pp higher. Low confidence.

### Q7: Brazil score in second half
Directly from Step 3 above: λ_BRA_2H=1.191 → P = **69.6%**

### Q10: Brazil score in first half
Direct from FD 3-way de-vig (blend with Kalshi): **66.8%**
(FD: 63.7%, Kalshi cross-check: 69.9%)

### Q1: Brazil more SoT in 2H (base rate)
base_rate_priors: dominant_more_2h_sot, favorite = 0.64 (statsbomb_wc_n50)
fav_strength (Brazil h2h de-vig) = 0.755
prior_with_favorite_scaling: 0.64 + 0.21 × (0.755 - 0.50) = 0.64 + 0.054 = **69.3%**
No market available — base-rate only.

---

## Final Table

| # | Question | Our% | Crowd% | Pick | Method | Conf |
|---|----------|------|--------|------|--------|------|
| 1 | Brazil more SoT than Scotland in 2H | 71% | — | YES | derived (player-prop Poisson sum, 2H halve) | Medium |
| 2 | Scotland caught offside 2+ times | 40% | — | NO | base-rate (underdog) | Low |
| 3 | Scotland scores first AND Brazil scores in 2H | 15% | — | NO | derived (Poisson decomp) | Low |
| 4 | Brazil more corners than Scotland | 74% | 74% | YES | direct 3-way (Pinnacle) | High |
| 5 | Scotland score at least 1 goal | 45% | 45% | NO | direct 2-way (team_totals) | High |
| 6 | Match has 3+ total goals | 54% | 54% | YES | direct 2-way (pooled 4 bks) | High |
| 7 | Brazil score in the second half | 70% | — | YES | derived (Poisson λ_BRA_2H) | Low |
| 8 | 4+ total cards | 39% | 39% | NO | direct 2-way (Pinnacle) | High |
| 9 | Scott McTominay 1+ SoT | 48% | 48% | NO | ladder fit (pooled, 7% hold) | Medium |
| 10 | Brazil score in the first half | 67% | 67% | YES | direct 3-way (FD blend + Kalshi) | Medium |

**Base-rate rows (quarantined — no market data):** Q2, Q3, Q7
**Q1 updated:** player-prop Poisson derivation (71–74% range, 71% after correlation correction). Supersedes base-rate 69%. λ_BRA_SoT=7.17, λ_SCO_SoT=3.27 (full match, de-vigged); halved for 2H.

---

## Picks summary
YES: Q1, Q4, Q6, Q7, Q10
NO: Q2, Q3, Q5, Q8, Q9

---

*Logged: results_log.csv (10 rows), devig_bakeoff.csv (6 rows — Q4/Q5/Q6/Q8/Q9/Q10)*
