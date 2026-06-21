"""
Thin client for The Odds API v4.
Auth: query param apiKey=...
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import requests

from .. import config

BASE_URL = "https://api.the-odds-api.com/v4"
TIMEOUT = 30

SOCCER_SPORT_KEYS = [
    "soccer_fifa_world_cup_2026",
    "soccer_fifa_world_cup",
    "soccer_international",
    "soccer_conmebol_copa_america",
    "soccer_africa_cup_of_nations",
]


def _get(path: str, params: dict | None = None) -> dict | list:
    if not config.ODDS_API_KEY:
        raise RuntimeError("ODDS_API_KEY not configured")
    p = {**(params or {}), "apiKey": config.ODDS_API_KEY}
    resp = requests.get(f"{BASE_URL}{path}", params=p, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def ping() -> dict:
    if not config.ODDS_API_KEY:
        return {"status": "skipped", "message": "ODDS_API_KEY not configured"}
    try:
        data = _get("/sports/", {"all": "false"})
        soccer = [s for s in data if "soccer" in s.get("key", "")]
        return {"status": "ok", "message": f"{len(soccer)} soccer sports available"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def get_sports() -> list[dict]:
    return _get("/sports/", {"all": "false"})


def get_odds(sport_key: str, regions: str = "eu", markets: str = "h2h,totals,spreads,btts") -> list[dict]:
    time.sleep(1)
    return _get(f"/sports/{sport_key}/odds/", {"regions": regions, "markets": markets})


def get_scores(sport_key: str, days_from: int = 3) -> list[dict]:
    time.sleep(1)
    return _get(f"/sports/{sport_key}/scores/", {"daysFrom": str(days_from)})


def find_active_sport_key() -> str | None:
    sports = get_sports()
    active_keys = {s["key"] for s in sports if not s.get("has_outrights", True)}
    for key in SOCCER_SPORT_KEYS:
        if key in active_keys:
            return key
    # Fall back to any active soccer sport
    for s in sports:
        if "soccer" in s.get("key", "") and not s.get("has_outrights", True):
            return s["key"]
    # Try any soccer key regardless of active status
    for s in sports:
        if "soccer" in s.get("key", ""):
            return s["key"]
    return None


def save_sample(data, filename: str) -> Path:
    config.RAW_SAMPLES.mkdir(parents=True, exist_ok=True)
    path = config.RAW_SAMPLES / filename
    text = config.redact(json.dumps(data, indent=2, ensure_ascii=False))
    path.write_text(text, encoding="utf-8")
    return path
