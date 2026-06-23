---
name: extended-pool-apifootball-findings
description: "Expanding the team-rate pool to WC2026 teams via API-Football: pipeline works but free-tier stats are Europe-only and national-team form is opponent-quality-biased — fails the validation gate, do not deviate on it"
metadata: 
  node_type: memory
  type: project
  originSessionId: a01f7e9d-786d-43bd-8c7b-8a196a29800a
---

Built a pipeline to backfill missing WC2026 teams into the team-rate pool (plan: API-Football + Sofascore → R2, merge, re-backtest). Outcome below. Extends [[resolution-backtest-findings]] and [[deviation-evidence-strength-rule]].

**Pipeline (all built, working end-to-end):**
- `forecasting/team_canon.py` — WC2026 roster (48) vs usable pool (29 ≥4 games) → 24 missing; `priority_teams()` puts today's teams first.
- `raw_landing/sources/api_football_natl.py` — lands national-team fixtures+stats+events to R2 (immutable keys, stable by fixture id for cross-run dedup). Free plan: **`last` param blocked, seasons 2022-2024 only, 10 req/min** → throttle 7s/call + 429-retry 65s cooldown.
- `outputs/extract_natl_features.py` — merges into 26-field schema + `source`/`proxied_2h` cols → `outputs/team_features_extended.csv` (engine reads this, falls back to backtest_features.csv) + uploads to R2. API-Football has no 2H SoT/corners → proxied via StatsBomb 2H-share (SoT .519, cor .511, card .632); card_2h real from events.
- `outputs/backtest_resolution_bysource.py` — re-backtest segmented by source.

**Two findings that kill naive use of the API-Football data:**
1. **Free-tier statistics are Europe-only.** Austria 8 games, Norway 8 (usable); but Iraq 1, Jordan 0, Algeria 1 — AFC/CAF matches return EMPTY statistics. So most non-European WC2026 minnows can't be covered on the free tier.
2. **National-team raw form is opponent-quality-biased → fails the validation gate.** Austria's 2H-SoT mean (3.34) came out ABOVE Argentina's (2.84) because Austria's games include San Marino/Cyprus thrashings while Argentina's are WC-vs-elite. The per-source re-backtest could not even SCORE api_football matches (their opponents lack ≥4 LOO games) → inconclusive. StatsBomb subset still reproduces the edge (fouls +0.021, 2H corners +0.027).

**Strategic conclusion (user-aligned):** base rates are a FLOOR, not an edge — scoring is RBP vs crowd, and base rates are public info the crowd also has (tie vs a calibrated crowd; thin edge only vs a naive one). We use them only because our biased deviations are worse (the −16/−33 disasters). So until a real non-market edge exists (opponent-adjusted team data, referee, or a market), **don't spend risk on non-market questions — concentrate on market-based trades** (de-vig sharp lines vs softer crowd = the only repeatable edge). Documented in `sports-predict-ee/forecasting/NONMARKET_STATUS.md`.

**How to apply:** Do NOT deviate on api_football team rates for comparison questions — they're opponent-contaminated and unvalidated. Keep them provenance-flagged (`statsbomb/api_football` shows in worksheet evidence) so a reviewer distrusts mixed-source rows. To make them usable would need opponent-strength adjustment (opponent-relative or Elo-normalized rates), not raw means. The market remains the best anchor where it exists (e.g. ARG-AUT "Team Most SoT" → Austria-more ≈ 18-23%, vs the contaminated team-data 50%).

**Also fixed (real bug, source-independent):** comparison handlers in `worksheet.py` returned P(home>away) regardless of which team the question named. Added `_subject_is_home(n)` (parses raw question for first-named team); now answers P(subject>other). Also fixed the long-standing `home_team`/`away_team` injection bug — `normalize_market` never echoed team names, so the team-rate path had NEVER fired before this.
