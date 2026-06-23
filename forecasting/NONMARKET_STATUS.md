# Non-market forecasting — status & next steps

**Status (2026-06-22): NOT production-ready for questions without a betting market.**

"Non-market" questions are the SportsPredict prop questions that have no sportsbook
counterpart (who-has-more corners / SoT / fouls, offsides ≥N, 2H-vs-1H, etc.). Predicting
these requires per-team historical stats. Today we cannot do this reliably. Three gaps,
in order of severity:

### 1. Coverage gap — we don't have data for most teams
- The validated team-rate pool is StatsBomb WC 2018+2022 only: **29 usable teams** (≥4 games)
  out of the **48-team** 2026 field. 24 teams were missing.
- The backfill source (API-Football free tier) has **Europe-only statistics coverage**:
  Austria/Norway came back with 8 usable games each, but **Iraq, Jordan, Algeria returned
  empty statistics** (AFC/CAF qualifiers aren't covered on the free plan). The free plan also
  blocks the `last` param and restricts to seasons 2022–2024.

### 2. Data-quality gap — the data we do have isn't clean
- API-Football national-team form is **opponent-quality-biased**. Austria's 2H-SoT mean came
  out *above* Argentina's because Austria's sample includes San Marino/Cyprus thrashings while
  Argentina's are WC-vs-elite. Raw means are **not comparable across sources or opponent pools**.
- The per-source re-backtest (`outputs/backtest_resolution_bysource.py`) could not even **score**
  the API-Football matches — their opponents lack ≥4 games — so the source is **unvalidated**,
  not just noisy. StatsBomb's own edge still reproduces (fouls +0.021, 2H corners +0.027).

### 3. Modeling gap — single-stat shrunk rates don't transfer
- The validated method (shrunk LOO rate → `poisson_p_a_greater_b`) only works inside a
  **homogeneous-opponent pool** (StatsBomb WC, everyone plays everyone strong). It has no notion
  of opponent strength, home/away, or competition tier, so it breaks on heterogeneous
  national-team form.

## What *does* work today
- Any question with a **real betting market**: de-vig the market. **This is the only repeatable
  edge** — sharp lines vs a softer crowd. Concentrate risk here.
- Matches between two **StatsBomb-pool** teams: comparison questions carry a small validated edge.

## Why base rates are a floor, not a strategy
Scoring is RBP (relative to the crowd), so a forecast only earns when it beats the crowd *and*
the crowd is wrong. Base rates are **public information the crowd also has**:
- Against a calibrated crowd, base rate ≈ crowd → ~0 RBP (a tie; you can't win by tying).
- Against a naive crowd (anchors at 50%, round numbers), the calibrated base rate is a thin edge —
  but that's betting on *crowd error*, not on knowing something.

So base rates are a **risk-minimizer**, not an edge. We use them only because our biased engine
deviations are *worse* (they caused the −16 / −33 disasters). The honest implication: until a real
non-market edge source exists, **don't spend risk on non-market questions** — play the markets and
treat non-market props as skip/floor, not as tradeable. (See memory `nonmarket-backtest-findings`,
`deviation-evidence-strength-rule`.)

## Next steps / future improvements (in priority order)
1. **Opponent-strength adjustment.** Replace raw team means with opponent-adjusted rates
   (Elo/strength-normalized, or the for-rate + opponent-against matchup signal) so cross-source
   and minnow-padded samples become comparable. This is the single biggest unlock.
2. **Better data source / coverage.** The free API-Football tier is Europe-only; a paid tier (or
   FBref / Sofascore, the latter needing a browser-capable context — currently Cloudflare-blocked)
   would give global coverage and true 1H/2H splits instead of StatsBomb-proxied 2H.
3. **Proper feature-selected model.** Move from single-stat Poisson to a regression with opponent
   strength, venue, competition tier, and rest as features — and select features against the
   resolution backtest rather than assuming a single rate.
4. **Re-validate per source.** Once enough teams are fetched that matchups have *both* sides
   covered, re-run `backtest_resolution_bysource.py`; only then can API-Football graduate from
   base-rate-only to a deviation source.

## Pipeline already in place (so the above is incremental, not from scratch)
- `forecasting/team_canon.py` — WC2026 roster vs usable pool, `missing_teams()`, `priority_teams()`
- `raw_landing/sources/api_football_natl.py` — national-team fetch → R2 (budget guard, 429 retry)
- `raw_landing/sources/sofascore.py` — flagged `sofascore_untested` (blocked from servers)
- `outputs/extract_natl_features.py` — merge → `team_features_extended.csv` (+source/proxied_2h) → R2
- `outputs/backtest_resolution_bysource.py` — the per-source validation gate
- `forecasting/team_loo_rates.py` reads the extended table and exposes `source_tag()` for provenance
