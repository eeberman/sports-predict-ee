"""Durable state helpers for idempotent scheduled runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import config


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def load_sent_state() -> dict[str, Any]:
    state = _read_json(config.SENT_EMAILS_PATH, {"sent_emails": {}, "failure_emails": {}})
    state.setdefault("sent_emails", {})
    state.setdefault("failure_emails", {})
    return state


def save_sent_state(state: dict[str, Any]) -> None:
    _write_json(config.SENT_EMAILS_PATH, state)


def load_match_snapshot(match_id: str) -> dict[str, Any] | None:
    path = config.SNAPSHOT_DIR / f"{match_id}.json"
    if not path.exists():
        return None
    return _read_json(path, None)


def save_match_snapshot(match_id: str, snapshot: dict[str, Any]) -> Path:
    path = config.SNAPSHOT_DIR / f"{match_id}.json"
    _write_json(path, snapshot)
    return path

