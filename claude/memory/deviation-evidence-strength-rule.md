---
name: deviation-evidence-strength-rule
description: Core contest rule — deviate from the calibrated base rate only in proportion to evidence strength; generic engine deviations have zero resolution
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a01f7e9d-786d-43bd-8c7b-8a196a29800a
---

In the SportsPredict Probability Cup (Brier-scored, quadratic penalty), our wins are small market/team-data-grounded calls; our losses are big confident deviations on un-priced base-rate questions (ESP-KSA offside −16.47, BEL-IRN cards −33.44).

**Rule:** deviate from the calibrated base rate ONLY in proportion to the strength of the evidence.
- Market-priced question → de-vig and trust it.
- Direct team/player/referee data (a team's own multi-game record) → deviate confidently.
- Transferable base rate / archetype only → stay near the calibrated marginal; report the center of a wide distribution, not its favorable end.

**Why:** the Brier penalty is quadratic, so a few overconfident misses dwarf many small wins (12/15 beat-rate but net +0.05 RBP, worse Brier than crowd). And [[nonmarket-backtest-findings]] proved our generic engine's deviations (favorite-scaling) carry ZERO resolution — so any deviation must come from genuine external signal, never the engine itself.

**How to apply:** before submitting a non-market forecast that sits >~10 pts off the calibrated base rate, require a named, direct data source. If the only justification is an archetype/transferable rate, shrink back toward the base rate.
