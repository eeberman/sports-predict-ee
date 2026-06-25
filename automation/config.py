"""Configuration constants for SportsPredict email automation."""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = REPO_ROOT / "automation_state"
SNAPSHOT_DIR = STATE_DIR / "match_snapshots"
SENT_EMAILS_PATH = STATE_DIR / "sent_emails.json"
OUTPUT_DIR = REPO_ROOT / "outputs" / "automation"

SEND_WINDOW_START_MIN = 65
SEND_WINDOW_END_MIN = 50
LOOKAHEAD_HOURS = 2

SECOND_HALF_GOAL_SHARE = 0.53
SECOND_HALF_SOT_SHARE = 0.53
SECOND_HALF_CARD_SHARE = 0.58
BTTS_NOT_1_1_FACTOR = 0.79
ONE_SIDED_PROP_HAIRCUT_PCT = 4.0
MISSING_PLAYER_SOT_FALLBACK_PCT = 15

TRUSTED_BOOKS = (
    "pinnacle",
    "fanduel",
    "draftkings",
    "betmgm",
    "betrivers",
    "bovada",
    "williamhill_us",
    "caesars",
)

PROP_BOOK_PRIORITY = ("fanduel", "betrivers", "draftkings")

ODDS_REGIONS = os.environ.get("ODDS_REGIONS", "us,eu,uk")

ODDS_MARKET_CHUNKS = (
    "h2h,totals,spreads",
    "btts",
    "alternate_totals",
    "team_totals",
    "alternate_team_totals",
    "h2h_h1",
    "totals_h1",
    "team_shots_on_target",
    "player_shots_on_target",
    "player_goal_scorer_anytime",
)
