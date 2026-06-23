---
name: r2-and-apifootball-gotchas
description: "Operational gotchas: R2 creds live in the ROOT .env (must load_env_file('../.env')); API-Football free tier limits (no last param, seasons 2022-2024, 10 req/min, Europe-only stats)"
metadata: 
  node_type: memory
  type: reference
  originSessionId: a01f7e9d-786d-43bd-8c7b-8a196a29800a
---

Hard-won setup details for this repo (cost real time to rediscover). See [[extended-pool-apifootball-findings]].

**R2 credentials live in the REPO-ROOT `.env`, not `sports-predict-ee/.env`.**
- `raw_landing/config.py` auto-loads `sports-predict-ee/.env` (which only has `.env.example`), so R2 vars come up MISSING by default.
- Fix in any script that uploads: `config.load_env_file(config.PROJECT_ROOT.parent / '.env')` (PROJECT_ROOT = sports-predict-ee). Then `r2.test_roundtrip()` works. Bucket = `sports-predict`.
- `provider_probe` already finds `FOOTBALL_DATA_API_KEY` without this; only the R2 path needs the explicit load.
- Also note: `outputs/backtest_features.csv` and the `backtest_*.py` scripts live at REPO ROOT (`sports_predict/outputs/`), NOT under `sports-predict-ee/`. `team_loo_rates` reads from there (now prefers `outputs/team_features_extended.csv`).

**API-Football (api-sports.io) FREE tier limits — design fetchers around these:**
- The `last` / `next` params are PAID-only (return `errors.plan`, 0 results, don't count against quota). Use `?team=ID&season=YYYY` and filter/sort client-side (`recent_finished()`).
- Seasons restricted to **2022–2024** only (2021/2025 blocked). Season 2024 spans into late 2025 for European national teams, so recency is fine.
- Rate limit **10 req/min** → throttle ~7s/call (`THROTTLE=6` + client's 1s sleep) and retry 429 with a 65s cooldown (added to `api_football._get`).
- `/status` does NOT count against the daily 100 quota — safe to poll for the budget guard.
- **Statistics coverage is Europe-only on free tier**: AFC/CAF fixtures (Iraq, Jordan, Algeria…) return empty `/fixtures/statistics`. Don't expect non-European minnow coverage.
