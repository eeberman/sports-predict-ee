# Raw Landing Report

**Generated:** 2026-06-21T12:47:29.046189+00:00
**Last run_id:** `97c4524a`
**Mode:** DRY-RUN

---

## Sources Attempted

- sportspredict
- football_data_co_uk (5 seasons)
- statsbomb_open_data (2 cycles)
- statbunker

## Quota-Limited Sources Excluded

- API-Football: excluded (no historical pulls in this task)
- The Odds API: excluded (no historical pulls in this task)

## Local Disk Usage

Raw data is stored in R2 only. Local files: `.env`, `raw_manifest.csv`, `outputs/logs/`.

## Next Recommended Step

1. Verify R2 bucket contents via Cloudflare dashboard
2. Add international StatBunker comp_ids (see `outputs/statbunker_manual_todo.md`)
3. Set up MotherDuck and begin processing layer (separate task)