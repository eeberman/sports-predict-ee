"""The Odds API ingestion and normalized market lookups."""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass
from typing import Any, Iterable

from provider_probe.clients import the_odds_api

from . import config


def norm_name(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


@dataclass(frozen=True)
class PricePoint:
    market: str
    outcome: str
    price: float
    bookmaker: str
    point: float | None = None
    description: str | None = None


class MarketBook:
    def __init__(self, *, home: str, away: str, event: dict | None, prices: list[PricePoint]):
        self.home = home
        self.away = away
        self.event = event
        self.prices = prices

    @property
    def found_event(self) -> bool:
        return self.event is not None

    def complete_market_signature(self) -> str:
        parts = [
            f"{p.market}:{norm_name(p.description)}:{norm_name(p.outcome)}:{p.point}:{p.bookmaker}:{p.price}"
            for p in self.prices
        ]
        return "|".join(sorted(parts))

    def _trusted(self, price: PricePoint) -> bool:
        return price.bookmaker in config.TRUSTED_BOOKS

    def _matching(
        self,
        market: str,
        *,
        outcome: str | None = None,
        point: float | None = None,
        description: str | None = None,
        trusted_only: bool = True,
    ) -> list[PricePoint]:
        rows = [p for p in self.prices if p.market == market]
        if trusted_only:
            rows = [p for p in rows if self._trusted(p)]
        if outcome is not None:
            want = norm_name(outcome)
            rows = [p for p in rows if norm_name(p.outcome) == want]
        if point is not None:
            rows = [p for p in rows if p.point is not None and abs(float(p.point) - float(point)) < 1e-9]
        if description is not None:
            want_desc = norm_name(description)
            rows = [p for p in rows if norm_name(p.description) == want_desc]
        return rows

    def consensus_price(self, market: str, outcome: str, *, point: float | None = None, description: str | None = None) -> float | None:
        rows = self._matching(market, outcome=outcome, point=point, description=description)
        if not rows:
            return None
        return float(statistics.median(p.price for p in rows))

    def preferred_prop_price(self, market: str, outcome: str, *, point: float | None = None, description: str | None = None) -> PricePoint | None:
        rows = self._matching(market, outcome=outcome, point=point, description=description, trusted_only=False)
        if not rows:
            return None
        for book in config.PROP_BOOK_PRIORITY:
            book_rows = [p for p in rows if p.bookmaker == book]
            if book_rows:
                return sorted(book_rows, key=lambda p: p.price, reverse=True)[0]
        trusted_rows = [p for p in rows if self._trusted(p)]
        if trusted_rows:
            return sorted(trusted_rows, key=lambda p: p.price, reverse=True)[0]
        return sorted(rows, key=lambda p: p.price, reverse=True)[0]

    def h2h_prices(self) -> tuple[float, float, float] | None:
        home = self.consensus_price("h2h", self.home)
        draw = self.consensus_price("h2h", "Draw")
        away = self.consensus_price("h2h", self.away)
        if home and draw and away:
            return home, draw, away
        return None

    def two_way_prices(self, market: str, *, point: float | None = None, description: str | None = None) -> tuple[float, float] | None:
        over = self.consensus_price(market, "Over", point=point, description=description)
        under = self.consensus_price(market, "Under", point=point, description=description)
        if over and under:
            return over, under
        yes = self.consensus_price(market, "Yes", point=point, description=description)
        no = self.consensus_price(market, "No", point=point, description=description)
        if yes and no:
            return yes, no
        return None

    def available_points(self, market: str, *, description: str | None = None) -> list[float]:
        rows = self._matching(market, description=description, trusted_only=False)
        points = sorted({float(p.point) for p in rows if p.point is not None})
        return points


def _event_matches(event: dict, home: str, away: str) -> bool:
    event_teams = {norm_name(event.get("home_team")), norm_name(event.get("away_team"))}
    wanted = {norm_name(home), norm_name(away)}
    return event_teams == wanted


def market_book_from_events(events: Iterable[dict], home: str, away: str) -> MarketBook:
    event = next((e for e in events if _event_matches(e, home, away)), None)
    if not event:
        return MarketBook(home=home, away=away, event=None, prices=[])

    # Use caller's home/away names for stable downstream lookups even if the API
    # returns reversed home/away ordering.
    prices: list[PricePoint] = []
    for bookmaker in event.get("bookmakers", []):
        book_key = bookmaker.get("key", "")
        for market in bookmaker.get("markets", []):
            market_key = market.get("key", "")
            for outcome in market.get("outcomes", []):
                name = outcome.get("name") or ""
                if market_key == "h2h":
                    if norm_name(name) == norm_name(event.get("home_team")):
                        name = home if norm_name(event.get("home_team")) == norm_name(home) else away
                    elif norm_name(name) == norm_name(event.get("away_team")):
                        name = away if norm_name(event.get("away_team")) == norm_name(away) else home
                prices.append(
                    PricePoint(
                        market=market_key,
                        outcome=name,
                        price=float(outcome["price"]),
                        bookmaker=book_key,
                        point=outcome.get("point"),
                        description=outcome.get("description"),
                    )
                )
    return MarketBook(home=home, away=away, event=event, prices=prices)


def fetch_odds_for_match(home: str, away: str) -> tuple[MarketBook, dict[str, Any]]:
    raw_events: list[dict] = []
    failures: list[str] = []
    used_sport_keys: list[str] = []
    for sport_key in the_odds_api.SOCCER_SPORT_KEYS:
        for chunk in config.ODDS_MARKET_CHUNKS:
            try:
                events = the_odds_api.get_odds(sport_key, regions=config.ODDS_REGIONS, markets=chunk)
            except Exception as exc:
                failures.append(f"{sport_key} {chunk}: {exc}")
                continue
            raw_events.extend(events)
            used_sport_keys.append(sport_key)
            if any(_event_matches(e, home, away) for e in events):
                # Still try remaining chunks for the same sport key, but skip later sport keys.
                pass
        if any(_event_matches(e, home, away) for e in raw_events):
            break
    book = market_book_from_events(raw_events, home, away)
    meta = {"raw_events": raw_events, "failures": failures, "used_sport_keys": sorted(set(used_sport_keys))}
    return book, meta

