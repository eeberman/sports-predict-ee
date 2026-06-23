"""Rebuild raw_manifest.csv from immutable R2 object metadata."""
from __future__ import annotations

import csv
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from . import config, r2
from .manifest import _FIELDS
from .sources.football_data_co_uk import LEAGUES


PREFIXES = [
    ("sportspredict", "events", "raw/sportspredict/events/"),
    ("sportspredict", "lobbies", "raw/sportspredict/lobbies/"),
    ("sportspredict", "matches", "raw/sportspredict/matches/"),
    ("sportspredict", "markets", "raw/sportspredict/markets/"),
    ("football_data_co_uk", "csv", "raw/football_data_co_uk/csv/"),
    ("statsbomb_open_data", "competitions", "raw/statsbomb_open_data/competitions/"),
    ("statsbomb_open_data", "matches", "raw/statsbomb_open_data/matches/"),
    ("statsbomb_open_data", "events", "raw/statsbomb_open_data/events/"),
    ("statsbomb_open_data", "lineups", "raw/statsbomb_open_data/lineups/"),
    ("statbunker", "referee_cards", "raw/statbunker/referee_cards/"),
]


def _existing_rows() -> dict[str, dict]:
    if not config.MANIFEST_PATH.exists():
        return {}
    with config.MANIFEST_PATH.open(newline="", encoding="utf-8-sig") as handle:
        return {row["r2_key"]: row for row in csv.DictReader(handle) if row.get("r2_key")}


def _run_id(key: str) -> str:
    match = re.search(r"(?:^|/)run_id=([^/]+)", key)
    return match.group(1) if match else ""


def _source_url(source: str, entity: str, key: str) -> str:
    filename = Path(key).name
    stem = Path(filename).stem
    if source == "football_data_co_uk":
        match = re.match(r"(.+)_(\d{4})$", stem)
        if match:
            label, season = match.groups()
            code = LEAGUES.get(label, "")
            if code:
                return f"https://www.football-data.co.uk/mmz4281/{season}/{code}.csv"
    if source == "statsbomb_open_data":
        base = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
        if entity == "competitions":
            return f"{base}/competitions.json"
        if entity == "matches":
            match = re.match(r"matches_(\d+)_(\d+)$", stem)
            if match:
                return f"{base}/matches/{match.group(1)}/{match.group(2)}.json"
        return f"{base}/{entity}/{filename}"
    if source == "statbunker":
        comp_id = stem.split("_", 1)[0]
        return f"https://www.statbunker.com/competitions/RefereeYellowCards?comp_id={comp_id}"
    base = "https://api.sportspredict.com/api/v1"
    if entity == "events":
        return f"{base}/events"
    identifiers = {
        "lobbies": ("lobbies_", "events", "lobbies"),
        "matches": ("matches_", "lobbies", "matches"),
        "markets": ("markets_", "matches", "markets"),
    }
    prefix, parent, child = identifiers.get(entity, ("", "", ""))
    identifier = stem.removeprefix(prefix)
    return f"{base}/{parent}/{identifier}/{child}" if identifier else ""


def reconcile() -> tuple[int, Path | None]:
    existing = _existing_rows()
    backup: Path | None = None
    if config.MANIFEST_PATH.exists():
        backup_dir = config.OUTPUTS / "manifest_backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = backup_dir / f"raw_manifest.pre_reconcile.{stamp}.csv"
        shutil.copy2(config.MANIFEST_PATH, backup)

    rebuilt: list[dict] = []
    for source, entity, prefix in PREFIXES:
        for item in r2.list_objects(prefix):
            if int(item["Size"]) <= 0:
                raise RuntimeError(f"Refusing to manifest zero-byte object: {item['Key']}")
            old = existing.get(item["Key"], {})
            prior_status = (old.get("status") or "").strip().lower()
            notes = (old.get("notes") or "").strip()
            note_parts = [
                part.strip() for part in notes.split(";")
                if part.strip()
                and not part.strip().startswith("reconciled_from_r2_metadata")
            ]
            if prior_status and prior_status != "uploaded" and not any(
                part.startswith("prior_status=") for part in note_parts
            ):
                note_parts.append(f"prior_status={prior_status}")
            note_parts.append("reconciled_from_r2_metadata")
            notes = "; ".join(note_parts)
            rebuilt.append({
                "run_id": _run_id(item["Key"]),
                "source_name": source,
                "entity_name": entity,
                "source_url": old.get("source_url") or _source_url(source, entity, item["Key"]),
                "source_params_json": old.get("source_params_json") or "{}",
                "r2_key": item["Key"],
                "r2_uri": r2.r2_uri(item["Key"]),
                "local_temp_path": "",
                "status": "uploaded",
                "bytes_uploaded": int(item["Size"]),
                "row_count_if_known": old.get("row_count_if_known") or -1,
                "ingested_at_utc": item["LastModified"].astimezone(timezone.utc).isoformat(),
                "notes": notes,
            })

    rebuilt.sort(key=lambda row: row["r2_key"])
    config.MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = config.MANIFEST_PATH.with_suffix(".csv.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=_FIELDS)
        writer.writeheader()
        writer.writerows(rebuilt)
    temporary.replace(config.MANIFEST_PATH)
    print(f"Reconciled manifest rows: {len(rebuilt)}")
    if backup:
        print(f"Previous manifest backup: {backup}")
    return len(rebuilt), backup
