"""SportsPredict fetch and match normalization for automation."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from provider_probe.clients.sportspredict import _tool
from sportspredict_inventory import config as sp_config
from sportspredict_inventory.normalize import normalize_market

from .models import MatchInfo


def split_match_name(name: str) -> tuple[str, str]:
    home_raw, away_raw = (name.split(" vs ", 1) + [""])[:2]
    mapping = sp_config.FIFA_CODE_TO_NAME
    home = mapping.get(home_raw.strip(), home_raw.strip())
    away = mapping.get(away_raw.strip(), away_raw.strip())
    return home, away


def fetch_probability_cup_matches() -> list[MatchInfo]:
    events = json.loads(_tool("list_events", {}))
    pc = [e for e in events if "probability cup" in (e.get("title") or e.get("name") or "").lower()]
    event = pc[0] if pc else events[0]
    event_id = event["id"]

    lobbies = json.loads(_tool("list_lobbies", {"event_id": event_id}))
    lobby_id = lobbies[0]["id"]
    try:
        _tool("join_lobby", {"lobby_id": lobby_id})
    except Exception:
        pass

    raw_matches = json.loads(_tool("list_matches", {"event_id": event_id, "lobby_id": lobby_id}))
    matches: list[MatchInfo] = []
    for raw in raw_matches:
        kickoff_raw = raw.get("opening_time") or raw.get("kickoff") or ""
        try:
            kickoff = datetime.fromisoformat(kickoff_raw.replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            continue
        home, away = split_match_name(raw.get("name", ""))
        matches.append(
            MatchInfo(
                event_id=event_id,
                lobby_id=lobby_id,
                match_id=raw["id"],
                name=raw.get("name", ""),
                home=home,
                away=away,
                kickoff=kickoff,
            )
        )
    return sorted(matches, key=lambda m: m.kickoff)


def fetch_questions(match: MatchInfo) -> list[dict]:
    raw_markets = json.loads(_tool("list_markets", {"lobby_id": match.lobby_id, "match_id": match.match_id}))
    questions = []
    for index, market in enumerate(raw_markets, 1):
        question = market.get("question") or market.get("title") or market.get("name") or ""
        normalized = normalize_market({"question": question}, {"home_team": match.home, "away_team": match.away})
        normalized["home_team"] = match.home
        normalized["away_team"] = match.away
        normalized["raw_question"] = question
        questions.append(
            {
                "number": index,
                "market_id": market.get("id"),
                "question": question,
                "normalized": normalized,
            }
        )
    return questions

