# Memory index

- [Non-market backtest findings](nonmarket-backtest-findings.md) — engine adds zero edge; priors biased hot (cards/corners/pen) and cold (offside); quote calibrated base rate
- [Deviation ∝ evidence strength rule](deviation-evidence-strength-rule.md) — only deviate from base rate with direct team/market data; generic engine deviations are noise
- [Resolution backtest findings](resolution-backtest-findings.md) — shrunk team rates add real edge on comparison (who-does-more) questions, none on threshold (total≥N); opponent-against best for totals
- [Extended-pool API-Football findings](extended-pool-apifootball-findings.md) — built WC2026 team-backfill pipeline (→R2); free-tier stats Europe-only (Iraq/Jordan empty), national-team form opponent-quality-biased & unvalidated → do NOT deviate on it; fixed comparison-direction + home_team-injection bugs
- [R2 & API-Football gotchas](r2-and-apifootball-gotchas.md) — R2 creds in ROOT .env (load_env_file('../.env')); API-Football free tier: no last param, seasons 2022-2024, 10 req/min, Europe-only stats
- [Working style](working-style.md) — pressure-test scope before building; blunt feasibility verdicts over optimistic delivery; market-first / edge-vs-crowd thinking
- [Corner-comparison independence trap](corner-comparison-independence-trap.md) — no market prices the corner h2h; anchor on the most relevant comparison market, NOT a blind shrink (old +correlation 'shrink favorite' rationale was backwards; n=1 evidence)
- [Multi-API auto-pull next step](multi-api-autopull-next-step.md) — planned: auto-pull markets from multiple APIs to feed predict-game Step 2 (currently manual-paste-first)
- [Non-market prediction buildout](nonmarket-prediction-buildout.md) — planned: real non-market estimator beyond base-rate fallback; must stay quarantined from market numbers
- [Lean-rule validation](lean-rule-validation.md) — open: test pure de-vig (A) vs blind bias-leans (B) vs evidence-only (current default) on logged Brier-vs-crowd data
- [Market de-vig methodology](market-devig-methodology.md) — direct single-market de-vig is the reliable workhorse (beat crowd on all of ARG-AUT); derived multi-market combos need assumptions & are where blow-ups happen; crowd fav-bias + over-bias are the edge; de-vig hygiene + source hierarchy
- [De-vig method bake-off](devig-method-bakeoff.md) — default de-vig is now odds-ratio (not proportional) for hold>~5%; all 4 methods logged per market to devig_bakeoff.csv; re-eval choice on settled Brier
