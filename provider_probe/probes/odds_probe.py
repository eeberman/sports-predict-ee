"""
Probe The Odds API for market coverage.
"""

from __future__ import annotations

import time

from .. import config
from ..clients import the_odds_api as client
from . import ProbeResult

# Standard market keys to test individually
STANDARD_MARKET_KEYS = ["h2h", "totals", "spreads", "btts"]
PLAYER_MARKET_KEYS = ["player_shots_on_target", "player_goal_scorer_anytime"]


def _try_market(sport_key: str, market: str) -> bool:
    """Try a single market for a sport; return True if server accepts it."""
    try:
        time.sleep(1)
        events = client.get_odds(sport_key, regions="eu", markets=market)
        return True  # 200 means accepted (may still return 0 events)
    except Exception as exc:
        msg = str(exc)
        if "422" in msg or "400" in msg:
            return False
        # Other errors (5xx, timeout) — treat as accepted but failed
        return False


def run() -> ProbeResult:
    key_present = bool(config.ODDS_API_KEY)
    if not key_present:
        print("  [odds] ODDS_API_KEY missing — skipping")
        return ProbeResult(
            provider="the_odds_api",
            data_area="odds",
            status="skipped",
            api_key_present=False,
            notes="ODDS_API_KEY not configured",
        )

    print("  [odds] Fetching available sports...")
    try:
        sports = client.get_sports()
    except Exception as exc:
        return ProbeResult(
            provider="the_odds_api",
            data_area="odds",
            status="error",
            api_key_present=True,
            notes=f"get_sports() failed: {exc}",
        )

    soccer_sports = [s for s in sports if "soccer" in s.get("key", "")]
    print(f"  [odds] {len(soccer_sports)} soccer sports in catalogue")

    # Save sports list
    sample_path = client.save_sample(soccer_sports, "the_odds_api_sports.json")

    # Find a usable sport key
    sport_key = client.find_active_sport_key()
    if not sport_key and soccer_sports:
        sport_key = soccer_sports[0]["key"]

    fields_found: list[str] = []
    fields_missing: list[str] = []
    notes_parts: list[str] = []
    odds_sample_path: str | None = str(sample_path)

    if not sport_key:
        return ProbeResult(
            provider="the_odds_api",
            data_area="odds",
            status="error",
            api_key_present=True,
            notes="No soccer sport key found in catalogue",
            raw_sample_path=str(sample_path),
        )

    print(f"  [odds] Testing sport_key={sport_key}")

    # Test each standard market individually to pinpoint which are accepted
    accepted_markets: list[str] = []
    for market in STANDARD_MARKET_KEYS:
        print(f"  [odds]   trying market={market}...", end=" ")
        ok = _try_market(sport_key, market)
        if ok:
            accepted_markets.append(market)
            fields_found.append(market)
            print("accepted")
        else:
            fields_missing.append(market)
            print("rejected (422/400)")

    notes_parts.append(f"sport_key={sport_key}, accepted_markets={accepted_markets}")

    # Now fetch one event sample with all accepted markets to inspect structure
    if accepted_markets:
        try:
            time.sleep(1)
            combined = ",".join(accepted_markets)
            events = client.get_odds(sport_key, regions="eu", markets=combined)
            truncated = events[:2] if events else events
            odds_path = client.save_sample(truncated, f"the_odds_api_{sport_key}_odds.json")
            odds_sample_path = str(odds_path)

            if events:
                event = events[0]
                print(f"  [odds] Sample event: {event.get('away_team')} vs {event.get('home_team')}")

                bookmakers = event.get("bookmakers", [])
                if bookmakers:
                    fields_found.append("bookmaker_name")
                    mkts = bookmakers[0].get("markets", [])
                    if mkts:
                        outcomes = mkts[0].get("outcomes", [])
                        if outcomes and "price" in outcomes[0]:
                            fields_found.append("implied_probability")

                if event.get("commence_time"):
                    fields_found.append("timestamps")

                notes_parts.append(f"{len(events)} events, {len(bookmakers)} bookmakers in sample")
            else:
                notes_parts.append(f"sport_key={sport_key} returned 0 events (may be off-season or future tournament)")

        except Exception as exc:
            notes_parts.append(f"combined odds fetch failed: {exc}")

    # Test player props (US region, common for these markets)
    print("  [odds] Checking player prop markets...")
    for pm in PLAYER_MARKET_KEYS:
        ok = _try_market(sport_key, pm)
        if ok:
            fields_found.append(pm)
        else:
            fields_missing.append(pm)
        print(f"  [odds]   player market {pm}: {'accepted' if ok else 'rejected'}")

    # Try a broader set of sports if the first key had few accepted markets
    if len(accepted_markets) < 2:
        notes_parts.append(
            "Few markets accepted for this sport key. "
            "The World Cup 2026 odds may not be active yet (tournament is future). "
            "Expected market availability: h2h and totals should work when odds are live; "
            "btts and spreads availability depends on bookmaker/region."
        )

    status = "ok" if len(fields_found) >= 3 else ("partial" if fields_found else "error")

    return ProbeResult(
        provider="the_odds_api",
        data_area="odds",
        status=status,
        api_key_present=True,
        fields_found=fields_found,
        fields_missing=fields_missing,
        notes="; ".join(notes_parts),
        raw_sample_path=odds_sample_path,
    )
