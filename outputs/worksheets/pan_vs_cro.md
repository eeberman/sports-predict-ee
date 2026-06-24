# PAN vs CRO — Probability Cup worksheet

**Match:** Panama vs Croatia (WC 2026 group) · **Kickoff:** 2026-06-23 23:00 UTC
**Method:** de-vig real markets (FanDuel, DraftKings, Kalshi); base-rate fallback
where no market exists. Panama = home/underdog, Croatia = away/heavy favorite.

> **OPEN:** Q9 (Fajardo) and Q10 (L. Sučić) are pending the starting XI. See the
> lineup decision tree at the bottom. Update this file **and** `results_log.csv`
> together when lineups drop.

## Final table

| # | Question | Fair (our) | Crowd | Pick | Method | Conf |
|---|----------|-----------|-------|------|--------|------|
| 1 | Panama commit more fouls than Croatia? | 56% | — | YES | base-rate (no market) | Low |
| 2 | Panama caught offside 2+ times? | 40% | — | NO | base-rate (no market) | Low |
| 3 | Panama more SoT than Croatia in 2H? | 22% | 18% | NO | derived (each-half MostSoT parlay) | Low |
| 4 | Croatia score first goal of 2H? | 57% | 57% | YES | derived (2H goal-prob × CRO share) | Low |
| 5 | Croatia more cards than Panama? | 33% | — | NO | base-rate (no market) | Low |
| 6 | Panama score at least 1 goal? | 57% | 57% | YES | direct 2-way (Kalshi) | High |
| 7 | 9+ total corner kicks? | 53% | 54% | YES | direct 2-way (Kalshi + FD) | High |
| 8 | Panama have 3+ shots on target? | 63% | 63% | YES | ladder fit (λ=3.25) | Medium |
| 9 | José Fajardo 1+ SoT? | 57% | 57% | YES | ladder fit (λ=0.85) — PENDING XI | Medium\* |
| 10 | Luka Sučić 1+ SoT? | 59% | 59% | YES | ladder fit (λ=0.90) — PENDING XI | Medium\* |

\* Medium if confirmed starting.

## Derivations

**Q1** No foul market. `underdog_more_fouls = 0.56` (Panama underdog) → 56% YES. Low.

**Q2** No offside market. `offside_2plus` underdog = 0.40. Panama defending deep
draws fewer offsides than it commits; hold at base → 40%. Low.

**Q3** No direct 2H-SoT comparison market.
- Full-match "Most SoT" 3-way de-vig: PAN 11.0 / Draw 7.8 / CRO 81.2.
- "Most SoT in each half" parlay: PAN +3300 (2.9%), CRO −120 (54.5%), tie ~42.5%.
  iid-half q = √0.545 ≈ 73.9% = P(CRO wins a single half). P(PAN ≥ CRO 2H) ≈ 26%,
  less single-half ties (~10pt) → raw ≈ 16–18%.
- Comparison markets are +correlated and we've **twice overstated the favorite**
  on this question type (ARG-AUT Austria: we 20, crowd 30, hit YES). Shrink
  underdog up → our 22%, crowd (raw) 18%. Pick NO. Low.

**Q4** No direct market. P(≥1 goal in 2H) from 2H total bands (0 +370 → de-vig
P(0)=19.8%) = 80.2%. Croatia 2H goal share from 1H team-goal de-vig (λ_CRO_1H≈1.00,
λ_PAN_1H≈0.39, ×1.1 for 2H) = 71.6%. → 0.802 × 0.716 = 57.5% YES. Low (multi-input).

**Q5** No card data. Inverse foul lean: Panama (weaker/defending) fouls more →
more cards; favorites carded less. P(CRO more) ≈ 1 − 0.56 − ties ≈ 33% (NO). Low.

**Q6** Kalshi "0.5 goals" Yes 58 / No 43 (Panama team-goals; magnitude rules out
total). Hold 1.0%, de-vig → 57.4% YES. High.

**Q7** FD Over 8 (−155) / Under 9 (+100), hold 10.8% → P(9+) 54.9% (OR 55.5).
Kalshi 9+ 53/48, hold 1.0% → 52.5%. Kalshi-weighted → our 53%, crowd ~54%. YES.
High. Bake-off (FD): prop 54.9 / OR 55.5 / shin 55.4 / additive 55.4 (logged).

**Q8** FD one-sided Panama SoT ladder (3+ −165 … 9+ +7000). Poisson fit λ=3.25,
P(3+) = 63.0% (raw 3+ = 62.3%, coherent). → 63% YES. Medium.

**Q9** DK Fajardo SoT 1+ −135 / 2+ +380 / 3+ +1600. Poisson fit λ=0.85,
P(1+) = 57.3% (raw 1+ 57.4%, fit tracks all rungs). → 57% YES, Medium if starting.

**Q10** DK Luka Sučić SoT 1+ −145 / 2+ +350 / 3+ +1400. Poisson fit λ=0.90,
P(1+) = 59.3%. (Distinct from *Petar* Sučić in the FD list.) → 59% YES, Medium if starting.

## Q9/Q10 lineup decision tree
1. **Starting, odds unchanged** → use 57% / 59% as-is. Medium.
2. **Starting, odds moved** → re-fit: `american_to_prob` →
   `fit_poisson_mean_from_ladder([1,2,3],[p1,p2,p3])` → `_pois_sf(1,λ)` (compute.py).
3. **Not confirmed starting (default pre-game)** → cannot distinguish "out of squad"
   from "benched" before kickoff. Conservative default: `P_start × (25/90)`.
   Fajardo ≈ 16%, Sučić ≈ 16%. Low. (Edge case — normal flow is path 1.)

## Sources
Kalshi: Panama 0.5 goals 58/43; corners 8+ 65/36, 9+ 53/48, 10+ 42/59.
FanDuel: Match/Team SoT ladders; Most SoT full (PAN +750/Draw +1100/CRO −650) &
each-half (PAN +3300/CRO −120); corners (Over 8 −155/Under 9 +100); 2H goal bands
(0 +370/1-4 −475/5+ +2700); CRO 1H goals (No +140/=1 +130/2+ +260); PAN 1H goals
(No −280/=1 +240/2+ +1500); Half-with-Most-Goals 2H +108.
DraftKings: Fajardo 1+ −135/2+ +380/3+ +1600; L. Sučić 1+ −145/2+ +350/3+ +1400.
