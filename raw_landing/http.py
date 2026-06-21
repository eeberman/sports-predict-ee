"""
Shared HTTP helpers: polite GET with retry and configurable delay.
"""
from __future__ import annotations

import time

import requests

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

PLAIN_HEADERS = {
    "User-Agent": "research-bot/1.0",
    "Accept": "*/*",
}

_RETRY_STATUSES = {429, 500, 502, 503, 504}
_MAX_RETRIES = 3
_RETRY_DELAY = 2.0


def polite_get(
    url: str,
    delay: float = 1.0,
    timeout: int = 30,
    headers: dict | None = None,
    stream: bool = False,
) -> requests.Response:
    if headers is None:
        headers = PLAIN_HEADERS
    time.sleep(delay)
    for attempt in range(_MAX_RETRIES):
        resp = requests.get(url, headers=headers, timeout=timeout, stream=stream)
        if resp.status_code not in _RETRY_STATUSES:
            break
        wait = _RETRY_DELAY * (attempt + 1)
        print(f"    HTTP {resp.status_code} — retrying in {wait:.0f}s ({attempt+1}/{_MAX_RETRIES})")
        time.sleep(wait)
    resp.raise_for_status()
    return resp
