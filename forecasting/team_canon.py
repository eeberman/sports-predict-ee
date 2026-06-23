"""
Canonical team naming + WC2026 roster reconciliation for the extended team-rate pool.

The live engine (`team_loo_rates`) keys teams on the StatsBomb spelling that appears
in `outputs/backtest_features.csv`. New sources (API-Football, Sofascore) use their own
spellings. This module:
  - `canon(name)`     → maps any source spelling to the canonical StatsBomb name
  - `pool_teams()`    → teams already usable in the pool (>= MIN_GAMES games)
  - `wc2026_teams()`  → the 2026 World Cup roster (from the SportsPredict FIFA map)
  - `missing_teams()` → WC2026 roster minus usable pool teams = the fetch list
  - `priority_teams()`→ same list but with today's match teams pulled to the front,
                        so a budget-capped fetch still covers tonight's fixtures.
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from sportspredict_inventory import config as spc

ROOT = Path(__file__).resolve().parents[2]
FEATURES = ROOT / "outputs" / "backtest_features.csv"

MIN_GAMES = 4

# Source spelling (lower-cased) → canonical StatsBomb name.
# Only divergent spellings need an entry; identical names pass through unchanged.
_ALIAS: dict[str, str] = {
    "korea republic": "South Korea",
    "republic of korea": "South Korea",
    "usa": "United States",
    "united states of america": "United States",
    "ir iran": "Iran",
    "iran islamic republic": "Iran",
    "czech republic": "Czechia",
    "turkey": "Türkiye",
    "turkiye": "Türkiye",
    "côte d'ivoire": "Ivory Coast",
    "cote d'ivoire": "Ivory Coast",
    "dr congo": "DR Congo",
    "congo dr": "DR Congo",
    "democratic republic of congo": "DR Congo",
    "cape verde islands": "Cape Verde",
    "bosnia": "Bosnia and Herzegovina",
    "bosnia & herzegovina": "Bosnia and Herzegovina",
    "curacao": "Curaçao",
}


def canon(name: str) -> str:
    """Map any source spelling to the canonical StatsBomb name used by the engine."""
    if not name:
        return ""
    key = name.strip().lower()
    return _ALIAS.get(key, name.strip())


def pool_teams(min_games: int = MIN_GAMES) -> set[str]:
    """Teams already usable in the current pool (>= min_games appearances)."""
    cnt: Counter[str] = Counter()
    with open(FEATURES, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            cnt[canon(r["home"])] += 1
            cnt[canon(r["away"])] += 1
    return {t for t, c in cnt.items() if c >= min_games}


def wc2026_teams() -> set[str]:
    """
    The 2026 World Cup roster, canonicalized. Sourced from the SportsPredict FIFA
    code→name map (built from this tournament's actual match names).
    """
    return {canon(v) for v in spc.FIFA_CODE_TO_NAME.values()}


def missing_teams(min_games: int = MIN_GAMES) -> list[str]:
    """WC2026 teams not yet usable in the pool — the fetch list."""
    return sorted(wc2026_teams() - pool_teams(min_games))


# Missing teams playing on 2026-06-22 (ARG-AUT, FRA-IRQ, NOR-SEN, JOR-ALG):
# Argentina/France/Senegal are already in the pool, so only these five need fetching.
TODAY_MISSING_2026_06_22 = ["Austria", "Iraq", "Norway", "Jordan", "Algeria"]


def priority_teams(slate_teams: list[str] | None = None, min_games: int = MIN_GAMES) -> list[str]:
    """
    Fetch list with today's match teams first. `slate_teams` are canonical names of
    teams playing today; any that are in the missing set lead, the rest follow sorted.
    Defaults to the 2026-06-22 slate.
    """
    missing = set(missing_teams(min_games))
    front_src = slate_teams if slate_teams is not None else TODAY_MISSING_2026_06_22
    front = [canon(t) for t in front_src if canon(t) in missing]
    rest = sorted(missing - set(front))
    return front + rest


if __name__ == "__main__":
    pool = pool_teams()
    print(f"pool teams (>= {MIN_GAMES} games): {len(pool)}")
    print(f"WC2026 roster: {len(wc2026_teams())}")
    miss = missing_teams()
    print(f"missing ({len(miss)}): {miss}")
    print(f"priority (today first): {priority_teams()}")
