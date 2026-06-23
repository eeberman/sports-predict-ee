---
name: nonmarket-backtest-findings
description: "Backtest proof that our non-market forecast engine adds zero edge and several priors are biased; quote the calibrated base rate, deviate only on real team/match data"
metadata: 
  node_type: memory
  type: project
  originSessionId: a01f7e9d-786d-43bd-8c7b-8a196a29800a
---

Backtest (128 StatsBomb WC 2018+2022 matches, `outputs/backtest_nonmarket.py`) replayed our live engine on the 9 non-market question families vs ground truth, scored as `skill = Brier(marginal) − Brier(ours)`.

**Result: NOT ONE family shows EDGE.** Every favorite-dependent family (more-2H-corners, more-fouls, halftime-lead) has resolution ≈ 0 — our Elo-driven `prior_with_favorite_scaling` does not discriminate. A constant predictor can't beat the marginal by construction, so the favorite-agnostic families can only break even or lose.

**Several seeded priors are miscalibrated (the root of the disasters):**
- penalty_or_red: ours 56% vs actual 40% (+16, worst, −0.026 skill)
- corners≥10: ours 52% vs actual 38% (+14)
- cards_2H≥2: ours 73% vs actual 64% (+9) — reproduces BEL-IRN cards −33.44 as a *systematic hot bias*
- total_SoT≥8: ours 61% vs 54% (+8); halftime-fav-lead: 53% vs 42% (+11)
- offside_2plus: ours 37% vs actual 45% (−8, runs COLD) — reproduces ESP-KSA offside −16.47 direction

**Real but small signals DO exist** in the directional base rates (favorite wins 2H corners 57%, underdog more fouls 62%, offside 45%) — exploitable vs a 50/50 crowd, but our engine extracts none as resolution.

**How to apply:** On non-market questions, quote the *calibrated empirical base rate*, NOT our hot priors and NOT favorite-scaling (it's noise). Deviate only with genuine team/match-specific data (a team's own multi-game record, a specific referee) — confirmed by [[deviation-evidence-strength-rule]]. The contest edge here is calibration-driven (don't be the hot/cold one), not prediction-driven. Limited 2026 evidence (ESP-KSA, BEL-IRN) agrees with the historical base rates over our adjusted priors. Caveat: Elo table is approximate, but the directional marginals are from actual outcomes and are solid.
