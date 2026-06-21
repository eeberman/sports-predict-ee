"""
Pull StatsBomb Open Data from GitHub raw URLs.

Scope:
  - competitions.json (all)
  - Filter: country_name == "International"
  - For each international competition: 2 most recent seasons
  - For each (competition_id, season_id): matches JSON
  - For each match: events JSON + lineups JSON

No git clone. Direct per-file HTTP GET. 1-second delay between requests.
Files streamed to R2 — no local disk storage.
"""
from __future__ import annotations

import json
from datetime import date

from .. import manifest, r2
from ..http import polite_get, PLAIN_HEADERS

_BASE = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"


def _r2_key(entity: str, filename: str, run_id: str) -> str:
    today = date.today().isoformat()
    return f"raw/statsbomb_open_data/{entity}/ingested_date={today}/run_id={run_id}/{filename}"


def _fetch_json(url: str) -> bytes:
    resp = polite_get(url, delay=1.0, headers=PLAIN_HEADERS)
    return resp.content


def _upload_or_skip(
    url: str, entity: str, filename: str, run_id: str, rows: list
) -> tuple[bool, str]:
    key = _r2_key(entity, filename, run_id)
    if manifest.already_uploaded(key):
        return False, key
    try:
        data = _fetch_json(url)
        n = r2.upload_bytes(key, data, "application/json")
        row = manifest.ManifestRow(
            run_id=run_id, source_name="statsbomb_open_data",
            entity_name=entity, source_url=url,
            r2_key=key, r2_uri=r2.r2_uri(key), bytes_uploaded=n,
        )
        manifest.append_row(row)
        rows.append(row)
        return True, key
    except Exception as exc:
        note = str(exc)[:120]
        row = manifest.ManifestRow(
            run_id=run_id, source_name="statsbomb_open_data",
            entity_name=entity, source_url=url,
            r2_key=key, r2_uri=r2.r2_uri(key), status="error", notes=note,
        )
        manifest.append_row(row)
        rows.append(row)
        return False, key


def run(run_id: str, cycles: int = 2, dry_run: bool = False) -> list[manifest.ManifestRow]:
    rows: list[manifest.ManifestRow] = []

    # --- competitions ---
    comp_url = f"{_BASE}/competitions.json"
    comp_key = _r2_key("competitions", "competitions.json", run_id)
    print(f"  [sb] {'DRY-RUN ' if dry_run else ''}competitions -> {comp_key}")

    if dry_run:
        rows.append(manifest.ManifestRow(
            run_id=run_id, source_name="statsbomb_open_data",
            entity_name="competitions", source_url=comp_url,
            r2_key=comp_key, r2_uri=r2.r2_uri(comp_key), status="dry_run",
        ))
        # Use a stub for dry-run so we can show planned match/event files
        competitions_raw = _fetch_json(comp_url)
        competitions: list[dict] = json.loads(competitions_raw)
    else:
        if not manifest.already_uploaded(comp_key):
            data = _fetch_json(comp_url)
            n = r2.upload_bytes(comp_key, data, "application/json")
            row = manifest.ManifestRow(
                run_id=run_id, source_name="statsbomb_open_data",
                entity_name="competitions", source_url=comp_url,
                r2_key=comp_key, r2_uri=r2.r2_uri(comp_key), bytes_uploaded=n,
                row_count_if_known=len(json.loads(data)),
            )
            manifest.append_row(row)
            rows.append(row)
            competitions = json.loads(data)
            print(f"    uploaded {n:,} bytes, {len(competitions)} competitions")
        else:
            print("    skipped (already uploaded)")
            competitions = json.loads(_fetch_json(comp_url))

    # Filter international competitions
    international = [c for c in competitions if c.get("country_name") == "International"]
    print(f"  [sb] {len(international)} international competitions found")

    # Group by competition_id and pick `cycles` most recent seasons
    from collections import defaultdict
    comp_seasons: dict[int, list[dict]] = defaultdict(list)
    for c in international:
        comp_seasons[c["competition_id"]].append(c)

    selected: list[dict] = []
    for comp_id, seasons in comp_seasons.items():
        sorted_seasons = sorted(seasons, key=lambda x: x["season_name"], reverse=True)
        selected.extend(sorted_seasons[:cycles])

    print(f"  [sb] {len(selected)} competition-seasons selected ({cycles} most recent per competition)")

    total_matches = 0
    total_events = 0

    for cs in selected:
        comp_id = cs["competition_id"]
        season_id = cs["season_id"]
        comp_name = cs.get("competition_name", "")
        season_name = cs.get("season_name", "")
        label = f"{comp_name} {season_name}".strip()

        # matches file
        match_url = f"{_BASE}/matches/{comp_id}/{season_id}.json"
        match_filename = f"matches_{comp_id}_{season_id}.json"
        match_key = _r2_key("matches", match_filename, run_id)

        print(f"  [sb] {'DRY-RUN ' if dry_run else ''}matches {label} -> {match_key}")

        if dry_run:
            rows.append(manifest.ManifestRow(
                run_id=run_id, source_name="statsbomb_open_data",
                entity_name="matches", source_url=match_url,
                r2_key=match_key, r2_uri=r2.r2_uri(match_key), status="dry_run",
            ))
            try:
                match_data = json.loads(_fetch_json(match_url))
            except Exception:
                match_data = []
        else:
            if not manifest.already_uploaded(match_key):
                try:
                    raw_matches = _fetch_json(match_url)
                    n = r2.upload_bytes(match_key, raw_matches, "application/json")
                    match_data = json.loads(raw_matches)
                    row = manifest.ManifestRow(
                        run_id=run_id, source_name="statsbomb_open_data",
                        entity_name="matches", source_url=match_url,
                        r2_key=match_key, r2_uri=r2.r2_uri(match_key), bytes_uploaded=n,
                        row_count_if_known=len(match_data),
                    )
                    manifest.append_row(row)
                    rows.append(row)
                    print(f"    {len(match_data)} matches, {n:,} bytes")
                    total_matches += len(match_data)
                except Exception as exc:
                    print(f"    SKIP matches {label}: {exc}")
                    match_data = []
            else:
                print("    skipped (already uploaded)")
                match_data = json.loads(_fetch_json(match_url))

        # events + lineups per match
        for m in match_data:
            match_id = m.get("match_id")
            if not match_id:
                continue

            for entity, path_seg in [("events", "events"), ("lineups", "lineups")]:
                file_url = f"{_BASE}/{path_seg}/{match_id}.json"
                filename = f"{match_id}.json"
                ek = _r2_key(entity, filename, run_id)

                if dry_run:
                    rows.append(manifest.ManifestRow(
                        run_id=run_id, source_name="statsbomb_open_data",
                        entity_name=entity, source_url=file_url,
                        r2_key=ek, r2_uri=r2.r2_uri(ek), status="dry_run",
                    ))
                    if entity == "events":
                        total_events += 1
                else:
                    ok, _ = _upload_or_skip(file_url, entity, filename, run_id, rows)
                    if ok and entity == "events":
                        total_events += 1

    label_suffix = "(dry-run planned)" if dry_run else "uploaded"
    print(f"  [sb] done — {total_matches} matches, ~{total_events} event files {label_suffix}")
    print(f"  [sb] total manifest rows this run: {len(rows)}")
    return rows
