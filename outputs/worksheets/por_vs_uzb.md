# Portugal vs Uzbekistan — 2026-06-23 17:00 UTC
## Probability Cup Worksheet

---

## Questions & Market Mapping

| # | Question | Family | Market found |
|---|----------|--------|--------------|
| 1 | Will Uzbekistan be caught offside 2+ times? | offsides / team_offsides | ❌ None |
| 2 | In the 2H, will Portugal have more SoT than Uzbekistan? | shots / shots_comparison | Partial: FD Team Most SoT 3-way (FT) + each-half prop |
| 3 | Will Portugal be caught offside 2+ times? | offsides / team_offsides | ❌ None |
| 4 | Will a penalty kick be awarded OR a red card be shown? | discipline / penalty_or_red_card | Partial: Kalshi Red Card 28¢/74¢; no penalty market |
| 5 | Will Eldor Shomurodov have 1+ SoT in the 2H? | player_markets / player_shot_on_target | Partial: FD one-sided (FT +120, 1H +300, each-half +1500) |
| 6 | Will both teams score AND match have 3+ total goals? | goals_totals / btts_and_over | ✅ FD BTTS & O/U 2.5 (4-way) |
| 7 | Will Portugal win the match? | match_result / team_win | ✅ FD 1X2 via WDW+O/U combos (6-way) |
| 8 | Will the 2H have 2+ total goals? | goals_totals / total_goals_over | Partial: FD O/U 3.5 + 1H O/U 1.5 → Poisson split |
| 9 | Will Uzbekistan have 4+ SoT? | shots / team_shots_over | Partial: FD one-sided ladder (3+,4+,5+,6+) |
| 10 | Will Gonçalo Ramos score (excl. own goals)? | player_markets / player_goal | ✅ FD Anytime Goalscorer −125 |

---

## Markets Pasted

### 1X2 Moneyline (from Action Network consensus + FD)
- Portugal: −700 (FD), −700 (consensus)
- Uzbekistan: +1900 (FD), +1650 (consensus)
- Draw: estimated from WDW+O/U combos

### BTTS & O/U 2.5 (FanDuel, 4-way)
- BTTS Yes & Over 2.5: +175
- BTTS Yes & Under 2.5: +1500
- BTTS No & Over 2.5: +175
- BTTS No & Under 2.5: +200
- Booksum: 36.36 + 6.25 + 36.36 + 33.33 = 112.3% (hold = 12.3%)

### Total Goals O/U 3.5 (FanDuel / consensus)
- Over 3.5: +120 (FD) → implied 45.45%
- Under 3.5: −148 (FD) → implied 59.68%
- Sum = 105.13%, hold = 5.13%

### 1st Half O/U 1.5 (FanDuel)
- Over 1.5: +108 → implied 48.08%
- Under 1.5: −138 → implied 57.98%
- Sum = 106.06%, hold = 6.06%

### WDW + O/U 1.5 Goals (FanDuel, 6-way)
- Portugal & Over 1.5: −400 → 80.00%
- Portugal & Under 1.5: +750 → 11.76%
- Draw & Over 1.5: +1100 → 8.33%
- Draw & Under 1.5: +2000 → 4.76%
- UZB & Over 1.5: +2700 → 3.57%
- UZB & Under 1.5: +3500 → 2.78%
- Sum = 111.3% (hold = 11.3%)

### Team Most SoT in Each Half (FanDuel, partial)
- Portugal: −270 → implied 72.97%
- (other legs not pasted)

### Team SoT Ladders — Portugal (FanDuel)
| Threshold | Odds | Implied |
|-----------|------|---------|
| 7+ | −175 | 63.6% |
| 8+ | +105 | 48.8% |
| 9+ | +185 | 35.1% |
| 10+ | +310 | 24.4% |
| 11+ | +550 | 15.4% |
| 12+ | +950 | 9.5% |

### Team SoT Ladders — Uzbekistan (FanDuel)
| Threshold | Odds | Implied |
|-----------|------|---------|
| 3+ | +170 | 37.0% |
| 4+ | +470 | 17.5% |
| 5+ | +1200 | 7.7% |
| 6+ | +3000 | 3.2% |

### Shomurodov Player SoT Props (FanDuel, one-sided)
- 1+ SoT (FT): +120 → 45.45%
- 1+ SoT (1H): +300 → 25.00%
- 1+ SoT (each half): +1500 → 6.25%

### Kalshi — Red Card
- Yes: 28¢, No: 74¢ → booksum 102¢ (hold ~2%)
- De-vigged: P(red card) = 28/102 = **27.5%**

---

## De-vig Derivations

### Q7: Portugal win — 3-way OR from 6-way WDW combos

Reconstructed raw 3-way from WDW+O/U 1.5:
- POR raw: 0.800 + 0.118 = 0.918
- Draw raw: 0.083 + 0.048 = 0.131
- UZB raw: 0.036 + 0.028 = 0.064
- Sum = 1.113

OR de-vig (binary search for c ≈ 1.60 → all probs sum to 1):
- **POR fair = 87.5%**, Draw = 8.6%, UZB = 4.1%

Bake-off (all 4 methods, YES = Portugal wins):
| Method | Portugal |
|--------|----------|
| Proportional | 82.5% |
| Odds-ratio (default) | **87.5%** |
| Shin | ~85.0% |
| Additive | ~88.0% |

### Q6: BTTS & Over 2.5 — 4-way OR

Raw: [36.36%, 6.25%, 36.36%, 33.33%], sum = 112.3%

OR de-vig (c ≈ 1.185):
- BTTS Yes & Over 2.5: **32.5%**
- BTTS Yes & Under 2.5: 5.0%
- BTTS No & Over 2.5: 32.5%
- BTTS No & Under 2.5: 30.0%

Bake-off (YES = BTTS & Over 2.5):
| Method | Prob |
|--------|------|
| Proportional | 32.4% |
| Odds-ratio (default) | **32.5%** |
| Shin | ~32.3% |
| Additive | ~33.3% |

### Q8: 2H 2+ goals — Poisson split

Step 1 — Fit λ_total from O/U 3.5 (OR method):
- Fair Over 3.5 = 42.9% (OR de-vig)
- P(X ≥ 4 | λ) = 42.9% → **λ_total ≈ 3.35**

Step 2 — Fit λ_1H from 1H O/U 1.5 (OR method):
- Fair 1H Over 1.5 = 45.0% (OR de-vig)
- P(X ≥ 2 | λ) = 45.0% → **λ_1H ≈ 1.5** [e^{-1.5} × 2.5 = 0.558 ≈ 0.55 ✓]

Step 3 — Residual:
- **λ_2H = 3.35 − 1.5 = 1.85**

Step 4 — P(2H goals ≥ 2 | λ=1.85):
- P(0) = e^{-1.85} = 0.157
- P(1) = 1.85 × 0.157 = 0.291
- **P(≥2) = 1 − 0.157 − 0.291 = 55.2%**

### Q9: UZB 4+ SoT — Poisson fit from ladder

Raw implied ladder: [37.0%, 17.5%, 7.7%, 3.2%] at thresholds [3, 4, 5, 6]

Best-fit Poisson (minimizing squared error, grid 0.05 step):
**λ_UZB_SoT = 2.2**

Check: P(≥3|2.2)=37.7%, P(≥4|2.2)=18.1%, P(≥5|2.2)=7.3%, P(≥6|2.2)=2.5% — all close to raw.

**P(UZB ≥ 4 SoT) = 18.1%**

### Q2: Portugal more 2H SoT — raw Poisson (no tempering)

Step 1 — Fit λ_POR_SoT from ladder (thresholds 7–12):
- Best fit: **λ_POR_SoT = 7.6**
- Check: P(≥8|7.6) ≈ 49% ✓ (market +105 = 48.8%)

Step 2 — Per-half lambdas:
- λ_POR_half = 7.6/2 = 3.8
- λ_UZB_half = 2.2/2 = 1.1

Step 3 — Poisson comparison P(POR > UZB in a half):
- P(UZB=0)=0.333 × P(POR>0|3.8)=0.978 = 0.326
- P(UZB=1)=0.366 × P(POR>1|3.8)=0.893 = 0.327
- P(UZB=2)=0.201 × P(POR>2|3.8)=0.731 = 0.147
- P(UZB=3)=0.074 × P(POR>3|3.8)=0.526 = 0.039
- P(UZB≥4)=0.026 × ~0.345 = 0.009
- **Raw P(POR > UZB in 2H) ≈ 84.7%** → rounded to **85%**

Note: `temper_2h_dominance` NOT applied. The shrink constant (GAME_STATE_SHRINK=0.55)
was calibrated on a single match (ESP-KSA) and is not statistically robust.
Market cross-check: FD "each-half" Portugal −270 implies ~81% for the *compound*
(both halves), which is a floor. Raw Poisson 85% for 2H-only is consistent.
See `reports/modeling_plan.md` for the tempering backlog item.

### Q5: Shomurodov 2H SoT — derivation from 3 one-sided props

Assumed hold ≈ 10% on each one-sided prop:
- P(FT ≥1 SoT) = 45.45% / 0.90 = 50.5%
- P(1H ≥1 SoT) = 25.00% / 0.90 = 27.8%
- P(each half ≥1 SoT) = 6.25% / 0.90 = 6.9%

Identity: P(FT) = P(1H) + P(2H) − P(each half)
→ **P(2H ≥1 SoT) = 50.5 − 27.8 + 6.9 = 29.6% ≈ 30%**

### Q4: Penalty OR Red Card — composed

- P(red card) = Kalshi de-vig = 28/(28+74) = **27.5%**
- P(penalty awarded) = base rate = **42%** (no market found; SB WC VAR-era base)
- Independence assumed (reasonable approximation):
- **P(pen OR red) = 1 − (1−0.42) × (1−0.275) = 1 − 0.580 × 0.725 = 57.9% ≈ 58%**

### Q1 / Q3: Offsides — base rate

No offside market found for either team.
- Base rate (underdog): 0.40 → Q1 = **40%**
- Base rate (favorite): 0.40 → Q3 = **40%**

### Q10: Gonçalo Ramos — benched, base-rate sub estimate

**Timeline:**
1. Initial scan: not visible in FD → flagged "lineup unconfirmed" (12% bench estimate, Low conf)
2. User found DK Anytime Goalscorer −125 → updated to 53% (starting, Medium conf)
3. Pre-game lineup: Ramos confirmed NOT starting. DK pulled the market. **Final: 22%, Low conf.**

**Final derivation:**
- DK Anytime Goalscorer pulled (lineup confirmed benched).
- Polymarket O/U 0.5: YES 24¢ / NO 98¢ — incoherent binary (sums to 122¢); YES is stale
  pre-lineup last-trade. NO at 98¢ implies 2% and is directionally consistent but from a
  thin single-side trade, not a settled market. Not used as primary.
- Expected minutes: 20 min (actual history: 8 min in WC G1 vs Morocco; 25 min in pre-tournament friendly)
- Formula: P(scores) = P(starting, 90 min) × (minutes / 90)
  = 53% × (20/90) = **11.8% ≈ 12%**
- Confidence: **Low** (no clean sub market; linear time scaling from starting market is an approximation)

---

## Final Table

| # | Question | Fair prob (our) | Crowd (de-vig) | Pick | Method | Confidence |
|---|----------|----------------|----------------|------|--------|------------|
| 1 | UZB caught offside 2+ times | 40% | — | **NO** | base-rate, no market | Low |
| 2 | Portugal more 2H SoT than UZB | 85% | — | **YES** | raw Poisson (no tempering); λ_POR/2=3.8 vs λ_UZB/2=1.1 | Medium |
| 3 | Portugal caught offside 2+ times | 40% | — | **NO** | base-rate, no market | Low |
| 4 | Penalty OR red card | 58% | — | **YES** | derived: Kalshi red + base penalty, independence | Medium |
| 5 | Shomurodov 1+ SoT in 2H | 30% | — | **NO** | derived from 3 one-sided FD props | Medium |
| 6 | BTTS AND 3+ total goals | 33% | 33% | **NO** | direct 4-way OR (hold 12.3%) | Medium |
| 7 | Portugal win | 88% | 88% | **YES** | direct 3-way OR from 6-way WDW combos | High |
| 8 | 2H 2+ total goals | 55% | — | **YES** | Poisson split (λ_2H=1.85) | Medium |
| 9 | UZB 4+ SoT | 18% | 18% | **NO** | Poisson fit from one-sided ladder (λ=2.2) | Medium |
| 10 | Gonçalo Ramos scores | 12% | — | **NO** | derived: 53% starting market × (20/90 min actual history) | Low |
