"""
Thin client for API-Football v3 (api-sports.io).
Auth: header x-apisports-key
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import requests

from .. import config

BASE_URL = "https://v3.football.api-sports.io"
TIMEOUT = 30


def _headers() -> dict:
    return {"x-apisports-key": config.FOOTBALL_DATA_API_KEY}


def _get(path: str, params: dict | None = None, retries: int = 3, cooldown: int = 65) -> dict:
    if not config.FOOTBALL_DATA_API_KEY:
        raise RuntimeError("FOOTBALL_DATA_API_KEY not configured")
    for attempt in range(retries + 1):
        resp = requests.get(f"{BASE_URL}{path}", headers=_headers(), params=params or {}, timeout=TIMEOUT)
        if resp.status_code == 429 and attempt < retries:
            # Free plan caps at 10 req/min; wait for the window to reset and retry.
            print(f"    [api_football] 429 on {path}; cooling down {cooldown}s "
                  f"(attempt {attempt + 1}/{retries})")
            time.sleep(cooldown)
            continue
        resp.raise_for_status()
        return resp.json()
    resp.raise_for_status()
    return resp.json()


def ping() -> dict:
    if not config.FOOTBALL_DATA_API_KEY:
        return {"status": "skipped", "message": "FOOTBALL_DATA_API_KEY not configured"}
    try:
        data = _get("/status")
        sub = data.get("response", {}).get("subscription", {})
        plan = sub.get("plan", "unknown")
        reqs = data.get("response", {}).get("requests", {})
        remaining = reqs.get("current", "?")
        limit = reqs.get("limit_day", "?")
        return {"status": "ok", "message": f"plan={plan}, requests_today={remaining}/{limit}"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def get_status() -> dict:
    return _get("/status")


def search_team(name: str) -> list[dict]:
    time.sleep(1)
    data = _get("/teams", {"name": name})
    return data.get("response", [])


def get_fixtures_by_team(team_id: int, season: int, last: int = 5) -> list[dict]:
    time.sleep(1)
    data = _get("/fixtures", {"team": team_id, "season": season, "last": last})
    return data.get("response", [])


def get_team_season_fixtures(team_id: int, season: int) -> list[dict]:
    """All fixtures for a team in a season (Free plan: seasons 2022-2024 only).

    The Free plan blocks the `last`/`next` params, so we pull a whole season and
    filter/sort client-side. Each item carries teams, goals and score.halftime.
    """
    time.sleep(1)
    data = _get("/fixtures", {"team": team_id, "season": season})
    return data.get("response", [])


def recent_finished(team_id: int, season: int, n: int) -> list[dict]:
    """The `n` most-recent FINISHED fixtures for a team in a season, newest first."""
    fx = [f for f in get_team_season_fixtures(team_id, season)
          if f.get("fixture", {}).get("status", {}).get("short") == "FT"]
    fx.sort(key=lambda f: f["fixture"]["date"], reverse=True)
    return fx[:n]


def get_fixture_events(fixture_id: int) -> list[dict]:
    time.sleep(1)
    data = _get("/fixtures/events", {"fixture": fixture_id})
    return data.get("response", [])


def requests_remaining() -> tuple[int, int]:
    """Return (used_today, daily_limit) from /status. Used by the budget guard."""
    data = _get("/status")
    reqs = data.get("response", {}).get("requests", {})
    used = int(reqs.get("current", 0) or 0)
    limit = int(reqs.get("limit_day", 0) or 0)
    return used, limit


def get_fixture(fixture_id: int) -> dict:
    time.sleep(1)
    data = _get("/fixtures", {"id": fixture_id})
    items = data.get("response", [])
    return items[0] if items else {}


def get_fixture_statistics(fixture_id: int) -> list[dict]:
    time.sleep(1)
    data = _get("/fixtures/statistics", {"fixture": fixture_id})
    return data.get("response", [])


def get_fixture_players(fixture_id: int) -> list[dict]:
    time.sleep(1)
    data = _get("/fixtures/players", {"fixture": fixture_id})
    return data.get("response", [])


def get_fixture_lineups(fixture_id: int) -> list[dict]:
    time.sleep(1)
    data = _get("/fixtures/lineups", {"fixture": fixture_id})
    return data.get("response", [])


def get_fixtures_by_referee(referee_name: str, season: int) -> list[dict]:
    time.sleep(1)
    # API-Football supports searching by referee name on /fixtures
    data = _get("/fixtures", {"referee": referee_name, "season": season})
    return data.get("response", [])


def save_sample(data, filename: str) -> Path:
    config.RAW_SAMPLES.mkdir(parents=True, exist_ok=True)
    path = config.RAW_SAMPLES / filename
    text = config.redact(json.dumps(data, indent=2, ensure_ascii=False))
    path.write_text(text, encoding="utf-8")
    return path
