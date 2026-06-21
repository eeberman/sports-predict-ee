"""
Local manifest: tracks every file uploaded to R2 so re-runs skip already-uploaded keys.
"""
from __future__ import annotations

import csv
import dataclasses
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from . import config

_FIELDS = [
    "run_id", "source_name", "entity_name", "source_url",
    "source_params_json", "r2_key", "r2_uri", "local_temp_path",
    "status", "bytes_uploaded", "row_count_if_known",
    "ingested_at_utc", "notes",
]


@dataclasses.dataclass
class ManifestRow:
    run_id: str
    source_name: str
    entity_name: str
    source_url: str
    source_params_json: str = "{}"
    r2_key: str = ""
    r2_uri: str = ""
    local_temp_path: str = ""
    status: str = "uploaded"        # "uploaded", "skipped", "error"
    bytes_uploaded: int = 0
    row_count_if_known: int = -1
    ingested_at_utc: str = dataclasses.field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    notes: str = ""


def append_row(row: ManifestRow) -> None:
    path = config.MANIFEST_PATH
    write_header = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(dataclasses.asdict(row))


def load() -> pd.DataFrame:
    path = config.MANIFEST_PATH
    if not path.exists():
        return pd.DataFrame(columns=_FIELDS)
    return pd.read_csv(path, dtype=str)


def already_uploaded(r2_key: str) -> bool:
    df = load()
    if df.empty:
        return False
    match = df[(df["r2_key"] == r2_key) & (df["status"] == "uploaded")]
    return not match.empty
