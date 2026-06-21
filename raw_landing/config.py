"""
Configuration and environment validation for raw_landing.
Never prints secret values — only "present" or "MISSING".
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
OUTPUTS = Path("outputs")
LOGS = OUTPUTS / "logs"
SAMPLES = OUTPUTS / "samples"
MANIFEST_PATH = Path("raw_manifest.csv")

# ---------------------------------------------------------------------------
# Required env vars
# ---------------------------------------------------------------------------
R2_REQUIRED = [
    "R2_BUCKET",
    "R2_ACCOUNT_ID",
    "CLOUDFLARE_API_TOKEN",
]

SP_REQUIRED = ["SPORTSPREDICT_API_KEY"]


class ConfigError(RuntimeError):
    pass


def get(key: str) -> str:
    return os.environ.get(key, "")


def _check_keys(keys: list[str]) -> list[str]:
    missing = []
    for k in keys:
        present = bool(os.environ.get(k, "").strip())
        status = "present" if present else "MISSING"
        print(f"  {k}: {status}")
        if not present:
            missing.append(k)
    return missing


def validate_r2() -> None:
    print("R2 credentials:")
    missing = _check_keys(R2_REQUIRED)
    if missing:
        raise ConfigError(f"Missing required R2 env vars: {missing}")


def validate_sportspredict() -> None:
    print("SportsPredict credentials:")
    missing = _check_keys(SP_REQUIRED)
    if missing:
        raise ConfigError(f"Missing required SportsPredict env vars: {missing}")


def validate_all() -> None:
    validate_r2()
    validate_sportspredict()
    print("Optional (not used in this task):")
    for k in ["API_FOOTBALL_KEY", "ODDS_API_KEY", "MOTHERDUCK_TOKEN"]:
        v = os.environ.get(k, "")
        print(f"  {k}: {'present' if v.strip() else 'not set (OK)'}")
