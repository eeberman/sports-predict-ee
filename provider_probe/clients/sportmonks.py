"""
Thin client for Sportmonks v3 Football API (optional).
"""

from __future__ import annotations

import json
from pathlib import Path

import requests

from .. import config

BASE_URL = "https://api.sportmonks.com/v3/football"
TIMEOUT = 30


def _get(path: str, params: dict | None = None) -> dict:
    if not config.SPORTMONKS_API_KEY:
        raise RuntimeError("SPORTMONKS_API_KEY not configured")
    p = {**(params or {}), "api_token": config.SPORTMONKS_API_KEY}
    resp = requests.get(f"{BASE_URL}{path}", params=p, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def ping() -> dict:
    if not config.SPORTMONKS_API_KEY:
        return {"status": "skipped", "message": "SPORTMONKS_API_KEY not configured"}
    try:
        data = _get("/core/my-subscription")
        plan = data.get("data", {}).get("plan", {}).get("name", "unknown")
        return {"status": "ok", "message": f"plan={plan}"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def save_sample(data, filename: str) -> Path:
    config.RAW_SAMPLES.mkdir(parents=True, exist_ok=True)
    path = config.RAW_SAMPLES / filename
    text = config.redact(json.dumps(data, indent=2, ensure_ascii=False))
    path.write_text(text, encoding="utf-8")
    return path
