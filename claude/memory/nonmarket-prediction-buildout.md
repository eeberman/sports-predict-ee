---
name: nonmarket-prediction-buildout
description: Planned direction — build out a proper non-market prediction setup as a parallel track to market de-vig
metadata: 
  node_type: memory
  type: project
  originSessionId: ed99ff8f-c7ec-45cf-99ae-566cad463235
---

A planned direction for the sports_predict project (flagged 2026-06-22) is to
**build out a non-market prediction setup** — a real model/estimator for
questions where no market exists or as an independent cross-check, beyond just
quoting calibrated base rates.

**Why:** the [[predict-game]] skill is market-de-vig-first; when no market can
answer a question it currently falls back to a clearly-labeled calibrated base
rate (see [[nonmarket-backtest-findings]]). The user wants a stronger non-market
capability than base-rate fallback.

**How to apply:** keep this strictly separate and clearly marked from
market-derived numbers (the existing finding is that the generic engine added
zero edge — see [[deviation-evidence-strength-rule]]). Any non-market output
must stay visually quarantined from de-vigged probabilities in predict-game.
