"""Selective, immutable repair of non-SportsPredict raw landing gaps."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from uuid import uuid4

import requests

from . import manifest, r2
from .sources.football_data_co_uk import LEAGUES, SEASONS


FOOTBALL_BASE = "https://www.football-data.co.uk/mmz4281"
STATSBOMB_BASE = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"


@dataclass(frozen=True)
class RepairTarget:
    source_name: str
    entity_name: str
    filename: str
    source_url: str
    content_type: str


def _filenames(prefix: str) -> set[str]:
    return {Path(item["Key"]).name for item in r2.list_objects(prefix)}


def _statsbomb_match_ids() -> set[str]:
    match_ids: set[str] = set()
    for item in r2.list_objects("raw/statsbomb_open_data/matches/"):
        data = json.loads(r2.download_bytes(item["Key"], max_bytes=2_000_000))
        if not isinstance(data, list):
            raise RuntimeError(f"StatsBomb match index is not a list: {item['Key']}")
        match_ids.update(str(row["match_id"]) for row in data if row.get("match_id") is not None)
    return match_ids


def build_plan() -> list[RepairTarget]:
    targets: list[RepairTarget] = []
    football_present = _filenames("raw/football_data_co_uk/csv/")
    for label, code in LEAGUES.items():
        for season in SEASONS:
            filename = f"{label}_{season}.csv"
            if filename not in football_present:
                targets.append(RepairTarget(
                    "football_data_co_uk",
                    "csv",
                    filename,
                    f"{FOOTBALL_BASE}/{season}/{code}.csv",
                    "text/csv",
                ))

    match_ids = _statsbomb_match_ids()
    for entity in ("events", "lineups"):
        present = {Path(name).stem for name in _filenames(f"raw/statsbomb_open_data/{entity}/")}
        for match_id in sorted(match_ids - present):
            targets.append(RepairTarget(
                "statsbomb_open_data",
                entity,
                f"{match_id}.json",
                f"{STATSBOMB_BASE}/{entity}/{match_id}.json",
                "application/json",
            ))
    return sorted(targets, key=lambda item: (item.source_name, item.entity_name, item.filename))


def summarize(targets: list[RepairTarget]) -> dict[str, int]:
    counts = {
        "football_csv": sum(t.source_name == "football_data_co_uk" for t in targets),
        "statsbomb_events": sum(t.entity_name == "events" for t in targets),
        "statsbomb_lineups": sum(t.entity_name == "lineups" for t in targets),
        "total": len(targets),
    }
    print("Non-SportsPredict repair plan (read-only):")
    print(f"  Football CSV files: {counts['football_csv']}")
    print(f"  StatsBomb event files: {counts['statsbomb_events']}")
    print(f"  StatsBomb lineup files: {counts['statsbomb_lineups']}")
    print(f"  Total files: {counts['total']}")
    for target in targets:
        print(f"  - {target.source_name}/{target.entity_name}/{target.filename}")
    return counts


def _fetch(target: RepairTarget) -> bytes:
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            response = requests.get(target.source_url, timeout=60)
            response.raise_for_status()
            data = response.content
            if not data:
                raise ValueError("source returned zero bytes")
            return data
        except Exception as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(2 * attempt)
    raise RuntimeError(f"Fetch failed after 3 attempts: {type(last_error).__name__}") from last_error


def _validate(target: RepairTarget, data: bytes) -> int:
    if target.entity_name == "csv":
        text = data.decode("utf-8-sig")
        lines = text.splitlines()
        if len(lines) < 2 or "," not in lines[0]:
            raise ValueError(f"Invalid Football-Data CSV: {target.filename}")
        return len(lines) - 1
    value = json.loads(data)
    if not isinstance(value, list):
        raise ValueError(f"StatsBomb JSON is not a list: {target.filename}")
    return len(value)


def apply(targets: list[RepairTarget]) -> tuple[str, int]:
    if not targets:
        print("No missing non-SportsPredict objects; nothing to upload.")
        return "", 0
    run_id = uuid4().hex[:8]
    ingested_date = date.today().isoformat()
    uploaded = 0
    for index, target in enumerate(targets, start=1):
        prefix = f"raw/{target.source_name}/{target.entity_name}/"
        if target.filename in _filenames(prefix):
            print(f"[{index}/{len(targets)}] skipped; logical object now exists: {target.filename}")
            continue
        key = f"{prefix}ingested_date={ingested_date}/run_id={run_id}/{target.filename}"
        print(f"[{index}/{len(targets)}] fetching {target.source_name}/{target.entity_name}/{target.filename}")
        data = _fetch(target)
        row_count = _validate(target, data)
        size = r2.upload_bytes(key, data, target.content_type)
        manifest.append_row(manifest.ManifestRow(
            run_id=run_id,
            source_name=target.source_name,
            entity_name=target.entity_name,
            source_url=target.source_url,
            r2_key=key,
            r2_uri=r2.r2_uri(key),
            bytes_uploaded=size,
            row_count_if_known=row_count,
            notes="selective_non_sportspredict_repair",
        ))
        uploaded += 1
        print(f"  uploaded and verified: {size:,} bytes")
    print(f"Repair run {run_id}: {uploaded}/{len(targets)} files uploaded")
    return run_id, uploaded
