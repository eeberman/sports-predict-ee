"""
Thin client for Open-Meteo (no API key required).
"""

from __future__ import annotations

import json
from pathlib import Path

import requests

from .. import config

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
TIMEOUT = 30

HOURLY_VARS = "temperature_2m,precipitation_probability,windspeed_10m,weathercode"


def _get(url: str, params: dict) -> dict:
    resp = requests.get(url, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def ping() -> dict:
    try:
        data = get_forecast(lat=36.8, lon=10.18, start_date="2026-06-20", end_date="2026-06-21")
        hours = len(data.get("hourly", {}).get("time", []))
        return {"status": "ok", "message": f"Open-Meteo responsive, {hours} hourly rows returned"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def get_forecast(lat: float, lon: float, start_date: str, end_date: str) -> dict:
    return _get(FORECAST_URL, {
        "latitude": lat,
        "longitude": lon,
        "hourly": HOURLY_VARS,
        "timezone": "auto",
        "start_date": start_date,
        "end_date": end_date,
    })


def get_historical(lat: float, lon: float, start_date: str, end_date: str) -> dict:
    return _get(ARCHIVE_URL, {
        "latitude": lat,
        "longitude": lon,
        "hourly": HOURLY_VARS,
        "timezone": "auto",
        "start_date": start_date,
        "end_date": end_date,
    })


def save_sample(data, filename: str) -> Path:
    config.RAW_SAMPLES.mkdir(parents=True, exist_ok=True)
    path = config.RAW_SAMPLES / filename
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
