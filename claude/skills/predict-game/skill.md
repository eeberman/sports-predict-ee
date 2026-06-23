---
name: predict-game
description: >
  Predict an upcoming game's SportsPredict question set (typically 10 questions)
  by de-vigging real betting markets, and track results over time. Use whenever
  the user wants to "run the next game", "predict this match", "score these
  questions", names an upcoming match for prediction, or pastes a slate of
  yes/no + comparison questions. Also use when the user pastes a game's SETTLED
  outcomes for upkeep — that triggers settlement mode. Drives a 4-step
  interactive flow: (1) auto-fetch the questions and call which ones a market
  probably exists for, (2) wait for the user to paste markets (opt-in odds
  auto-pull), (3) de-vig to fair probabilities, score, log, and write a
  worksheet, (4) discuss / grill. Market de-vigging is the core method — do NOT
  fall back to a generic non-market model unless explicitly asked.
---

# predict-game

Predict a game's question set by de-vigging the betting markets that match each
question. The de-vigged crowd is the strongest estimator available; the edge is
clean de-vig hygiene plus, occasionally, question-specific evidence — never a
separate forecasting engine.

**Interactive, stateful, 4-step flow.** Do one step, then stop and wait for the
user. Don't run ahead. A separate **settlement mode** (below) handles pasted
results.

Repo this skill is welded to: `sports-predict-ee/`. Canonical code:
`forecasting/compute.py` (de-vig math), `forecasting/results_log.py` (logging),
`sportspredict_inventory/normalize.py` (`normalize_market`),
`provider_probe/clients/sportspredict.py` (`_tool`, question fetch). Read these
from the repo first; if an import/path fails, fall back to the formulas in
`references/devig.md` and tell the user the repo path broke. **Logging failures
must be surfaced loudly** — a silently dropped row corrupts the calibration set.

---

## Step 1 — Auto-fetch questions + market-existence call

Fetch the question set automatically. **Step 1 calls SportsPredict only — never
the odds API.** Use the question-fetch half of the existing pipeline
(`get_next_game.py` / `worksheet.py`): `_tool` → `list_events` → `list_lobbies`
→ `list_matches` → `list_markets` for the next upcoming match (or the match the
user named).

- If the user named a specific game, fetch that one; otherwise take the next
  upcoming.
- **Fallback:** if the SportsPredict fetch errors or returns nothing, ask the
  user to paste the questions. Don't invent the official questions.

Run each question through `normalize_market` to get its `question_family` /
`subtype`, then emit one table. The only added feature here is the
market-existence call, so the user knows where to spend odds-hunting effort:

```
| # | Question | Market likely? | Market type to look for |
```

- **Market likely?** — `Yes` / `Maybe (derive)` / `Unlikely`. Default this
  **deterministically from the family** using `references/market-existence.md`.
  Only override with Claude judgment where the family genuinely can't decide —
  above all **star vs. role player** props (same family, opposite availability)
  and exotic combos. Don't burn judgment on rows the table already settles.
- **Market type to look for** — the specific line to search for, not a category.
  Derive it mechanically from `normalize_market`'s `threshold_value`:
  - Threshold questions ("N or more"): target line is **O/U (N−0.5)**.
    E.g. "9 or more corners" → `Total corners O/U 8.5`; "6+ SoT" → `Team SoT O/U 5.5`.
  - Comparison questions ("X more than Y"): name the direct comparison market
    (e.g. `Most corners 3-way`, `2H moneyline`) or the two component ladders.
  - Binary yes/no without threshold: name the exact prop (e.g. `BTTS yes/no`,
    `Anytime goalscorer`, `Penalty yes/no`).
  For `Maybe (derive)`, name each *component* market to find, not just the family.

**Player market absence ≠ benched.** If a player prop doesn't appear in an
initial scan, flag it as **"lineup unconfirmed"** — do NOT silently assign a
bench base rate. Ask the user to check a second source (FD anytime goalscorer
list, action network, etc.) before treating absence as benched. A missing FD
line could be a display filter, a different market name, or the player simply
playing a different role. Only apply bench base rate after explicit lineup
confirmation (e.g. official team sheet or user confirms no market exists
anywhere).

Then stop. Ask the user to paste whatever markets they can find.

---

## Step 2 — Markets (manual-first, opt-in auto-pull)

The user pastes odds they found (any format: American, decimal, cents/%,
ladders). Then:

1. Parse each market, map it to a question number.
2. Echo a confirmation table: question #, market found, raw implied probs, and
   **hold** (overround). Flag every question with no market yet.
3. Tag each as **direct** (one market answers it) or **derived** (must combine
   markets). Derived is where blow-ups happen — surface it now.
4. For the still-missing **"market likely"** questions only, *offer*: "want me
   to pull odds-API anchors for the gaps?" Call `the_odds_api` **only if the
   user says yes**, and only for those gap questions — never spray the API
   across covered or untradeable rows. (User is watchful about call burn.)

Then stop and let the user confirm or add more.

---

## Step 3 — De-vig, score, log, worksheet

De-vig each market and answer each question. Use `compute.py`
(`devig_method`, `devig_two_way`, `devig_three_way`, `fit_poisson_mean_from_ladder`,
`_pois_sf`, `poisson_p_a_greater_b`); math + hygiene in `references/devig.md` —
read it before scoring.

**De-vig method.** Default is **odds-ratio** (`devig_method(raw)` /
`devig_odds_ratio`), not proportional, for any market with hold > ~5%. It strips
more vig from the longshot leg (favorite-longshot correction). Proportional and
the near-vig-free Kalshi 3-ways agree to <0.1pt anyway. One-sided ladders (`X+`
only) have no booksum to redistribute → method N/A, Poisson fit stands. This
default is a **tracked hypothesis**: see the bake-off persist step below.

**Deviation rule (important).** Default `our_prob = crowd_prob` (the de-vigged
market). Only move off the market with **direct, question-specific evidence** (a
sharper market disagreeing, a concrete lineup/availability fact). **Never apply
blind favorite/over-bias leans** — generic deviations are noise. Every time
`our_prob ≠ crowd_prob`, state the specific reason; that's what makes the logged
divergence learnable.

**Derived vs un-derivable.** If market data *can* reach the answer, derive it,
**walk through every step** in the worksheet, and mark it indirect. If no market
data can reach it, fall back to the calibrated base rate from
`outputs/base_rate_priors.csv` — **clearly labeled "base-rate, no market", Low
confidence, visually quarantined** from de-vigged numbers. Never let a base-rate
number share a lane with a market number.

**Market-first ordering.** Score all market-backed questions first (direct and
derived). Only after those are fully done, sweep the remaining no-market questions
and assign base rates as a final pass. If a "Market likely? Yes" question still
has no market partway through Step 3, offer the user one last chance to paste it
before falling back — don't silently assign a base rate mid-session.

**Confidence (rule-based, not a vibe):**
- **High** — direct de-vig of a normal-hold two-/three-way market.
- **Medium** — direct but one-sided/thin (had to assume the vig), or a
  single-input derivation.
- **Low** — multi-input derivation, or base-rate fallback.

Emit the final table:

```
| # | Question | Fair prob (our) | Crowd (de-vig) | Pick | Method | Confidence |
```

Method is honest: `direct 2-way`, `direct 3-way`, `ladder fit`,
`derived (steps→)`, `base-rate (no market)`.

**Then persist three things:**
1. **Log** every question via `results_log.append` — `our_prob`, `crowd_prob`
   (raw de-vig, before any evidence-based lean), match, date, `status=open`,
   empty `outcome`. Both columns always, so later you can measure whether your
   leans beat the raw market. If the write fails, say so loudly.
2. **De-vig bake-off** — for every question answered off a real multi-way market
   (margin > ~2%), log all four methods' YES prob via
   `forecasting.devig_bakeoff.append` (`devig_all_methods` gives them).
   `python -m forecasting.devig_bakeoff --summary` Brier-scores them once
   outcomes settle — this is how the odds-ratio default gets re-evaluated. Skip
   base-rate and one-sided-ladder rows (methods coincide). Surface write failures.
3. **Worksheet** — write `outputs/worksheets/<match>.md` (align with the repo's
   `worksheet.py` convention): the questions, markets pasted, **the de-vig steps
   for every derived question**, and the final table. This is the process record
   for post-mortems when a derived call resolves badly.

Then stop.

## Step 4 — Discuss / grill

Offer to talk through the numbers. To pressure-test the *method* (not just this
game), invoke the `grill-me` skill.

**Keep worksheet and log in sync.** If a `our_prob` changes during Step 4
discussion (new market found, lineup corrected, derivation error caught), update
both immediately — patch the worksheet derivation section and update the
`results_log.csv` row at the same time. Don't let the worksheet go stale.
If `crowd_prob` also changes, update that column too. A stale worksheet poisons
post-mortems; a stale log corrupts the Brier calibration.

---

## Settlement mode (post-game upkeep)

Trigger when the user pastes **outcomes** for a game already predicted
(e.g. "Q3 YES, Q5 NO, ..."), not questions or markets. Then:

1. Match rows in `results_log.csv` by game + question.
2. Set `outcome` (YES/NO), `status=settled`.
3. If the user pasted the **contest RBP**, store it as-is in the `rbp` column.
   **Do not compute RBP** — that's the contest's number.
4. **Also settle `devig_bakeoff.csv`** — set `outcome`/`status=settled` on the
   matching bake-off rows for that game, so the method comparison accrues data.
5. Print the running **Brier of our_prob vs crowd_prob** (via
   `results_log --summary` logic) AND the de-vig method bake-off
   (`python -m forecasting.devig_bakeoff --summary`). The first is the
   leans-vs-market signal; the second is whether odds-ratio is still the right
   default. Don't switch the default on a thin sample.

---

## Carry-over methodology (don't relearn each game)

- Direct single-market de-vig is the workhorse; it beat the crowd across every
  ARG-AUT question. Derived combos need assumptions and are the failure mode.
- Comparison "who does more" markets (corners, SoT) are positively correlated
  within a match; independent-Poisson on two team ladders overstates the
  favorite — shrink toward the crowd, or use a direct "most X" 3-way. See
  `references/devig.md`.
- The fav/over-bias finding is real but unsettled as a *rule* — it's currently
  NOT applied (evidence-only deviation). Whether pure de-vig, blind leans, or
  evidence-only wins is an open question to be settled by the logged
  Brier-vs-crowd data, not assumed.
- **Ladder Poisson fit — log both λ estimates when a two-sided anchor exists.**
  Fitting Poisson to raw one-sided ladder probs recovers approximately the correct
  λ under uniform hold (hold cancels in rung ratios). The real bias is non-uniform
  hold: books apply more juice to outer/longshot rungs, which pulls the fitted λ
  slightly high. To calibrate this over time: whenever you have *both* a two-sided
  market (e.g. Team SoT O/U N.5) AND a one-sided ladder for the same team/stat,
  note both λ estimates in the worksheet note — `λ_twoway=X, λ_ladder=Y`. Once
  enough pairs accumulate, the typical divergence becomes the correction factor.
  Until then, use the ladder fit as-is and treat the λ as having ~+0.2 upward bias
  on the outer rungs.

- **No game-state tempering.** `temper_2h_dominance` in `compute.py` is NOT
  applied. The intent (dominant teams ease off in 2H) is real, but the shrink
  constant `GAME_STATE_SHRINK=0.55` was calibrated on a single match (ESP-KSA)
  and is not reliable. Use the raw Poisson comparison probability. If a 2H
  comparison market exists (e.g. FD "each-half" prop or a 2H moneyline), use
  that as a cross-check floor instead. See `reports/modeling_plan.md` for the
  backlog item to calibrate this properly.
