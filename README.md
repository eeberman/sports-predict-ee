# SportsPredict Probability Cup

Automated pipeline to research, fetch, and eventually predict SportsPredict Probability Cup
markets. **Does not auto-submit predictions** — all answers are confirmed manually.

---

## Project Status

### Phase 1 — Market Inventory ✓

Fetches all SP events/lobbies/matches/markets, normalises questions into ~30 reusable
templates, and categorises into 7 model families (scoreline, outcome, discipline, shots,
halftime, lineup, weather).

- Package: `sportspredict_inventory/`
- Outputs: `reports/question_taxonomy.md`, `reports/modeling_plan.md`

### Phase 2 — Provider Research ✓

Probed 6 data sources for free-tier availability. Key findings:

- **API-Football** — match stats, lineups, referee assignments
- **The Odds API** — betting odds + implied probabilities
- **StatBunker** — referee card rates by competition
- **Open-Meteo** — weather (free, no key needed)

- Package: `provider_probe/`
- Outputs: `outputs/provider_recommendations.md`, `outputs/provider_probe_matrix.csv`

### Phase 3 — Raw Data Landing ✓

Pulls 4 no-quota sources and uploads immutable snapshots to Cloudflare R2.

| Source | What | Volume |
|---|---|---|
| SportsPredict API | Live events/lobbies/matches/markets | ~4 JSON files |
| Football-Data.co.uk | Historical results CSVs | 55 files (5 seasons × 11 leagues) |
| StatsBomb Open Data | International match events + lineups | ~500 JSON files |
| StatBunker | Referee card tables (HTML) | 4 HTML files |

- Package: `raw_landing/`
- Storage: Cloudflare R2 bucket `sports-predict`
- Path pattern: `raw/{source}/{entity}/ingested_date=YYYY-MM-DD/run_id={id}/{filename}`

### Phase 4 — Processing Layer (TODO)

Transform R2 raw files into structured DuckDB/MotherDuck feature tables:
team form, h2h records, scoring rates, referee card rates, odds-implied probabilities.

### Phase 5 — Prediction Models (TODO)

One model per market family outputting a probability (0–1) per open market.
Model families and feature sets defined in `reports/modeling_plan.md`.

### Phase 6 — Answer System (TODO)

CLI to review model predictions for each open market, confirm or override, then log actual
results once SportsPredict announces them. Tracks accuracy over time.

Submission to SportsPredict is manual — the tool surfaces the number, the user enters it.

---

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your API keys (see .env.example for required vars)
```

---

## Usage

### Market Inventory

```bash
python -m sportspredict_inventory.fetch       # pull live markets from SP API
python -m sportspredict_inventory.categorize  # normalise + categorise
python -m sportspredict_inventory.report      # generate markdown reports
```

### Raw Data Landing

```bash
python -m raw_landing.cli check-config                 # verify all credentials
python -m raw_landing.cli test-r2                      # test Cloudflare R2 connection
python -m raw_landing.cli pull-all-no-quota --dry-run  # preview planned uploads
python -m raw_landing.cli pull-all-no-quota            # live pull → R2
```

Individual sources:

```bash
python -m raw_landing.cli pull-sportspredict
python -m raw_landing.cli pull-football-data [--seasons 5]
python -m raw_landing.cli pull-statsbomb [--cycles 2]
python -m raw_landing.cli pull-statbunker
```

### Repair Missing Non-SportsPredict Files

The repair command is read-only unless `--apply` is provided. It only targets missing
configured Football-Data and StatsBomb objects; it never calls SportsPredict or StatBunker.

```bash
python -m raw_landing.cli --env-file ../.env repair-non-sportspredict
python -m raw_landing.cli --env-file ../.env repair-non-sportspredict --apply
python -m raw_landing.cli --env-file ../.env reconcile-manifest
python audit_r2_raw_landing.py
```

### Provider Probes

```bash
python -m provider_probe.cli probe-all
python -m provider_probe.cli probe-referee-sources
```

---

## Non-market forecasting status

Questions without a betting market (who-has-more corners/SoT/fouls, offsides, 2H-vs-1H) are
**not production-ready** — see [forecasting/NONMARKET_STATUS.md](forecasting/NONMARKET_STATUS.md)
for the coverage / data-quality / modeling gaps and the next-step roadmap (opponent-strength
adjustment, broader data, feature-selected model).

---

## Security

- `.env` is gitignored and never committed
- No predictions are auto-submitted to SportsPredict under any circumstances
- R2 files are immutable — existing keys are never overwritten
- API keys are only printed as "present" / "MISSING", never their values
