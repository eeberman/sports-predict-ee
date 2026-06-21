"""
Pull raw SportsPredict contest data and upload to R2.

Endpoints used (read-only):
  GET /events
  GET /events/{id}/lobbies
  GET /lobbies/{id}/matches   (paginated)
  GET /matches/{id}/markets   (paginated)

Never calls join, submit, update, or predict endpoints.
"""
from __future__ import annotations

import json
import time
from datetime import date
from typing import Any

import requests

from .. import config, manifest, r2

_BASE = "https://api.sportspredict.com/api/v1"
_AUTH_STRATEGIES = [
    lambda key: {"Authorization": f"Bearer {key}"},
    lambda key: {"X-Api-Key": key},
    lambda key: {"X-API-Key": key},
    lambda key: {"api-key": key},
]
_MIN_DELAY = 0.5


def _probe_auth(key: str) -> dict:
    for strategy in _AUTH_STRATEGIES:
        headers = strategy(key)
        try:
            time.sleep(_MIN_DELAY)
            resp = requests.get(f"{_BASE}/events", headers=headers, timeout=15)
            if resp.status_code not in (401, 403):
                return headers
        except requests.RequestException:
            pass
    raise RuntimeError("All SportsPredict auth strategies failed")


def _get(url: str, headers: dict, params: dict | None = None) -> Any:
    time.sleep(_MIN_DELAY)
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _paginate(url: str, headers: dict, params: dict | None = None) -> list:
    results: list = []
    params = dict(params or {})
    page = 1
    while True:
        params["page"] = page
        data = _get(url, headers, params)
        if isinstance(data, list):
            results.extend(data)
            if not data:
                break
            page += 1
        elif isinstance(data, dict):
            items = data.get("data") or data.get("results") or data.get("markets") or data.get("matches") or []
            results.extend(items)
            meta = data.get("meta") or {}
            total_pages = meta.get("total_pages") or meta.get("last_page")
            if total_pages and page >= int(total_pages):
                break
            if not items:
                break
            page += 1
        else:
            break
    return results


def _r2_key(entity: str, filename: str, run_id: str) -> str:
    today = date.today().isoformat()
    return f"raw/sportspredict/{entity}/ingested_date={today}/run_id={run_id}/{filename}"


def run(run_id: str, dry_run: bool = False) -> list[manifest.ManifestRow]:
    config.validate_sportspredict()
    sp_key = config.get("SPORTSPREDICT_API_KEY")
    rows: list[manifest.ManifestRow] = []

    print("  [sp] Probing auth...")
    if not dry_run:
        auth_headers = _probe_auth(sp_key)
    else:
        auth_headers = {}

    # --- events ---
    key = _r2_key("events", "events.json", run_id)
    print(f"  [sp] {'DRY-RUN ' if dry_run else ''}events -> {key}")
    if dry_run:
        rows.append(manifest.ManifestRow(run_id=run_id, source_name="sportspredict",
            entity_name="events", source_url=f"{_BASE}/events",
            r2_key=key, r2_uri=r2.r2_uri(key), status="dry_run"))
    elif not manifest.already_uploaded(key):
        events = _get(f"{_BASE}/events", auth_headers)
        data = json.dumps(events, ensure_ascii=False).encode()
        n = r2.upload_bytes(key, data, "application/json")
        row = manifest.ManifestRow(run_id=run_id, source_name="sportspredict",
            entity_name="events", source_url=f"{_BASE}/events",
            r2_key=key, r2_uri=r2.r2_uri(key), bytes_uploaded=n,
            row_count_if_known=len(events) if isinstance(events, list) else -1)
        manifest.append_row(row)
        rows.append(row)
        print(f"    uploaded {n:,} bytes, {row.row_count_if_known} events")
    else:
        print("    skipped (already uploaded)")

    # --- lobbies + matches + markets ---
    if not dry_run:
        events_list = _get(f"{_BASE}/events", auth_headers)
        if not isinstance(events_list, list):
            events_list = events_list.get("data", []) if isinstance(events_list, dict) else []
    else:
        events_list = [{"id": "DRY_EVENT_ID"}]

    for event in events_list:
        event_id = event.get("id") or event.get("event_id")
        if not event_id:
            continue

        # lobbies
        lobby_url = f"{_BASE}/events/{event_id}/lobbies"
        lkey = _r2_key("lobbies", f"lobbies_{event_id}.json", run_id)
        print(f"  [sp] {'DRY-RUN ' if dry_run else ''}lobbies/{event_id} -> {lkey}")
        if dry_run:
            rows.append(manifest.ManifestRow(run_id=run_id, source_name="sportspredict",
                entity_name="lobbies", source_url=lobby_url,
                r2_key=lkey, r2_uri=r2.r2_uri(lkey), status="dry_run"))
            lobbies = [{"id": "DRY_LOBBY_ID"}]
        elif not manifest.already_uploaded(lkey):
            try:
                lobbies = _get(lobby_url, auth_headers)
            except requests.HTTPError:
                lobbies = _get(f"{_BASE}/lobbies", auth_headers, {"event_id": event_id})
            if not isinstance(lobbies, list):
                lobbies = lobbies.get("data", []) if isinstance(lobbies, dict) else []
            data = json.dumps(lobbies, ensure_ascii=False).encode()
            n = r2.upload_bytes(lkey, data, "application/json")
            row = manifest.ManifestRow(run_id=run_id, source_name="sportspredict",
                entity_name="lobbies", source_url=lobby_url,
                r2_key=lkey, r2_uri=r2.r2_uri(lkey), bytes_uploaded=n,
                row_count_if_known=len(lobbies))
            manifest.append_row(row)
            rows.append(row)
            print(f"    uploaded {n:,} bytes, {len(lobbies)} lobbies")
        else:
            print("    skipped (already uploaded)")
            lobbies = []

        if dry_run:
            lobbies = [{"id": "DRY_LOBBY_ID"}]

        for lobby in (lobbies if not dry_run else [{"id": "DRY_LOBBY_ID"}]):
            lobby_id = lobby.get("id") or lobby.get("lobby_id")
            if not lobby_id:
                continue

            # matches
            match_url = f"{_BASE}/lobbies/{lobby_id}/matches"
            mkey = _r2_key("matches", f"matches_{lobby_id}.json", run_id)
            print(f"  [sp] {'DRY-RUN ' if dry_run else ''}matches/{lobby_id} -> {mkey}")
            if dry_run:
                rows.append(manifest.ManifestRow(run_id=run_id, source_name="sportspredict",
                    entity_name="matches", source_url=match_url,
                    r2_key=mkey, r2_uri=r2.r2_uri(mkey), status="dry_run"))
                matches = [{"id": "DRY_MATCH_ID"}]
            elif not manifest.already_uploaded(mkey):
                matches = _paginate(match_url, auth_headers)
                data = json.dumps(matches, ensure_ascii=False).encode()
                n = r2.upload_bytes(mkey, data, "application/json")
                row = manifest.ManifestRow(run_id=run_id, source_name="sportspredict",
                    entity_name="matches", source_url=match_url,
                    r2_key=mkey, r2_uri=r2.r2_uri(mkey), bytes_uploaded=n,
                    row_count_if_known=len(matches))
                manifest.append_row(row)
                rows.append(row)
                print(f"    uploaded {n:,} bytes, {len(matches)} matches")
            else:
                print("    skipped (already uploaded)")
                matches = []

            if dry_run:
                matches = [{"id": "DRY_MATCH_ID"}]

            for match in (matches[:3] if dry_run else matches):
                match_id = match.get("id") or match.get("match_id")
                if not match_id:
                    continue
                market_url = f"{_BASE}/matches/{match_id}/markets"
                mkkey = _r2_key("markets", f"markets_{match_id}.json", run_id)
                if dry_run:
                    print(f"  [sp] DRY-RUN markets/{match_id} -> {mkkey}")
                    rows.append(manifest.ManifestRow(run_id=run_id, source_name="sportspredict",
                        entity_name="markets", source_url=market_url,
                        r2_key=mkkey, r2_uri=r2.r2_uri(mkkey), status="dry_run"))
                elif not manifest.already_uploaded(mkkey):
                    markets = _paginate(market_url, auth_headers)
                    data = json.dumps(markets, ensure_ascii=False).encode()
                    n = r2.upload_bytes(mkkey, data, "application/json")
                    row = manifest.ManifestRow(run_id=run_id, source_name="sportspredict",
                        entity_name="markets", source_url=market_url,
                        r2_key=mkkey, r2_uri=r2.r2_uri(mkkey), bytes_uploaded=n,
                        row_count_if_known=len(markets))
                    manifest.append_row(row)
                    rows.append(row)
                    if len(matches) <= 5 or matches.index(match) % 10 == 0:
                        print(f"    [{match_id}] {n:,} bytes, {len(markets)} markets")
                else:
                    pass  # skip silently for match-level files

    print(f"  [sp] done — {len(rows)} manifest rows")
    return rows
