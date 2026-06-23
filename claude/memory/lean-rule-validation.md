---
name: lean-rule-validation
description: "Open research question — does data validate pure de-vig (A), blind fav/over-bias leans (B), or a new lean rule?"
metadata: 
  node_type: memory
  type: project
  originSessionId: ed99ff8f-c7ec-45cf-99ae-566cad463235
---

Open research track (flagged 2026-06-22): empirically test which deviation rule
wins for the [[predict-game]] skill, using the logged `our_prob` vs
`crowd_prob` vs outcome Brier data.

- **Rule A** — `our_prob = crowd_prob` always (pure de-vig, never deviate).
- **Rule B** — apply blind favorite-bias / over-bias leans near coin-flips
  (see [[market-devig-methodology]]).
- **New rule** — deviate only on direct question-specific evidence, or some
  other learned rule.

**Current decision:** the skill ships with the conservative rule — deviate from
the de-vigged market ONLY on direct question-specific evidence, never on generic
bias (per [[deviation-evidence-strength-rule]]). This is a deliberate baseline,
NOT a final answer.

**Why:** [[market-devig-methodology]] says fav/over-bias is the edge, but
[[deviation-evidence-strength-rule]] says generic deviations are noise — these
conflict. Only out-of-sample Brier-vs-crowd data can settle it.

**How to apply:** as `results_log.csv` fills, compare Brier of (a) pure de-vig,
(b) simulated blind leans, (c) the evidence-only rule actually used. Promote
whichever wins. Until then, default to evidence-only.
