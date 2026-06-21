import random
import time
from typing import Any, Iterator
from urllib.parse import parse_qs, urljoin, urlparse

import requests

from . import config

_AUTH_STRATEGIES = [
    lambda key: {"Authorization": f"Bearer {key}"},
    lambda key: {"X-Api-Key": key},
    lambda key: {"X-API-Key": key},
    lambda key: {"api-key": key},
]


class AuthError(Exception):
    pass


class PaginationError(Exception):
    pass


class SportsPredictClient:
    def __init__(self, api_key: str):
        self._api_key = api_key
        self._auth_headers: dict[str, str] = {}
        self._session = requests.Session()
        self._last_request_time = 0.0
        self._auth_probed = False

    def _probe_auth(self) -> None:
        for strategy in _AUTH_STRATEGIES:
            headers = strategy(self._api_key)
            try:
                resp = self._session.get(
                    f"{config.BASE_URL}/events",
                    headers=headers,
                    timeout=config.REQUEST_TIMEOUT,
                )
            except requests.RequestException:
                continue
            if resp.status_code not in (401, 403):
                self._auth_headers = headers
                self._auth_probed = True
                return
        raise AuthError(
            "All auth strategies failed — check SPORTSPREDICT_API_KEY. "
            "Key starts with: " + self._api_key[:8] + "..."
        )

    def _ensure_auth(self) -> None:
        if not self._auth_probed:
            self._probe_auth()

    def _rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < config.MIN_REQUEST_INTERVAL:
            time.sleep(config.MIN_REQUEST_INTERVAL - elapsed)

    def _handle_rate_limit_headers(self, resp: requests.Response) -> None:
        remaining = resp.headers.get("X-RateLimit-Remaining")
        reset = resp.headers.get("X-RateLimit-Reset")
        if remaining is not None and int(remaining) < 5 and reset is not None:
            now = time.time()
            sleep_for = max(0.0, float(reset) - now)
            if sleep_for > 0:
                print(f"  [rate limit] sleeping {sleep_for:.1f}s until reset")
                time.sleep(sleep_for)

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        self._ensure_auth()
        url = f"{config.BASE_URL}{endpoint}" if endpoint.startswith("/") else endpoint
        headers = {**self._auth_headers, **kwargs.pop("headers", {})}

        for attempt in range(config.MAX_RETRIES + 1):
            self._rate_limit()
            try:
                resp = self._session.request(
                    method,
                    url,
                    headers=headers,
                    timeout=config.REQUEST_TIMEOUT,
                    **kwargs,
                )
            except requests.ConnectionError as exc:
                if attempt < config.MAX_RETRIES:
                    time.sleep(1.0)
                    continue
                raise
            finally:
                self._last_request_time = time.monotonic()

            self._handle_rate_limit_headers(resp)

            if resp.status_code in config.RETRY_STATUS_CODES and attempt < config.MAX_RETRIES:
                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After")
                    wait = float(retry_after) if retry_after else (
                        config.BACKOFF_BASE ** attempt + random.uniform(0, 0.5)
                    )
                else:
                    wait = config.BACKOFF_BASE ** attempt + random.uniform(0, 0.5)
                print(f"  [retry {attempt+1}/{config.MAX_RETRIES}] status={resp.status_code}, waiting {wait:.1f}s")
                time.sleep(wait)
                continue

            return resp

        return resp  # return last response after exhausting retries

    def get(self, endpoint: str, params: dict | None = None) -> Any:
        resp = self._request("GET", endpoint, params=params or {})
        resp.raise_for_status()
        return resp.json()

    def post(self, endpoint: str, json: dict | None = None) -> requests.Response:
        return self._request("POST", endpoint, json=json or {})

    def get_paginated(self, endpoint: str, params: dict | None = None) -> list:
        params = dict(params or {})
        all_items: list = []
        url = f"{config.BASE_URL}{endpoint}" if endpoint.startswith("/") else endpoint
        page_count = 0

        while True:
            if page_count >= 100:
                raise PaginationError(f"Exceeded 100 pages for {endpoint}")
            page_count += 1

            self._ensure_auth()
            self._rate_limit()
            resp = self._session.get(
                url,
                headers=self._auth_headers,
                params=params,
                timeout=config.REQUEST_TIMEOUT,
            )
            self._last_request_time = time.monotonic()
            self._handle_rate_limit_headers(resp)
            resp.raise_for_status()
            data = resp.json()

            items = _extract_items(data)
            all_items.extend(items)

            # Detect next page
            next_url = _detect_next_page(data, resp, params)
            if next_url is None:
                break
            if next_url.startswith("http"):
                url = next_url
                params = {}
            else:
                params = next_url  # dict of updated params

        return all_items


def _extract_items(data: Any) -> list:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "results", "items", "markets", "matches", "events", "lobbies"):
            if key in data and isinstance(data[key], list):
                return data[key]
    return [data] if data else []


def _detect_next_page(data: Any, resp: requests.Response, current_params: dict) -> Any:
    # Pattern A — cursor-based
    if isinstance(data, dict):
        next_cursor = (
            data.get("next_cursor")
            or (data.get("cursor") or {}).get("next")
            or (data.get("meta") or {}).get("next_cursor")
        )
        if next_cursor:
            new_params = dict(current_params)
            new_params["cursor"] = next_cursor
            return new_params

        # Pattern B — offset/limit
        meta = data.get("meta") or data.get("pagination") or {}
        total = meta.get("total") or meta.get("total_count")
        offset = meta.get("offset")
        limit = meta.get("limit") or meta.get("per_page")
        if total is not None and offset is not None and limit is not None:
            next_offset = int(offset) + int(limit)
            if next_offset < int(total):
                new_params = dict(current_params)
                new_params["offset"] = next_offset
                new_params["limit"] = limit
                return new_params

        # Pattern C — page number
        page = meta.get("page") or meta.get("current_page")
        total_pages = meta.get("total_pages") or meta.get("last_page")
        if page is not None and total_pages is not None:
            if int(page) < int(total_pages):
                new_params = dict(current_params)
                new_params["page"] = int(page) + 1
                return new_params

        # Explicit next URL in body
        next_url = data.get("next") or (meta.get("links") or {}).get("next")
        if next_url and isinstance(next_url, str) and next_url.startswith("http"):
            return next_url

    # Pattern D — Link header (RFC 5988)
    link_header = resp.headers.get("Link", "")
    if link_header:
        for part in link_header.split(","):
            part = part.strip()
            if 'rel="next"' in part:
                url_part = part.split(";")[0].strip().strip("<>")
                return url_part

    return None
