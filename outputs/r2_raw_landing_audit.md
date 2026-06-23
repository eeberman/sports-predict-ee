# R2 Raw Landing Audit

**Generated:** 2026-06-21T14:58:54.400886+00:00
**R2 connection:** PASS (bucket `sports-predict` listed successfully; no object was uploaded)
**Overall completeness:** `sports_predict_deferred_non_sportspredict_complete`

## Executive summary

R2 is reachable and contains 454 objects (605,594,147 bytes) under the four audited source prefixes. 
All approved non-SportsPredict coverage is complete: Football-Data has 55/55 files, StatsBomb has events and lineups for all 193 indexed matches, and four configured StatBunker files are present. SportsPredict matches and markets remain explicitly deferred. 
The discovered local manifest has 454 rows and indexes all audited source objects; 0 bucket objects lack manifest rows.

The non-SportsPredict raw layer is internally consistent and safe to use later. Full synthetic-question generation remains blocked only on the intentionally deferred SportsPredict snapshot.

## Project structure

- Workspace: `C:\Users\elieberm1\Documents\sports_predict\sports-predict-ee`
- Raw landing package: `C:\Users\elieberm1\Documents\sports_predict\sports-predict-ee\raw_landing`
- Manifest used: `C:\Users\elieberm1\Documents\sports_predict\sports-predict-ee\raw_manifest.csv`
- Reports: `C:\Users\elieberm1\Documents\sports_predict\sports-predict-ee\outputs`
- Logs: none found
- StatBunker manual todo: `C:\Users\elieberm1\Documents\sports_predict\sports-predict-ee\outputs\statbunker_manual_todo.md` (present)

## Environment compatibility

Required canonical variable presence (values not printed):

- `R2_BUCKET`: present
- `R2_ACCOUNT_ID`: present
- `R2_ENDPOINT_URL`: MISSING
- `AWS_ACCESS_KEY_ID`: MISSING
- `AWS_SECRET_ACCESS_KEY`: MISSING
- `AWS_REGION`: MISSING

Compatible aliases used by this audit:

- `R2_ACCESS_KEY_ID`: present
- `R2_SECRET_ACCESS_KEY`: present
- `s3_api`: present

Canonical variables missing: R2_ENDPOINT_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION. The audit connected using existing aliases: R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, s3_api.

## Coverage audit

| source | entity | R2 files | bytes | manifest rows | runs | completeness | notes |
|---|---|---:|---:|---:|---:|---|---|
| sportspredict | events | 2 | 478 | 2 | 2 | complete | latest sample count=1. |
| sportspredict | lobbies | 2 | 258 | 2 | 2 | complete | latest sample count=1. |
| sportspredict | matches | 0 | 0 | 0 | 0 | missing | No objects found under expected prefix. not available. |
| sportspredict | markets | 0 | 0 | 0 | 0 | missing | No objects found under expected prefix. not available. |
| football_data_co_uk | csv | 55 | 8,357,771 | 55 | 2 | complete | Configured coverage 55/55 files. |
| statsbomb_open_data | competitions | 1 | 34,887 | 1 | 1 | complete |  |
| statsbomb_open_data | matches | 4 | 355,871 | 4 | 1 | complete | Cheap JSON count across match files: 193 matches. |
| statsbomb_open_data | events | 193 | 592,275,504 | 193 | 2 | complete | Event IDs without lineups: 0. |
| statsbomb_open_data | lineups | 193 | 4,349,381 | 193 | 2 | complete | Lineup IDs without events: 0. |
| statbunker | referee_cards | 4 | 219,997 | 4 | 1 | present_but_needs_review | Manual todo present: yes. Configured club competitions are present; international comp_ids remain manual. |

## Source-specific findings

### SportsPredict

- Events: 2 files; latest sample count=1.
- Lobbies: 2 files; latest sample count=1.
- Matches: 0 files.
- Markets: 0 files.
- Markets cannot be validated for nonzero size because no market object exists.

### Football-Data.co.uk

- Present: 55/55 configured league-season files.
- Missing: none.
- Files by configured league: england_E0=5, spain_SP1=5, germany_D1=5, italy_I1=5, france_F1=5, netherlands_N1=5, portugal_P1=5, belgium_B1=5, turkey_T1=5, greece_G1=5, scotland_SC0=5.

### StatsBomb Open Data

- Match files: 4; cheap parsed match count: 193.
- Event files: 193.
- Lineup files: 193.
- Event IDs missing lineups: none.
- Lineup IDs missing events: none.

### StatBunker

- Referee-card files: 4.
- Manual todo: present.
- Four configured club competitions are present. International competition IDs remain a documented manual step.

## Manifest versus bucket

- Manifest rows: 454.
- Bucket objects missing from manifest: 0.
- Manifest rows missing from R2: 0.
- Manifest rows with non-success status: 0.
- Zero-byte manifest objects: 0.
- Noncanonical bucket-prefixed keys: 1.
- Total diff records: 1.

The three formerly stale StatBunker error rows are reconciled as uploaded using current R2 metadata.

## Local storage

Local duplicate candidates: 0. No large raw datasets were downloaded during this audit.

## Recommended next actions

1. No further non-SportsPredict raw pull is needed for the configured scope.
2. Leave SportsPredict matches and markets deferred until a credential is available and an explicit pull is approved.
3. Keep international StatBunker competitions as a documented manual extension.
4. The reconciled manifest can be used as the source of truth for later processing.

## Final audit status

1. R2 connection status: PASS
2. Overall completeness status: sports_predict_deferred_non_sportspredict_complete
3. Missing source/entity list: sportspredict/matches, sportspredict/markets
4. Manifest/R2 source mismatch count: 0
5. Recommended next action: no non-SportsPredict repair is required; acquire SportsPredict access only when ready to complete synthetic-question inputs.
