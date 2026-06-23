---
name: market-devig-methodology
description: direct single-market de-vig is the reliable workhorse and beats the crowd; derived multi-market combos need assumptions and are where blow-ups happen
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 98c9b0c5-edfa-4705-9d91-a0ce02554442
---

Core methodology for the Probability Cup, validated on ARG vs AUT (2026-06-22): a pure single-market de-vig approach beat the crowd on every question it touched; the only loss was a derived/modeled one.

**Direct vs derived (the key split):**
- **Direct** = ONE market prices the exact question. De-vig and submit. Reliable. (ARG win ← h2h 3-way; ≤2 goals ← O/U 2.5 under; team 6+ SoT ← that team's SoT ladder; player 1+ SoT ← that prop.) On ARG-AUT all direct de-vigs beat or tied the crowd.
- **Derived** = NO single market prices it, so you combine 2+ markets, which requires an assumption. This is where blow-ups live. Combine only when the assumption is safe; otherwise shrink toward the crowd. See [[corner-comparison-independence-trap]].

**Valid derivation that worked — "team scores in 2H"** (no direct line): P(scores 2H) = P(scores match) − P(1H only), where P(1H only) = P(scores 1H) − P(scores both halves). All three legs de-vigged from that team's goal lines (match O/U 0.5, 1H O/U 0.5, "to score in both halves"). Beat crowd. Decomposition-by-complement is safe; independence on correlated counts is not.

**De-vig hygiene:**
- 2-way / 3-way proportional de-vig (normalize raw implied to sum 1). Report the hold.
- WIDE markets = noisier de-vig, trust less. The 3-way "Half with Most Goals" had 8.1% hold (vs 3.8% on h2h). Tight 2-way h2h/O-U are the most trustworthy.
- One-sided lines (yes-only props, e.g. -105) can't be truly de-vigged — shave ~5-6% est. hold and flag as estimate.
- For "team X+ of stat" ladders, fit a Poisson to the survival curve to read any threshold and smooth vig.

**Crowd biases to exploit (the actual edge — fade the CROWD vs the market, not the market):**
- Favorite-bias: crowd rounds the favorite UP on everything (win, dominance, SoT, score). Market already prices it; crowd double-counts.
- Over/action-bias: crowd leans over on goals (≤N-goals under is systematically underpriced by the crowd).

**Source hierarchy / freshness:** Pinnacle is sharpest (lowest hold) — de-vig against it over EU consensus when available. Closing line is the best predictor; wait toward KO. Player props are unbettable until LINEUPS (~1hr pre-KO): is the player starting, in what role.

**No-market questions** (offside, total cards, 2H-SoT head-to-head): per [[deviation-evidence-strength-rule]] and [[nonmarket-backtest-findings]] the engine adds no edge — usually skip. Two refinements proven on ARG-AUT: (1) do NOT submit a team-data *comparison* against the crowd with no market (our team-data said AUT 50% to win 2H SoT; crowd nailed 27% on a NO — good thing we skipped). (2) For total-CARDS questions the referee card-average is the one cheap, accessible signal worth using.
