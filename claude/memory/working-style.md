---
name: working-style
description: "How the user wants to work on sports_predict: pressure-test scope before building, blunt feasibility verdicts over optimistic delivery, market-first thinking"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a01f7e9d-786d-43bd-8c7b-8a196a29800a
---

Confirmed pattern over several sessions on the sports_predict forecasting project.

The user wants scope **pressure-tested before any build** — they invoke `/grill-me`, push back on vague scope, and narrow it themselves (e.g. "markets vs non-markets", "only today's teams", "give me a research prompt before building"). Don't jump to implementation; surface the hard scoping forks first.

**Why:** they're optimizing for not wasting effort on dead ends, and they reason like a trader — what's the actual edge, what does it cost.

**How to apply:** Lead with blunt feasibility verdicts, including "this doesn't work / isn't worth it," over optimistic delivery — they respond well to honest negative findings (accepted the api_football "fails validation" and "base rates are a floor not an edge" conclusions readily). Frame everything in terms of edge vs the crowd (RBP), market-first. When a build reveals the data/approach is bad, say so plainly and recommend stopping rather than shipping a weak result. See [[deviation-evidence-strength-rule]], [[extended-pool-apifootball-findings]].
