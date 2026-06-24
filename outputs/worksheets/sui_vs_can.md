# SUI vs CAN — Probability Cup worksheet

**Match:** Switzerland (home) vs Canada — 2026-06-24
**Method:** de-vig real markets; base-rate fallback only where no market exists.
**Default de-vig:** odds_ratio for hold > ~5%.

## Markets pasted / pulled

- **1X2 (9 books, Odds API):** consensus SUI 2.50 / Draw 2.95 / CAN 3.25 (hold 4.9%)
- **Total goals O/U 2.5 (Odds API):** Over ~2.24 / Under ~1.68 (cross-check only)
- **BTTS (FD/BetRivers/DK):** Yes ~1.78 / No ~1.97 (hold 6.9%)
- **2H total goals O/U 1.5 (BetMGM):** Over 2.25 / Under 1.57 (hold 8.1%)
- **Player SoT 1+ ladders (FanDuel):**
  - Xhaka over 0.5 @ 2.25 (+125), 1.5 @ 9.0 (+800); BetRivers 0.5 @ 2.60, 1.5 @ 9.0
  - J. David 1+ @ -210, 2+ @ +240, 3+ @ +900
- **Team SoT ladders (FanDuel, full match):** SUI 3+ -600 … ; CAN 3+ -390 …
- **Team Most SoT 3-way (FanDuel, full match):** SUI -120 / Draw +550 / CAN +145
- **No market found:** fouls comparison (Q1), Switzerland offsides (Q2), 2H cards (Q3), penalty (Q5)

## Derivations (steps)

**Q4 — BTTS AND 3+ goals (DERIVED):**
- BTTS de-vig (odds_ratio): raw Yes 0.561 / No 0.509 → P(BTTS) = **0.526**
- compose: P(BTTS ∧ ≥3 goals) = P(BTTS) × (1 − P(1-1 | BTTS)), factor 0.21 → 0.526 × 0.79 = **0.416**
- cross-check: P(total ≥3 goals) from O/U 2.5 over = 0.426; answer must sit ≤ min(0.526, 0.426) ✓
- → **0.42**, Low confidence (correlation/exclusion assumption injected).

**Q6 — Switzerland more SoT than Canada in 2H (DERIVED):**
- Fit Poisson to full-match team SoT ladders → λ_SUI = 4.80, λ_CAN = 4.30
- Halve for 2H (even split) → λ_SUI_2H = 2.40, λ_CAN_2H = 2.15
- Independent Poisson P(SUI > CAN in 2H) = **0.449**
- Anchor check: full-match Most-SoT 3-way de-vig → SUI 0.501 / Draw 0.132 / CAN 0.366; independent-ladder full-match P(SUI>CAN) = 0.499 → **matches the direct 3-way (0.501) almost exactly**, so independence holds here. 2H number is lower (0.449) only because a single half has more ties.
- → **0.45**, Low confidence (half-split + independence). Pick NO (SUI not favored to *strictly* out-shoot CAN in 2H).

**Q9 — Xhaka 1+ SoT (LADDER FIT, 2-book consensus):** Aggregated FanDuel + BetRivers rather than picking one book.
- FD over-only rungs [1+:0.444, 2+:0.111] → λ=0.60 → P(≥1)=0.451
- BetRivers rungs [1+:0.385, 2+:0.111] → λ=0.50 → P(≥1)=0.394
- Pooled (avg raw per rung [1+:0.4145, 2+:0.111]) → λ=0.55 → **P(≥1)=0.423**; matches average-of-P (0.422) and average-of-λ (0.423).
- → **0.42**, Medium. (Single-book picks 0.45/0.39 bracket it.)

**Q10 — J. David 1+ SoT (LADDER FIT, 2-book consensus):** Pooled FanDuel + BetRivers.
- FD rungs [1+:0.690, 2+:0.303, 3+:0.100] → λ=1.15 → P(≥1)=0.683
- BetRivers rungs [1+:0.645, 2+:0.303, 3+:0.125] → λ=1.10 → P(≥1)=0.667
- Pooled rungs → λ=1.10 → **P(≥1)=0.667**.
- → **0.67**, Medium.

## Final table

| # | Question | Fair (our) | Crowd (de-vig) | Pick | Method | Conf |
|---|----------|-----------:|---------------:|------|--------|------|
| 1 | Canada more fouls than Switzerland | 56% | — | YES | base-rate (no market) | Low |
| 2 | Switzerland caught offside 2+ times | 40% | — | NO | base-rate (no market) | Low |
| 3 | 2+ total cards in 2nd half | 73% | — | YES | base-rate (no market) | Low |
| 4 | BTTS AND 3+ total goals | 42% | 42% | NO | derived (BTTS×excl-1-1) | Low |
| 5 | Penalty awarded in match | 42% | — | NO | base-rate (no market) | Low |
| 6 | Switzerland more SoT than Canada 2H | 45% | 45% | NO | derived (ladders→½→Poisson) | Low |
| 7 | Switzerland win | 38% | 38% | NO | direct 3-way | High |
| 8 | 2H 2+ total goals | 40% | 40% | NO | direct 2-way | Medium |
| 9 | Granit Xhaka 1+ SoT | 42% | 42% | NO | ladder fit (2-book consensus) | Medium |
| 10 | Jonathan David 1+ SoT | 67% | 67% | YES | ladder fit | Medium |

No deviations from market on any row — `our_prob = crowd_prob` everywhere a market existed (evidence-only rule; no leans applied).
