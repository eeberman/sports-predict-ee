"""
Thin client for StatBunker (statbunker.com) referee statistics pages.
Fetches server-side-rendered HTML only — no JS, no aggressive scraping.
Single request per call; 2-second polite delay between requests.

Correct URL pattern (discovered via exploration):
  https://www.statbunker.com/competitions/RefereeYellowCards?comp_id={id}

Current competition IDs (from homepage as of 2026-06):
  776 = Premier League
  783 = UEFA Champions League
  777 = La Liga
  785 = Serie A
  762 = Bundesliga
"""

from __future__ import annotations

import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from .. import config

BASE_URL = "https://www.statbunker.com"
REFEREE_PATH = "/competitions/RefereeYellowCards"
TIMEOUT = 30
SAMPLE_TRUNCATE = 60_000  # bytes

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.statbunker.com/",
}

# Current competition IDs — Premier League is the most reliably populated
COMP_IDS = [
    (776, "Premier League"),
    (783, "UEFA Champions League"),
    (777, "La Liga"),
    (785, "Serie A"),
]


def fetch_page(url: str) -> requests.Response:
    time.sleep(2)
    session = requests.Session()
    session.max_redirects = 3
    resp = session.get(url, headers=_HEADERS, timeout=TIMEOUT, allow_redirects=True)
    resp.raise_for_status()
    return resp


def get_referee_stats_page(comp_id: int | str) -> str:
    url = f"{BASE_URL}{REFEREE_PATH}?comp_id={comp_id}"
    resp = fetch_page(url)
    resp.encoding = "utf-8"
    return resp.text


def _parse_header_cell(th) -> str:
    """Extract a canonical field name from a <th> using title attr or alt text."""
    title = (th.get("title") or "").lower()
    img = th.find("img")
    if img:
        alt = (img.get("alt") or "").lower()
        if "red and yellow" in alt or "second yellow" in alt:
            return "red_yellow_cards"
        if "yellow card" in alt and "/match" in th.get_text().lower():
            return "yellow_per_match"
        if "yellow card" in alt:
            return "yellow_cards"
        if "red card" in alt:
            return "red_cards"
    if "matches played" in title or th.get_text(strip=True).upper() == "P":
        return "matches"
    if "first half" in title:
        return "fh_cards_avg_minute"
    if "second half" in title:
        return "sh_cards_avg_minute"
    if "home" in title or th.get_text(strip=True).upper() == "H":
        return "home_cards"
    if "away" in title or th.get_text(strip=True).upper() == "A":
        return "away_cards"
    if "cards / match" in title or "cards/match" in th.get_text(strip=True).lower():
        return "cards_per_match"
    raw = th.get_text(strip=True).lower().replace(" ", "_")
    return raw if raw else "unknown"


def parse_referee_table(html: str) -> tuple[list[dict], list[str]]:
    """
    Parse the RefereeYellowCards table.
    Returns (rows, canonical_column_names).

    Column layout (confirmed from live page):
      0: referee_name
      1: matches (P)
      2: fh_cards_avg_minute  (First half cards + avg minute, e.g. "25(31)")
      3: sh_cards_avg_minute  (Second half)
      4: home_cards
      5: away_cards
      6: yellow_cards
      7: red_yellow_cards     (second bookings)
      8: red_cards
      9: yellow_per_match
     10: cards_per_match
     11: (More button — skip)
    """
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    if not tables:
        return [], []

    tbl = tables[0]
    header_row = tbl.find("tr")
    if not header_row:
        return [], []

    raw_headers = list(header_row.find_all(["th", "td"]))
    canonical_cols = ["referee_name"] + [_parse_header_cell(th) for th in raw_headers[1:]]
    # Drop the "More" button column
    if canonical_cols and canonical_cols[-1] in ("more", "unknown", ""):
        canonical_cols = canonical_cols[:-1]

    rows: list[dict] = []
    for tr in tbl.find_all("tr")[1:]:
        cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        if not cells or not cells[0].strip():
            continue
        # Pad / truncate to match header count
        row: dict = {}
        for i, col in enumerate(canonical_cols):
            row[col] = cells[i] if i < len(cells) else ""
        # Parse fh/sh into a numeric card count (strip the average-minute part)
        for key in ("fh_cards_avg_minute", "sh_cards_avg_minute"):
            if key in row:
                raw = row[key]
                m = re.match(r"^(\d+)", raw)
                row[f"{key}_count"] = int(m.group(1)) if m else None
        rows.append(row)

    return rows, canonical_cols


def save_html_sample(html: str, filename: str) -> Path:
    dest_dir = config.RAW_SAMPLES / "referee_sources"
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / filename
    path.write_text(html[:SAMPLE_TRUNCATE], encoding="utf-8", errors="replace")
    return path
