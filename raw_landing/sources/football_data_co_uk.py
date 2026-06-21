"""
Download free historical match CSV files from Football-Data.co.uk.

URL pattern:
  https://www.football-data.co.uk/mmz4281/{season}/{code}.csv

5 seasons × 11 leagues = 55 files.
No API key required. 2-second delay between requests.
Files streamed directly to R2 — no local copy retained.
"""
from __future__ import annotations

from datetime import date

from .. import manifest, r2
from ..http import polite_get, PLAIN_HEADERS

_BASE = "https://www.football-data.co.uk/mmz4281"

SEASONS = ["2526", "2425", "2324", "2223", "2122"]

LEAGUES: dict[str, str] = {
    "england_E0":     "E0",
    "spain_SP1":      "SP1",
    "germany_D1":     "D1",
    "italy_I1":       "I1",
    "france_F1":      "F1",
    "netherlands_N1": "N1",
    "portugal_P1":    "P1",
    "belgium_B1":     "B1",
    "turkey_T1":      "T1",
    "greece_G1":      "G1",
    "scotland_SC0":   "SC0",
}


def _r2_key(label: str, season: str, run_id: str) -> str:
    today = date.today().isoformat()
    filename = f"{label}_{season}.csv"
    return f"raw/football_data_co_uk/csv/ingested_date={today}/run_id={run_id}/{filename}"


def _planned_files() -> list[tuple[str, str, str]]:
    """Returns [(label, season, url), ...]"""
    files = []
    for label, code in LEAGUES.items():
        for season in SEASONS:
            url = f"{_BASE}/{season}/{code}.csv"
            files.append((label, season, url))
    return files


def run(run_id: str, seasons: int = 5, dry_run: bool = False) -> list[manifest.ManifestRow]:
    season_list = SEASONS[:seasons]
    rows: list[manifest.ManifestRow] = []
    total = len(LEAGUES) * len(season_list)
    done = 0

    print(f"  [fd] {total} files planned ({len(season_list)} seasons × {len(LEAGUES)} leagues)")

    for label, code in LEAGUES.items():
        for season in season_list:
            url = f"{_BASE}/{season}/{code}.csv"
            key = _r2_key(label, season, run_id)
            done += 1

            if dry_run:
                print(f"  [fd] DRY-RUN [{done}/{total}] {url} -> {key}")
                rows.append(manifest.ManifestRow(
                    run_id=run_id, source_name="football_data_co_uk",
                    entity_name="csv", source_url=url,
                    r2_key=key, r2_uri=r2.r2_uri(key), status="dry_run",
                ))
                continue

            if manifest.already_uploaded(key):
                print(f"  [fd] [{done}/{total}] skipped (already uploaded): {label}_{season}")
                row = manifest.ManifestRow(
                    run_id=run_id, source_name="football_data_co_uk",
                    entity_name="csv", source_url=url,
                    r2_key=key, r2_uri=r2.r2_uri(key), status="skipped",
                )
                rows.append(row)
                continue

            try:
                resp = polite_get(url, delay=2.0, headers=PLAIN_HEADERS)
                data = resp.content
                n = r2.upload_bytes(key, data, "text/csv")
                row = manifest.ManifestRow(
                    run_id=run_id, source_name="football_data_co_uk",
                    entity_name="csv", source_url=url,
                    r2_key=key, r2_uri=r2.r2_uri(key), bytes_uploaded=n,
                    row_count_if_known=max(0, len(data.splitlines()) - 1),
                )
                manifest.append_row(row)
                rows.append(row)
                print(f"  [fd] [{done}/{total}] {label}_{season}: {n:,} bytes")
            except Exception as exc:
                note = str(exc)[:120]
                print(f"  [fd] [{done}/{total}] SKIP {label}_{season}: {note}")
                row = manifest.ManifestRow(
                    run_id=run_id, source_name="football_data_co_uk",
                    entity_name="csv", source_url=url,
                    r2_key=key, r2_uri=r2.r2_uri(key), status="error", notes=note,
                )
                manifest.append_row(row)
                rows.append(row)

    uploaded = sum(1 for r_ in rows if r_.status == "uploaded")
    print(f"  [fd] done — {uploaded}/{total} uploaded")
    return rows
