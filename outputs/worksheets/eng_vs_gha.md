# England vs Ghana — 2026-06-23 20:00 UTC
**WC 2026 Group Stage | Probability Cup**

---

## Markets pasted (Step 2)

### Moneyline
| Book | ENG | Tie | GHA |
|------|-----|-----|-----|
| Kalshi | 85¢ YES | 12¢ YES | 5¢ YES |
| DK | -600 | +600 | +1600 |
| FanDuel | -600 | — | +1500 |
| Consensus | -550 | — | +1400 |

### BTTS & O/U 2.5 (FanDuel 4-way)
| Leg | Odds | Raw implied |
|-----|------|------------|
| Yes & Over 2.5 | +170 | 37.0% |
| Yes & Under 2.5 | +1300 | 7.1% |
| No & Over 2.5 | +200 | 33.3% |
| No & Under 2.5 | +175 | 36.4% |
| **Sum / Hold** | | **113.9% / 13.9%** |

### Team SoT — each-half ladders (FanDuel, one-sided)
| Threshold (in EACH half) | England | Ghana |
|--------------------------|---------|-------|
| 1+ | -2000 (95.2%) | +115 (46.5%) |
| 2+ | -310 (75.6%) | +800 (11.1%) |
| 3+ | +110 (47.6%) | — |
| 4+ | +340 (22.7%) | — |

### Corners — Ghana (Away) total (FanDuel & Kalshi)
| Market | Odds | Raw implied |
|--------|------|------------|
| FD Away corners O 4.5 | +540 | 15.6% |
| FD Away corners U 4.5 | -1150 | 92.0% |
| Kalshi Ghana 5+ YES | 16¢ | 16.0% |
| Kalshi Ghana 5+ NO | 88¢ | 88.0% |
| **Kalshi hold** | | **4.0%** |

### Player props (FanDuel, YES only)
| Player | Market | Odds | Raw implied |
|--------|--------|------|------------|
| Harry Kane | Score or assist | -250 | 71.4% |
| Antoine Semenyo | 1+ SoT | +130 | 43.5% |

---

## Derivation steps

### Q4 — BTTS AND 3+ goals (direct 4-way)
Question maps to "Yes & Over 2.5" leg of the FanDuel 4-way BTTS×O/U 2.5 market.
- Raw: Yes&Over=37.0%, Yes&Under=7.1%, No&Over=33.3%, No&Under=36.4%
- Hold: **13.9%** (high — FD soft-book; odds-ratio method matters here)
- odds-ratio de-vig: **32.71%**
- proportional: 32.52%, shin: 33.14%, additive: 33.57%
- **Fair P(Q4 = YES) = 33%** ← chosen (odds-ratio)

### Q7 — England win (direct 3-way Kalshi)
- Kalshi: ENG 85¢ / Tie 12¢ / GHA 5¢ → hold 2.0%
- odds-ratio de-vig: **ENG=84.1%, Tie=11.3%, GHA=4.7%**
- All methods agree to <1pt (near-vig-free)
- **Fair P(Q7 = YES) = 84%**

### Q10 — Ghana 5+ corner kicks (direct 2-way Kalshi)
- Kalshi: YES 16¢ / NO 88¢ → hold 4.0%
- odds-ratio de-vig: **YES=13.9%, NO=86.1%**
- FD cross-check (Away 4.5, 7.6% hold, odds-ratio): 11.3% — directionally consistent but wider vig strip; Kalshi anchor preferred.
- **Fair P(Q10 = YES) = 14%**

### Q3 & Q1 — Both teams 1+ SoT in 2H / at halftime (derived, Poisson)

**Approach:** FanDuel's "Team SoT in Each Half" ladder prices P(team ≥N SoT in BOTH halves).
Under the symmetric-halves / independence assumption:
- P(N+ in each half) = [P(N+ in single half)]²
- So P_per_half(N+) = √P_each_half(N+)

After de-vig (shave 3.5% off each one-sided rung):

**England per-half:**
- 1+ each half: 95.2% → de-vig 91.8% → √91.8% = **95.9% per half** (one-sided)
  *(The ladder also has 2+, 3+, 4+ rungs — fitted jointly)*
- Best-fit Poisson λ_ENG_half = **3.50**
- P(ENG ≥1 SoT in 2H) = 1 − e^{-3.5} = **97.0%**

**Ghana per-half:**
- 1+ each half: 46.5% → de-vig 44.9% → √44.9% = **67.0% per half**
- 2+ each half: 11.1% → de-vig 10.7% → √10.7% = **32.7% per half**
- Best-fit Poisson λ_GHA_half = **1.15**
- P(GHA ≥1 SoT in 2H) = 1 − e^{-1.15} = **68.3%**

**Q3 (2H) = Q1 (1H)** under symmetric halves assumption:
P(both ≥1 in half) = 97.0% × 68.3% = **66.3% ≈ 66%**

Confidence: **Medium** (Poisson + independence + symmetric-halves — three assumptions stacked).
λ note for future calibration: λ_ENG_half = 3.50 (ladder-based, per-half), λ_GHA_half = 1.15.

### Q6 — Ghana more SoT than England in 2H (derived, Poisson comparison)
Using the same per-half Poisson fits as Q3/Q1:
- λ_GHA_half = 1.15, λ_ENG_half = 3.50
- P(GHA > ENG) = Σ_k P(GHA=k) × P(ENG ≤ k−1)
- **P(Q6 = YES) = 8.3% ≈ 8%**

Confidence: **Low** (positive within-half correlation between team SoT suppressed in independent Poisson — per corner-comparison-independence-trap memory, the sign of the bias is ambiguous. No direct 2H SoT comparison market available. Full-match "Team Most SoT" cross-check: GHA at ~5% de-vigged, so 8% for 2H alone is directionally plausible [higher variance, shorter window]).

### Q8 — Harry Kane score or assist (1-sided prop)
- FD YES: -250 → raw 71.4%
- Assumed total hold: 8% (FD player props)
- Shave half-hold: 71.4% − 4.0% = **67.4% ≈ 67%**
- Confidence: **Medium** (one-sided; vig estimate)

### Q9 — Semenyo 1+ SoT (1-sided prop)
- FD YES: +130 → raw 43.5%
- Assumed total hold: 8%
- Shave half-hold: 43.5% − 4.0% = **39.5% ≈ 39%**  
  *(Lineup confirmed — Semenyo on FanDuel board at +130)*
- Confidence: **Medium** (one-sided; vig estimate)

### Q2 — Ghana more fouls than England (base-rate)
- No foul-comparison market exists (Unlikely per market-existence table)
- Prior: `underdog_more_fouls = 0.56` (source: defending-side foul lean)
- **P(Q2 = YES) = 56%**
- Confidence: **Low**

### Q5 — Penalty kick OR red card (base-rate)
- No standalone penalty or red card market found
- Prior: `penalty_or_red = 0.56` (composed: 1 − (1−0.40)(1−0.30))
- **P(Q5 = YES) = 56%**
- Confidence: **Low**

---

## Final table

| # | Question | Fair prob | Crowd (de-vig) | Pick | Method | Conf |
|---|----------|-----------|----------------|------|--------|------|
| 1 | HT both teams 1+ SoT | **66%** | 66% | YES | Derived (Poisson each-half, λ_ENG=3.5, λ_GHA=1.15) | Medium |
| 2 | Ghana more fouls than England | **56%** | — | YES | Base-rate (no market) | Low |
| 3 | Both teams 1+ SoT in 2H | **66%** | 66% | YES | Derived (same Poisson, symmetric halves) | Medium |
| 4 | BTTS AND 3+ goals | **33%** | 33% | **NO** | Direct 4-way (FD BTTS×O/U 2.5, OR de-vig, 13.9% hold) | High |
| 5 | Penalty kick OR red card | **56%** | — | YES | Base-rate (no market) | Low |
| 6 | Ghana more SoT than England in 2H | **8%** | 8% | **NO** | Derived (Poisson P(GHA>ENG) per half) | Low |
| 7 | England win | **84%** | 84% | YES | Direct 3-way (Kalshi, 2% hold, OR de-vig) | High |
| 8 | Harry Kane score or assist | **67%** | 67% | YES | Direct 1-sided (-250; 8% hold est.; shave −4%) | Medium |
| 9 | Antoine Semenyo 1+ SoT | **39%** | 39% | **NO** | Direct 1-sided (+130; 8% hold est.; shave −4%) | Medium |
| 10 | Ghana 5+ corner kicks | **14%** | 14% | **NO** | Direct 2-way (Kalshi, 4% hold, OR de-vig) | High |

**YESes: Q1, Q2, Q3, Q5, Q7, Q8 (6/10)**  
**NOs: Q4, Q6, Q9, Q10 (4/10)**

---

## Bake-off log entries
| Question | Market | Hold | OR | Prop | Shin | Add |
|----------|--------|------|-----|------|------|-----|
| Q7 England win | Kalshi 3-way | 2.0% | 84.1% | 83.3% | 84.1% | 84.3% |
| Q4 BTTS & 3+ | FD 4-way | 13.9% | 32.7% | 32.5% | 33.1% | 33.6% |
| Q10 Ghana 5+ corners | Kalshi 2-way | 4.0% | 13.9% | 15.4% | 14.0% | 14.0% |

---

## Notes / post-mortem flags
- **Q10:** Kalshi odds-ratio (13.9%) and FD odds-ratio (11.3%) diverge by ~3pt — worth watching. If Ghana 5+ corners settles YES, that's meaningful evidence FD was over-stripping vig on the longshot.
- **Q4:** 13.9% hold is the highest of the slate. Shin/additive push YES up to 33-34% vs OR's 32.7%. Directionally near-irrelevant for the pick (all well below 50%) but logged for method comparison.
- **Q1/Q3:** Symmetric-halves assumption is the main risk. If Ghana is known to sit deep and counter (less likely to attack in 1H), the 1H SoT probability for Ghana is lower than 2H. No evidence to deviate currently.
- **Q2/Q5:** Base-rate only. Treat as wide-confidence-interval guesses; don't submit with conviction.
- **Q6:** Strong NO (8%). The main tail risk is Ghana using a high-line 2H press if chasing — but England at 84% win prob makes that scenario unlikely.
