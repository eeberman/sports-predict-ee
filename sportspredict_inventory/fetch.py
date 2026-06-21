"""
python -m sportspredict_inventory.fetch [--force]

Fetches all Probability Cup data from the SportsPredict API and saves
raw JSON to data/raw/. Safe to re-run: existing per-match market files
are skipped unless --force is passed.
"""

import argparse
import json
import sys
import time
from pathlib import Path

from . import config
from .client import SportsPredictClient


def _save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_id(v) -> str:
    return str(v) if v is not None else ""


def _find_probability_cup_event(events_data) -> dict:
    if isinstance(events_data, list):
        candidates = events_data
    elif isinstance(events_data, dict):
        candidates = (
            events_data.get("data")
            or events_data.get("events")
            or events_data.get("results")
            or []
        )
        if not candidates:
            candidates = [events_data]
    else:
        candidates = []

    keyword = config.PROBABILITY_CUP_KEYWORD.lower()
    matches = [
        e for e in candidates
        if isinstance(e, dict)
        and keyword in (e.get("title") or e.get("name") or "").lower()
    ]

    if not matches:
        titles = [e.get("title") or e.get("name") or str(e.get("id")) for e in candidates]
        print("ERROR: No 'Probability Cup' event found. Available events:")
        for t in titles:
            print(f"  - {t}")
        sys.exit(1)

    if len(matches) > 1:
        print(f"WARNING: {len(matches)} events matched 'probability cup'. Using the first.")

    return matches[0]


def _find_lobby(lobbies_data) -> dict:
    if isinstance(lobbies_data, list):
        candidates = lobbies_data
    elif isinstance(lobbies_data, dict):
        candidates = (
            lobbies_data.get("data")
            or lobbies_data.get("lobbies")
            or lobbies_data.get("results")
            or []
        )
        if not candidates:
            candidates = [lobbies_data]
    else:
        candidates = []

    if not candidates:
        print("ERROR: No lobbies found for this event.")
        sys.exit(1)

    return candidates[0]


def _is_already_joined(lobby: dict) -> bool:
    for field in ("joined", "member", "is_member", "is_joined"):
        v = lobby.get(field)
        if v is True:
            return True
    status = lobby.get("participation_status") or lobby.get("membership_status") or ""
    return status.lower() in ("active", "joined", "member", "participating")


def _get_match_list(matches_data) -> list:
    if isinstance(matches_data, list):
        return matches_data
    if isinstance(matches_data, dict):
        for key in ("data", "matches", "results", "items"):
            if key in matches_data and isinstance(matches_data[key], list):
                return matches_data[key]
    return []


def _get_market_list(markets_data) -> list:
    if isinstance(markets_data, list):
        return markets_data
    if isinstance(markets_data, dict):
        for key in ("data", "markets", "results", "items", "questions"):
            if key in markets_data and isinstance(markets_data[key], list):
                return markets_data[key]
    return []


def main(force: bool = False) -> None:
    for path in [config.DATA_RAW, config.DATA_RAW_MARKETS, config.DATA_PROCESSED, config.REPORTS]:
        path.mkdir(parents=True, exist_ok=True)

    api_key = config.get_api_key()
    client = SportsPredictClient(api_key)

    # ── Step 1: Events ────────────────────────────────────────────────────────
    print("Step 1: Fetching events...")
    try:
        events_data = client.get("/events")
    except Exception as exc:
        print(f"  ERROR fetching /events: {exc}")
        sys.exit(1)
    _save_json(config.DATA_RAW / "events.json", events_data)
    print(f"  Saved events.json")

    event = _find_probability_cup_event(events_data)
    event_id = _normalize_id(event.get("id"))
    event_title = event.get("title") or event.get("name") or event_id
    print(f"  Found event: '{event_title}' (id={event_id})")

    # ── Step 2: Lobbies ───────────────────────────────────────────────────────
    print("Step 2: Fetching lobbies...")
    lobbies_data = None
    for endpoint in (f"/events/{event_id}/lobbies", "/lobbies"):
        params = {} if "events" in endpoint else {"event_id": event_id}
        try:
            lobbies_data = client.get(endpoint, params=params)
            break
        except Exception as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status == 404:
                print(f"  {endpoint} → 404, trying fallback")
                continue
            print(f"  ERROR: {exc}")
            sys.exit(1)

    if lobbies_data is None:
        print("ERROR: Could not fetch lobbies from any endpoint.")
        sys.exit(1)

    _save_json(config.DATA_RAW / "lobbies.json", lobbies_data)
    print("  Saved lobbies.json")

    lobby = _find_lobby(lobbies_data)
    lobby_id = _normalize_id(lobby.get("id"))
    print(f"  Found lobby: '{lobby.get('name') or lobby_id}' (id={lobby_id})")

    # ── Step 3: Join lobby if needed ──────────────────────────────────────────
    print("Step 3: Checking lobby membership...")
    if _is_already_joined(lobby):
        print("  Already joined — skipping join.")
    else:
        # First try to fetch markets without joining; join only if we get 403
        print("  Not joined; will attempt join before fetching markets if needed.")

    # ── Step 4: Matches ───────────────────────────────────────────────────────
    print("Step 4: Fetching matches...")
    matches: list = []
    for endpoint in (f"/lobbies/{lobby_id}/matches", "/matches"):
        params = {} if "lobbies" in endpoint else {"lobby_id": lobby_id}
        try:
            raw = client.get_paginated(endpoint, params=params)
            if raw:
                matches = raw
                break
        except Exception as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status == 403:
                # Need to join first
                print("  Got 403 — attempting lobby join...")
                join_resp = client.post(f"/lobbies/{lobby_id}/join")
                if join_resp.status_code in (200, 201, 204, 409):
                    print("  Joined (or already joined). Retrying matches...")
                    try:
                        raw = client.get_paginated(endpoint, params=params)
                        matches = raw
                        break
                    except Exception as exc2:
                        print(f"  ERROR after join: {exc2}")
                        continue
                else:
                    print(f"  Join failed: {join_resp.status_code} {join_resp.text[:200]}")
                    continue
            elif status == 404:
                print(f"  {endpoint} → 404, trying fallback")
                continue
            else:
                print(f"  ERROR: {exc}")
                continue

    if not matches:
        print("ERROR: Could not retrieve any matches.")
        sys.exit(1)

    _save_json(config.DATA_RAW / "matches.json", matches)
    print(f"  Found {len(matches)} matches. Saved matches.json")

    # ── Step 5: Markets per match ─────────────────────────────────────────────
    print("Step 5: Fetching markets for each match...")
    total = len(matches)
    fetched = 0
    skipped = 0
    errors = 0

    for i, match in enumerate(matches, 1):
        match_id = _normalize_id(match.get("id"))
        match_name = (
            match.get("name")
            or f"{match.get('home_team', '?')} vs {match.get('away_team', '?')}"
        )
        out_path = config.DATA_RAW_MARKETS / f"{match_id}.json"

        if out_path.exists() and not force:
            skipped += 1
            continue

        print(f"  [{i}/{total}] {match_name} (id={match_id})")

        markets: list = []
        for endpoint in (f"/matches/{match_id}/markets", "/markets"):
            params = {} if "matches" in endpoint else {"match_id": match_id}
            try:
                raw = client.get_paginated(endpoint, params=params)
                markets = raw
                break
            except Exception as exc:
                status = getattr(getattr(exc, "response", None), "status_code", None)
                if status == 404:
                    continue
                print(f"    WARNING: {exc}")
                break

        if markets:
            _save_json(out_path, markets)
            fetched += 1
        else:
            print(f"    WARNING: no markets found for match {match_id}")
            errors += 1

        time.sleep(config.MIN_REQUEST_INTERVAL)

    print(f"\nDone. Fetched: {fetched}, Skipped (cached): {skipped}, Errors: {errors}")
    print(f"Raw data saved to: {config.DATA_RAW}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch SportsPredict Probability Cup markets")
    parser.add_argument("--force", action="store_true", help="Re-fetch even if cached")
    args = parser.parse_args()
    main(force=args.force)
