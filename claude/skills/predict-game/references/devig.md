# De-vig math + hygiene (Step 3)

Canonical implementation: `sports-predict-ee/forecasting/compute.py`. Prefer
calling those functions over re-deriving. Summary below so the skill is
self-contained.

## Convert odds to raw implied probability

- American: `+o → 100/(o+100)`; `-o → o/(o+100)`.
- Decimal: `1/dec`.
- Cents / percent: `cents/100`.

Raw probs include the vig, so they sum to >1. The excess is the **hold**
(overround): `hold = sum(raw) - 1`.

## De-vig — method matters, and it's a tracked bake-off

A de-vig method decides **how to attribute the overround across legs**. Four are
implemented in `compute.py` (`devig_method(raw, method=...)`):

- **proportional** — `fair_i = raw_i / Σraw`. Splits margin in proportion to each
  leg. Simple, but leaves longshots too high / favorites too low when the book
  loads extra margin onto the longshot (favorite-longshot bias).
- **odds_ratio** (Cheung/Buchdahl) — one constant `c` divides every leg's
  odds-ratio; solve `c` so probs sum to 1. Pure curve-fit, no bettor model.
  **This is the current chosen default for hold > ~5%.**
- **shin** — attributes margin to adverse selection from sharp money
  (longshot-heavy); one parameter `z`. The 'insider' is a modeling device for
  sharps, **not** an assumption of fixed games.
- **additive** — subtract `margin/n` from each leg. Crude bracket; can clamp
  extreme longshots. Use only as a sanity bound.

odds_ratio / shin / additive all push the **longshot down, favorite up** vs
proportional — gently (OR) to aggressively (additive). On near-vig-free markets
(low-hold Kalshi 3-ways) all four agree to <0.1pt, so method is irrelevant there;
it only bites on fat-hold soft-book legs (FanDuel half-goals, SoT/corner ladders).

Two-way: `[raw_yes, raw_no]`. Three-way (1X2, half-with-most-goals): all 3 legs.

**This choice is a tracked hypothesis, not settled.** For every question answered
off a real multi-way market, log all four methods' YES probability via
`forecasting.devig_bakeoff.append`, then `python -m forecasting.devig_bakeoff
--summary` Brier-scores them head-to-head once outcomes settle. Keep odds_ratio
as default until the settled sample says otherwise — don't switch on a few rows.

## One-sided / thin markets

If only one side is quoted (common on player props and "yes only" specials),
you can't normalize. Estimate the missing vig: typical two-way hold ~4-8%,
player-prop hold ~6-10%. Shave roughly half the hold off the raw quoted side
and mark **Low confidence**. Always state the shave you applied.

## Ladders → Poisson (team SoT, corners, goals)

For a ladder of `N+` thresholds with prices, de-vig each rung where possible,
then fit a Poisson mean with `fit_poisson_mean_from_ladder(thresholds, probs)`.
Answer `P(X ≥ k)` with `_pois_sf(k, mu)`.

## Always pool across books when >1 book quotes the same market

**Default rule:** if two or more books quote the same market/ladder/prop, pool
them — never pick a single book. Pooling cuts book-specific noise and is the
better point estimate even when books disagree.

- **Ladders / props:** average the raw implied prob at each rung across books,
  then fit one Poisson to the pooled rungs. Equivalently, average the per-book
  fitted P (or λ) — all three routes agree to <0.2pt in practice.
- **Two-/three-way markets:** average each leg's raw implied prob across books
  first, then de-vig the consensus (this is already what the 1X2 consensus does).
- Record the single-book values in the note as the bracket (e.g. "pooled 0.42;
  FD 0.45 / BR 0.39"), so the spread is visible for post-mortems.
- One book is fine when only one quotes it — just flag it as single-book (lower
  confidence) so the next pull knows to hunt a second source.

## Comparison "who does more" questions — derive, don't lean

For "Home more corners/SoT than Away" there is usually **no market** for the
head-to-head, so it must be derived: fit a Poisson mean to each team's ladder,
then `poisson_p_a_greater_b(mu_a, mu_b)` (independent). That independence step is
an assumption you can't see, so the number is **Low confidence** — but do **not**
bolt on a directional "shrink the favorite toward 50" correction. An earlier
version of this note did, citing "corners are +correlated → independence
overstates the favorite." **That rationale was backwards:** positive inter-team
correlation *lowers* the variance of the difference, which pushes the *underdog
down*, not up. The true sign of the dependence is ambiguous and small, and the
only supporting miss was n=1 (ARG-AUT). So there is no justified blind shrink.

How to handle it, in order of preference:
1. Use a **direct/semi-direct** comparison market if one exists — a "most
   corners / most SoT" 3-way (home / away / tie), or a per-half "most X in each
   half" line worked down to the half. De-vig it; it needs no copula assumption
   and is the best anchor.
2. If only separate team ladders exist, report the independent-Poisson number
   as-is at **Low confidence**. Log it (and any comparison-market anchor) so the
   settled data, not a hunch, tells us whether a correction is ever warranted.

See `corner-comparison-independence-trap` memory for the full correction.

## Derived combos (BTTS+Over, half-splits, 2H-scoring)

When you build an answer from multiple markets you are injecting assumptions
(correlation, half-share splits, the missing side's vig). State each assumption
in the Method column. A clean direct market always trumps a derived combo —
hunt for the direct market first.

## Picking a side / deviating from the market

Default: `our_prob = crowd_prob` and the pick follows the de-vigged number. Only
move off the market with **direct, question-specific evidence** — a sharper
market that disagrees, or a concrete lineup/availability/team fact for *this*
question. State the reason whenever you deviate.

**Do NOT apply blind favorite-bias or over-bias leans.** The crowd's fav/over
bias is a real finding, but as a blanket "fade every favorite / every Over" rule
it is a *generic* deviation, and generic deviations have tested as noise. Treat
that finding as a hypothesis about *which market to trust when two disagree*, not
a license to shade every coin-flip. Whether pure de-vig, blind leans, or this
evidence-only rule actually wins is an open question to be settled by the logged
Brier-vs-crowd data — until then, evidence-only is the default.
