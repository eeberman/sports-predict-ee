---
name: multi-api-autopull-next-step
description: Planned next step — build auto-pull of odds/markets from multiple APIs for the predict-game flow
metadata: 
  node_type: memory
  type: project
  originSessionId: ed99ff8f-c7ec-45cf-99ae-566cad463235
---

A planned next step in the sports_predict project (decided 2026-06-22) is to
build out **automated market/odds auto-pull from multiple APIs**, not just
`the_odds_api`. This feeds Step 2 of the [[predict-game]] skill, whose Step 2 is
currently manual-paste-first with opt-in single-API auto-pull.

**Why:** manual market-gathering is the bottleneck; broader API coverage means
more questions get a direct market (vs error-prone derived combos, which are the
known failure mode — see [[market-devig-methodology]]).

**How to apply:** when this lands, upgrade predict-game Step 2 from
"manual-first, opt-in single-API" to multi-source auto-pull with the user
reviewing. Keep call-burn low (user is watchful about API calls); target only
the "market likely" questions still missing a market.
