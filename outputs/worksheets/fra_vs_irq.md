# FRA vs IRQ — Probability Cup worksheet

**Match:** France (home) vs Iraq (away) — FIFA World Cup
**Kickoff:** 2026-06-22 21:00 UTC (5:00pm ET)
**Predicted:** 2026-06-22

France is a heavy favorite (~91% to win). Market picture coheres across sources:
match-goals λ ≈ 3.95, France corner mean ≈ 7.2 vs Iraq ≈ 2.3, France blowout-shaped.
8 of 9 questions are market-grounded; only Q2 (fouls) and Q3 (cards) fall to
calibrated base-rate (quarantined, Low confidence).

## Sources used
- **Kalshi** ($31M vol, real-money) — match 3-way, BTTS, Over 2.5, team totals,
  half-result 3-ways, half-total ladders.
- **FanDuel** — team SoT ladders + each-half SoT, corner ladders + each-half
  corners, France/Iraq First Half Goals 3-ways.
- **Action Network** — moneyline (draw missing), team totals (used as cross-check).

## Markets pasted (de-vigged)
| Market | Source | Raw | De-vig |
| --- | --- | --- | --- |
| Match 3-way FRA 92/9 · Tie 7/94 · IRQ 3/98 | Kalshi | sum 100.5 | **FRA 91.0 / Tie 6.5 / IRQ 2.5** |
| Over 2.5 goals 76/25 | Kalshi | — | 75% |
| BTTS 35/66 | Kalshi | — | 34.5% |
| France team total o2.5 69/32 | Kalshi | — | 68.5% (→ FRA λ≈3.55) |
| Iraq team total o0.5 35/66 | Kalshi | — | 34.5% (→ IRQ λ≈0.42) |
| 1H total ladder O0.5/1.5/2.5/3.5 = 85/55/29/12 | Kalshi | — | 1H λ≈1.85 |
| 2H total ladder O0.5/1.5/2.5/3.5 = 89/64/37/17 | Kalshi | — | 2H λ≈2.10 |
| France First Half Goals No/1/2+ = +320/+175/-110 | FanDuel | sum 112.6 | No-1H 21.1% → **scores 79%** |
| Iraq First Half Goals No/1/2+ = -600/+420/+3500 | FanDuel | sum 107.7 | scores-1H ~20% |
| Iraq team SoT 3+/4+/5+ = +270/+750/+2000 | FanDuel | — | ladder λ≈1.85 |
| Iraq SoT 1+/2+ each half = +200/+1800 | FanDuel | — | per-half P(≥2)≈0.23 |
| Corners total (9.5 ≈ pick'em); France 7.5 ≈ 50%; Iraq 2.5 o ≈ 38% | FanDuel | — | FRA mean≈7.2, IRQ mean≈2.3 |
| First Half Corners (median ≈ 4.7) | FanDuel | — | 1H ≈ 49% of corners |

## Final table
| # | Question | Fair (our) | Crowd (de-vig) | Pick | Method | Conf |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Iraq more 1H corners than France | 10% | 10% | NO | derived (each-half corner market) | Low |
| 2 | France more fouls than Iraq | 40% | — | NO | base-rate (no market) | Low |
| 3 | Iraq ≥1 card in 2H | 72% | — | YES | base-rate (no market) | Low |
| 4 | BTTS & 3+ goals | 32% | 32% | NO | derived (Over2.5×BTTS − P(1-1)) | Med |
| 5 | Iraq 2+ SoT in 2H | 23% | 23% | NO | derived (SoT half-split, cross-val) | Med |
| 6 | France win | 91% | 91% | YES | direct 3-way | High |
| 7 | Iraq score in 2H | 20% | 20% | NO | derived (1H mkt + match rate), odds-ratio | Med |
| 8 | Iraq 4+ SoT (full match) | 11% | 11% | NO | ladder fit | Med |
| 9 | France score in 1H | 80% | 80% | YES | direct 3-way, odds-ratio | High |

**De-vig method:** market legs use the **odds-ratio** method (chosen default for
hold > ~5%) instead of proportional. Only Q9 (79→80) and Q7 (19→20) moved; Q6 is
method-invariant (0.5% hold), and the one-sided SoT/corner ladders have no clean
booksum to redistribute. All four methods' numbers per market are logged to
`outputs/results/devig_bakeoff.csv` so settled Brier can re-evaluate the choice.

## De-vig steps for derived / indirect questions

### Q1 — Iraq more 1H corners than France (derived, market-anchored, Low)
No market prices this exact question, so it must be derived. Primary anchor is the
most *relevant* market, not an independence reconstruction:
- **Primary — *Most Corners in Each Half: France -290*** (~70% de-vig that France
  has the most corners in *both* halves). France winning the 1H battle alone is
  higher than winning both → ~80%. 1H corner ties ≈ 10% (France 1H λ≈3.6, Iraq
  λ≈1.1 → Σ P(F=k)P(I=k) ≈ 0.10). → **Iraq ≈ 10%.**
- **Cross-check — independent Poisson** on the FanDuel France/Iraq corner ladders
  (France 1H λ≈3.6, Iraq 1H λ≈1.1) → P(Iraq > France) ≈ 8%.
- Brackets 8–10%; settle **10%**, **our = crowd**.
- **Lean dropped.** The prior version shrank Iraq up to 12% citing a "corner
  independence trap." That rested on a single logged miss (ARG-AUT, our 20 vs
  crowd 30, n=1) and a mechanism that doesn't hold: positive inter-team
  correlation would push the *underdog down*, not up, so the cited rationale was
  wrong. Removed — Q1 is now a straight market-anchored derivation.

### Q4 — BTTS & 3+ goals (derived, Med)
- BTTS = 34.5% (Kalshi). The only BTTS scoreline with < 3 goals is 1-1.
- France λ ≈ 3.55 (from team total o2.5 = 68.5%) → P(France=1) ≈ 0.10.
- Iraq λ ≈ 0.42 (from to-score 34.5%) → P(Iraq=1) ≈ 0.28.
- P(1-1) ≈ 0.10 × 0.28 ≈ 2.8%.
- **Q4 = 34.5% − 2.8% ≈ 32%.**

### Q5 — Iraq 2+ SoT in 2H (derived, Med)
- Iraq match SoT λ ≈ 1.85 (ladder fit). 2H share ≈ 53% (goal-data half-skew) → 2H λ ≈ 0.95.
- P(≥2) at λ=0.95 ≈ 24%.
- Cross-check: *Iraq 1+ SoT each half* +200 → 33% ≈ (per-half P≥1)² → per-half λ ≈ 0.9;
  *Iraq 2+ SoT each half* +1800 → 5.3% ≈ (per-half P≥2)² → per-half P(≥2) ≈ 0.23.
- **Q5 ≈ 23%.**

### Q7 — Iraq score in 2H (derived, Med)
- FanDuel Iraq First Half Goals de-vig → Iraq scores 1H ≈ 20%.
- Iraq match to-score = 34.5% (Kalshi/AN agree).
- Independent halves: P(no goal match) = 0.655 = P(no 1H)·P(no 2H) = 0.80·P(no 2H)
  → P(no 2H) ≈ 0.82 → **P(Iraq scores 2H) ≈ 18–19%.**

### Q8 — Iraq 4+ SoT full match (ladder fit, Med)
- Iraq team SoT ladder: 3+ +270 (27%), 4+ +750 (11.8%), 5+ +2000 (4.8%).
- Poisson fit → λ ≈ 1.85 → **P(≥4) ≈ 11%.**

### Q9 — France score in 1H (direct 3-way, High)
- France First Half Goals: No +320 (23.8%) / Exactly1 +175 (36.4%) / 2+ -110 (52.4%); sum 112.6%, hold 12.6%.
- De-vig No-1H-goal = 23.8 / 112.6 = 21.1% → **France scores 1H = 79%.**

### Q6 — France win (direct 3-way, High)
- Kalshi mid: France 91.5 / Tie 6.5 / Iraq 2.5 (sum 100.5, near vig-free) → **France 91.0%.**
- **Source-conflict note:** Action Network's 2-way ML (FRA -437 / IRQ +1494) summed
  to 87.7% — the draw was missing — and implied only ~77% for France. Kalshi
  (real-money, deep, clean 3-way) used as the anchor. The biggest open risk on this slate.

## Base-rate fallbacks (quarantined — NOT market numbers)
- **Q2 France more fouls than Iraq = 40%.** Prior `underdog_more_fouls = 0.56`
  (the defending underdog, Iraq, fouls more) → favorite-more ≈ 0.40. Low.
- **Q3 Iraq ≥1 card in 2H = 72%.** Prior `mean_2h_cards = 2.6` total; Iraq ~55%
  share → ~1.4 → P(≥1) ≈ 0.72. Low. No bookings market existed on FanDuel.

## Method notes / risks
- France-dominant slate; most picks are low-probability NOs on Iraq doing things.
- Q6 source conflict (Kalshi 91 vs AN ~77) is the single biggest divergence — watch it.
- Q1 is now a straight market-anchored derivation (our = crowd = 10), no lean.
  The earlier "independence-trap" shrink was dropped as unproven (n=1) and
  wrongly reasoned.
- Q2/Q3 are pure base-rate — expect these to be our weakest rows.
