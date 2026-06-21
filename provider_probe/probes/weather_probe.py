"""
Probe Open-Meteo for forecast and historical weather coverage.
"""

from __future__ import annotations

from .. import config
from ..clients import open_meteo as client
from . import ProbeResult

# Test venue: Tunis, Tunisia (TUN vs JPN was our first match)
TEST_LAT = 36.8
TEST_LON = 10.18
TEST_VENUE = "Tunis, Tunisia"

REQUIRED_FIELDS = [
    "temperature_2m",
    "precipitation_probability",
    "windspeed_10m",
    "weathercode",
]


def run() -> ProbeResult:
    print(f"  [weather] Open-Meteo (no key required)")
    print(f"  [weather] Test venue: {TEST_VENUE} ({TEST_LAT}, {TEST_LON})")

    fields_found: list[str] = []
    fields_missing: list[str] = []
    notes_parts: list[str] = []
    raw_path: str | None = None

    # Forecast test
    print("  [weather] Fetching forecast...")
    try:
        forecast = client.get_forecast(
            lat=TEST_LAT,
            lon=TEST_LON,
            start_date="2026-06-20",
            end_date="2026-06-22",
        )
        raw_path = str(client.save_sample(forecast, "open_meteo_forecast.json"))

        hourly = forecast.get("hourly", {})
        for field in REQUIRED_FIELDS:
            if field in hourly:
                fields_found.append(f"forecast_{field}")
            else:
                fields_missing.append(f"forecast_{field}")

        hour_count = len(hourly.get("time", []))
        tz = forecast.get("timezone", "unknown")
        notes_parts.append(f"forecast: {hour_count} hourly rows, timezone={tz}")

    except Exception as exc:
        notes_parts.append(f"forecast failed: {exc}")
        fields_missing.extend([f"forecast_{f}" for f in REQUIRED_FIELDS])

    # Historical test
    print("  [weather] Fetching historical actuals...")
    try:
        historical = client.get_historical(
            lat=TEST_LAT,
            lon=TEST_LON,
            start_date="2025-06-01",
            end_date="2025-06-02",
        )
        client.save_sample(historical, "open_meteo_historical.json")

        hourly = historical.get("hourly", {})
        for field in REQUIRED_FIELDS:
            hist_field = f"historical_{field}"
            if field in hourly:
                fields_found.append(hist_field)
            else:
                fields_missing.append(hist_field)

        hour_count = len(hourly.get("time", []))
        notes_parts.append(f"historical: {hour_count} hourly rows")

    except Exception as exc:
        notes_parts.append(f"historical failed: {exc}")
        fields_missing.extend([f"historical_{f}" for f in REQUIRED_FIELDS])

    # Record the coordinate dependency
    notes_parts.append(
        "DEPENDENCY: Open-Meteo requires lat/lon per venue. "
        "API-Football fixture.venue.city can supply city name; "
        "lat/lon must be resolved via a geocoder or a manual venue->coordinate table. "
        "Open-Meteo does not accept venue names."
    )

    status = "ok" if not fields_missing else ("partial" if fields_found else "error")

    return ProbeResult(
        provider="open_meteo",
        data_area="weather",
        status=status,
        api_key_present=True,  # no key needed
        fields_found=fields_found,
        fields_missing=fields_missing,
        notes="; ".join(notes_parts),
        raw_sample_path=raw_path,
    )
