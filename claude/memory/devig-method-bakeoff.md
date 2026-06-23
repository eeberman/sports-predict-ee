---
name: devig-method-bakeoff
description: de-vig default is now odds-ratio (not proportional) for hold>~5%; all 4 methods logged per market to devig_bakeoff.csv to re-eval the choice on settled Brier
metadata: 
  node_type: memory
  type: project
  originSessionId: f2a147ad-70d4-4778-ba02-b67b91fa47a4
---

**Decision (2026-06-22, FRA vs IRQ session):** the de-vig method is now a tracked
bake-off, not a fixed choice. **odds-ratio is the chosen default** for any market
with hold > ~5%; proportional stays fine for near-vig-free markets (low-hold
Kalshi 3-ways, where all methods agree to <0.1pt).

**Why off proportional:** proportional splits the overround in proportion to each
leg, which overstates longshots / understates favorites when the book loads extra
margin onto the longshot (favorite-longshot bias). odds-ratio, shin, and additive
all strip more margin from the longshot. We picked **odds-ratio** because it's a
pure curve-fit (one constant `c` on the odds-ratio) with no bettor-behavior story
to defend — the user explicitly rejected Shin's literal "insider who knows the
result" framing (no assumption of fixed games). Shin is fine *reframed* as sharp
adverse-selection, but odds-ratio sidesteps the argument. See [[market-devig-methodology]].

**Code:** `forecasting/compute.py` — `devig_method(raw, method=...)`,
`devig_odds_ratio`, `devig_shin`, `devig_additive`, `devig_all_methods`,
`DEFAULT_DEVIG_METHOD="odds_ratio"`. Bake-off logger:
`forecasting/devig_bakeoff.py` → `outputs/results/devig_bakeoff.csv` (logs YES
prob under all 4 methods + outcome slot); `python -m forecasting.devig_bakeoff
--summary` Brier-scores them head-to-head once rows settle.

**Governance:** keep odds-ratio as default until the *settled* bake-off sample
says otherwise — do NOT switch on a handful of rows. The chosen method is a
hypothesis to be beaten by data, same spirit as [[lean-rule-validation]].

**Scope / what doesn't move:** method only matters on fat-hold multi-way markets.
One-sided ladders (`X+` only, no paired under) have no booksum to redistribute →
method N/A, Poisson fit stands. On FRA-IRQ only Q9 (France score 1H 79→80) and Q7
(Iraq score 2H 19→20) moved under odds-ratio; Q6 was method-invariant.
