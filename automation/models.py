"""Small value objects shared by the automation runner."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class MatchInfo:
    event_id: str
    lobby_id: str
    match_id: str
    name: str
    home: str
    away: str
    kickoff: datetime


@dataclass
class Decision:
    number: int
    question: str
    prob: int | None
    source_tier: str
    derivation: str
    signature: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

