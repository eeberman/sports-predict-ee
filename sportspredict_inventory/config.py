import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.sportspredict.com/api/v1"

REPO_ROOT = Path(__file__).parent.parent
DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_RAW_MARKETS = DATA_RAW / "markets_by_match"
DATA_PROCESSED = REPO_ROOT / "data" / "processed"
REPORTS = REPO_ROOT / "reports"

MAX_RETRIES = 5
BACKOFF_BASE = 1.5
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
REQUEST_TIMEOUT = 30
MIN_REQUEST_INTERVAL = 0.25

PROBABILITY_CUP_KEYWORD = "probability cup"

# FIFA 3-letter code → full English team name used in question text.
# Built from the actual match names found in this tournament.
FIFA_CODE_TO_NAME: dict[str, str] = {
    "TUN": "Tunisia",
    "JPN": "Japan",
    "ESP": "Spain",
    "KSA": "Saudi Arabia",
    "BEL": "Belgium",
    "IRN": "Iran",
    "URU": "Uruguay",
    "CPV": "Cape Verde",
    "EGY": "Egypt",
    "ARG": "Argentina",
    "AUT": "Austria",
    "FRA": "France",
    "IRQ": "Iraq",
    "NOR": "Norway",
    "SEN": "Senegal",
    "JOR": "Jordan",
    "ALG": "Algeria",
    "POR": "Portugal",
    "UZB": "Uzbekistan",
    "ENG": "England",
    "GHA": "Ghana",
    "PAN": "Panama",
    "CRO": "Croatia",
    "COL": "Colombia",
    "COD": "DR Congo",
    "BIH": "Bosnia and Herzegovina",
    "QAT": "Qatar",
    "SUI": "Switzerland",
    "CAN": "Canada",
    "SCO": "Scotland",
    "BRA": "Brazil",
    "MAR": "Morocco",
    "CZE": "Czechia",
    "MEX": "Mexico",
    "RSA": "South Africa",
    "KOR": "South Korea",
    "ECU": "Ecuador",
    "GER": "Germany",
    "TUR": "Türkiye",
    "USA": "United States",
    "PAR": "Paraguay",
    "AUS": "Australia",
    "SWE": "Sweden",
    "NED": "Netherlands",
    "CIV": "Ivory Coast",
    # Full names that appear directly in match name field
    "New Zealand": "New Zealand",
    "Haiti": "Haiti",
    "Curacao": "Curaçao",
}


def get_api_key() -> str:
    key = os.environ.get("SPORTSPREDICT_API_KEY", "")
    if not key:
        raise ValueError(
            "SPORTSPREDICT_API_KEY is not set. "
            "Copy .env.example to .env and add your key."
        )
    return key
