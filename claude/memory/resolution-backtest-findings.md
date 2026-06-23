---
name: resolution-backtest-findings
description: "Team-data resolution backtest — comparison (who-does-more) questions are exploitable with shrunk team rates; threshold (total≥N) questions are not; opponent-against signal best for totals"
metadata:
  node_type: memory
  type: project
  originSessionId: a01f7e9d-786d-43bd-8c7b-8a196a29800a
---

Follow-up to [[nonmarket-backtest-findings]]. `outputs/backtest_resolution.py` (same 128 WC matches, LOO team rates, shrink k=5, Murphy scoring) tested whether a team's OWN multi-game rate adds resolution. Metric validated: synthetic oracle res=0.25, pure noise res=0.01, LOO confirmed to exclude the scored match.

**Resolution now lifts off zero (backtest 1 couldn't — constants have res≡0 by construction). Where team data earns positive skill:**
- **Comparison / who-does-more questions are exploitable.** home_more_fouls +0.0171, home_more_2h_corners +0.0177, sot_2h_4plus +0.0062 — all EDGE. Built with `compute.poisson_p_a_greater_b(μ_A, μ_B)` on the two teams' shrunk LOO rates.
- **Threshold / will-total-clear-N questions are NOT.** total_sot≥8, corners≥10, cards_2h≥2, offside≥2 all stay NEUTRAL at best; a match-specific Poisson mean from team rates barely beats the single global mean (game-level variance dominates the total).

**Three rules this nails down:**
1. **Team data helps when the question is RELATIVE, not absolute.** Deviate on "team A vs team B"; quote the calibrated base rate on "total ≥ N".
2. **Always shrink; never use a raw team rate.** team-raw is NOISE in 5/8 families (6-game samples overfit); shrinkage pulls every one back to NEUTRAL/EDGE. Quantifies [[deviation-evidence-strength-rule]]. (~38/128 instances had <4 LOO games and fell back to base rate.)
3. **For totals, the opponent-against (matchup) signal beats team-for alone.** Adding the opponent's concession rate made sot_2h the strongest edge (+0.0103) and nudged cards/total-SoT positive. Build matchup mean = for-rate + opp-against-rate for threshold questions.

**Reconciliation:** the `engine` row shows EDGE on fouls/corners here while backtest 1 said res≈0 — not a contradiction. Backtest 1 scored those as a FLAT constant (zero resolution by construction though directionally right); letting the prediction vary per match with which side is the underdog recovers the latent resolution. The team's shrunk rate does it better and with no Elo dependency.
