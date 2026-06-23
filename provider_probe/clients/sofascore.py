"""
Thin client for Sofascore's INTERNAL (undocumented) event-statistics API.

UNTESTED / EXPERIMENTAL — Sofascore sits behind Cloudflare bot protection and returns
403 to server-side requests without a browser/residential context. Kept so the pipeline
can use it from a reachable environment later; all derived data is provenance-tagged
`sofascore_untested` and never the sole basis for a deviation (see plan Phase E).

When reachable, this is the only free source with true full/1H/2H stat groups:
  /search/all?q=NAME            -> team entities
  /team/{id}/events/last/{page} -> recent matches
  /event/{id}/statistics        -> statistics[period ALL|1ST|2ND].groups[].statisticsItems
"""
from __future__ import annotations

import time

import requests

BASE = "https://api.sofascore.com/api/v1"
TIMEOUT = 20
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com",
}


class SofascoreBlocked(RuntimeError):
    """Raised when Cloudflare blocks the request (403) — the expected failure here."""


def _get(path: str) -> dict:
    time.sleep(2)  # polite delay for an unofficial endpoint
    resp = requests.get(f"{BASE}{path}", headers=_HEADERS, timeout=TIMEOUT)
    if resp.status_code == 403:
        raise SofascoreBlocked(f"403 (Cloudflare) on {path}")
    resp.raise_for_status()
    return resp.json()


def search_team(name: str) -> list[dict]:
    res = _get(f"/search/all?q={name}")
    return [r["entity"] for r in res.get("results", []) if r.get("type") == "team"]


def team_recent_events(team_id: int, page: int = 0) -> list[dict]:
    return _get(f"/team/{team_id}/events/last/{page}").get("events", [])


def event_statistics(event_id: int) -> dict:
    return _get(f"/event/{event_id}/statistics")


def reachable() -> tuple[bool, str]:
    """Cheap connectivity probe. Returns (ok, detail)."""
    try:
        _get("/sport/football/events/live")
        return True, "reachable"
    except SofascoreBlocked as exc:
        return False, str(exc)
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {str(exc)[:80]}"
