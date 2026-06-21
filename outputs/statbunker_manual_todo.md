# StatBunker Manual Todo — International Competition comp_ids

The following competition referee card tables are needed but their comp_ids
on StatBunker are not yet known. Find them manually:

1. Visit https://www.statbunker.com
2. Click the competition (e.g. 'FIFA World Cup 2026')
3. Look at the URL: `.../competitions/RefereeYellowCards?comp_id=NNN`
4. Add the comp_id to `provider_probe/clients/statbunker.py` COMP_IDS list
5. Re-run: `python -m raw_landing.cli pull-statbunker`

## Needed competitions

- FIFA World Cup 2026
- UEFA Euro (current cycle)
- Copa América (current cycle)
- AFCON (current cycle)

## Fields expected in each table

referee_name, matches, yellow_cards, red_yellow_cards, red_cards,
yellow_per_match, cards_per_match, home_cards, away_cards,
fh_cards_avg_minute, sh_cards_avg_minute

## R2 path pattern

`raw/statbunker/referee_cards/ingested_date=YYYY-MM-DD/run_id=.../`
