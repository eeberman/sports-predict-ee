"""Configuration for raw landing. Secret values are never printed."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(DEFAULT_ENV_PATH)

OUTPUTS = PROJECT_ROOT / "outputs"
LOGS = OUTPUTS / "logs"
SAMPLES = OUTPUTS / "samples"
MANIFEST_PATH = PROJECT_ROOT / "raw_manifest.csv"

_ALIASES: dict[str, tuple[str, ...]] = {
    "R2_ENDPOINT_URL": ("R2_ENDPOINT_URL", "s3_api"),
    "AWS_ACCESS_KEY_ID": ("AWS_ACCESS_KEY_ID", "R2_ACCESS_KEY_ID"),
    "AWS_SECRET_ACCESS_KEY": ("AWS_SECRET_ACCESS_KEY", "R2_SECRET_ACCESS_KEY"),
    "AWS_REGION": ("AWS_REGION",),
}

R2_REQUIRED = [
    "R2_BUCKET",
    "R2_ACCOUNT_ID",
    "R2_ENDPOINT_URL",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
]
SP_REQUIRED = ["SPORTSPREDICT_API_KEY"]


class ConfigError(RuntimeError):
    pass


def load_env_file(path: str | Path) -> Path:
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file():
        raise ConfigError(f"Environment file not found: {resolved}")
    load_dotenv(resolved, override=True)
    return resolved


def get(key: str, default: str = "") -> str:
    if key == "AWS_REGION":
        default = default or "auto"
    for candidate in _ALIASES.get(key, (key,)):
        value = os.environ.get(candidate, "").strip()
        if value:
            return value
    return default


def _check_keys(keys: list[str]) -> list[str]:
    missing: list[str] = []
    for key in keys:
        present = bool(get(key))
        print(f"  {key}: {'present' if present else 'MISSING'}")
        if not present:
            missing.append(key)
    return missing


def validate_r2() -> None:
    print("R2 credentials:")
    missing = _check_keys(R2_REQUIRED)
    print(f"  AWS_REGION: {'present' if get('AWS_REGION') else 'MISSING'}")
    if missing:
        raise ConfigError(f"Missing required R2 env vars: {missing}")


def validate_sportspredict() -> None:
    print("SportsPredict credentials:")
    missing = _check_keys(SP_REQUIRED)
    if missing:
        raise ConfigError(f"Missing required SportsPredict env vars: {missing}")


def validate_all() -> None:
    validate_r2()
    print("Optional:")
    for key in ["SPORTSPREDICT_API_KEY", "API_FOOTBALL_KEY", "ODDS_API_KEY", "MOTHERDUCK_TOKEN"]:
        print(f"  {key}: {'present' if get(key) else 'not set (OK)'}")
