"""
Provider probe configuration.
Loads environment variables from .env; exposes path constants and a key_present() helper.
Never prints secret values — only presence/absence.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[2]
# The populated .env lives at the project root; load a local copy first if present,
# then the project-root .env (load_dotenv does not override already-set vars).
load_dotenv(REPO_ROOT / ".env")
load_dotenv(PROJECT_ROOT / ".env")

# Provider keys (never printed directly)
ODDS_API_KEY: str = os.environ.get("ODDS_API_KEY", "")
ODDS_PROVIDER: str = os.environ.get("ODDS_PROVIDER", "the_odds_api")

FOOTBALL_DATA_PROVIDER: str = os.environ.get("FOOTBALL_DATA_PROVIDER", "api_football")
FOOTBALL_DATA_API_KEY: str = os.environ.get("FOOTBALL_DATA_API_KEY", "")

WEATHER_PROVIDER: str = os.environ.get("WEATHER_PROVIDER", "open_meteo")

SPORTMONKS_API_KEY: str = os.environ.get("SPORTMONKS_API_KEY", "")
REFEREE_DATA_PROVIDER: str = os.environ.get("REFEREE_DATA_PROVIDER", "")

SPORTSPREDICT_API_KEY: str = os.environ.get("SPORTSPREDICT_API_KEY", "")

# Output paths
OUTPUTS = REPO_ROOT / "outputs"
RAW_SAMPLES = OUTPUTS / "raw_samples"
TAXONOMY_PATH = REPO_ROOT / "data" / "processed" / "question_templates.csv"

# All known secret values — used by redact() to scrub saved samples
_SECRETS: list[str] = [
    v for v in [
        ODDS_API_KEY, FOOTBALL_DATA_API_KEY, SPORTSPREDICT_API_KEY, SPORTMONKS_API_KEY
    ] if v
]


def key_present(name: str) -> bool:
    val = os.environ.get(name, "")
    status = "present" if val else "missing"
    print(f"  {name}: {status}")
    return bool(val)


def redact(text: str) -> str:
    for secret in _SECRETS:
        if secret and secret in text:
            text = text.replace(secret, "[REDACTED]")
    return text
