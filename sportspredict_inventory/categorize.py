"""
python -m sportspredict_inventory.categorize

Reads raw JSON from data/raw/, applies question normalization, and writes:
  data/processed/markets_inventory.csv
  data/processed/question_templates.csv

Also prints counts by match and by question family.
"""

import json
from pathlib import Path

import pandas as pd

from . import config
from .normalize import normalize_market


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_id(v) -> str:
    return str(v) if v is not None else ""


def _extract_list(data, *keys) -> list:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in keys:
            if k in data and isinstance(data[k], list):
                return data[k]
    return []


def _get_question_text(market: dict) -> str:
    for field in ("question", "title", "name", "description"):
        val = market.get(field)
        if val and isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def load_raw_data() -> tuple[dict, dict, list, dict[str, list]]:
    events_path = config.DATA_RAW / "events.json"
    lobbies_path = config.DATA_RAW / "lobbies.json"
    matches_path = config.DATA_RAW / "matches.json"

    for p in (events_path, lobbies_path, matches_path):
        if not p.exists():
            raise FileNotFoundError(
                f"Missing {p}. Run 'python -m sportspredict_inventory.fetch' first."
            )

    events_data = _load_json(events_path)
    lobbies_data = _load_json(lobbies_path)
    matches_raw = _load_json(matches_path)
    matches = _extract_list(matches_raw, "data", "matches", "results")
    if not matches and isinstance(matches_raw, list):
        matches = matches_raw

    markets_by_match: dict[str, list] = {}
    for market_file in sorted(config.DATA_RAW_MARKETS.glob("*.json")):
        match_id = market_file.stem
        raw = _load_json(market_file)
        items = _extract_list(raw, "data", "markets", "results", "items", "questions")
        if not items and isinstance(raw, list):
            items = raw
        markets_by_match[match_id] = items

    return events_data, lobbies_data, matches, markets_by_match


def _pick_event(events_data) -> dict:
    candidates = _extract_list(events_data, "data", "events", "results")
    if not candidates and isinstance(events_data, list):
        candidates = events_data
    keyword = config.PROBABILITY_CUP_KEYWORD.lower()
    for e in candidates:
        if isinstance(e, dict) and keyword in (e.get("title") or e.get("name") or "").lower():
            return e
    return candidates[0] if candidates else {}


def _pick_lobby(lobbies_data) -> dict:
    candidates = _extract_list(lobbies_data, "data", "lobbies", "results")
    if not candidates and isinstance(lobbies_data, list):
        candidates = lobbies_data
    return candidates[0] if candidates else {}


def _parse_teams_from_name(match_name: str) -> tuple[str, str]:
    """
    Split 'TUN vs JPN' → ('Tunisia', 'Japan') using FIFA_CODE_TO_NAME map.
    Falls back to the raw token if the code is not in the map.
    """
    if " vs " in match_name:
        home_raw, away_raw = match_name.split(" vs ", 1)
    else:
        return "", ""
    lookup = config.FIFA_CODE_TO_NAME
    home = lookup.get(home_raw.strip(), home_raw.strip())
    away = lookup.get(away_raw.strip(), away_raw.strip())
    return home, away


def build_inventory(
    events_data, lobbies_data, matches: list, markets_by_match: dict[str, list]
) -> pd.DataFrame:
    event = _pick_event(events_data)
    lobby = _pick_lobby(lobbies_data)

    event_id = _normalize_id(event.get("id"))
    event_title = event.get("title") or event.get("name") or event_id
    lobby_id = _normalize_id(lobby.get("id"))

    rows = []
    for match in matches:
        match_id = _normalize_id(match.get("id"))
        match_name = match.get("name") or match_id

        # Extract home/away — MCP data uses FIFA codes in match name, no separate fields
        home = match.get("home_team") or match.get("home") or ""
        away = match.get("away_team") or match.get("away") or ""
        if not home and not away:
            home, away = _parse_teams_from_name(match_name)

        opening_time = (
            match.get("opening_time") or match.get("opens_at")
            or match.get("start_time") or match.get("kickoff") or match.get("date") or ""
        )
        closing_time = (
            match.get("closing_time") or match.get("closes_at")
            or match.get("end_time") or match.get("deadline") or ""
        )

        markets = markets_by_match.get(match_id, [])
        if not markets:
            continue

        # Augment match dict with parsed team names so normalize_market can use them
        match_with_teams = {**match, "home_team": home, "away_team": away}

        for market in markets:
            question_text = _get_question_text(market)
            if not question_text:
                print(f"  WARNING: market {market.get('id')} in match {match_id} has no question text")

            norm = normalize_market(market, match_with_teams)

            rows.append({
                "event_id": event_id,
                "event_title": event_title,
                "lobby_id": lobby_id,
                "match_id": match_id,
                "match_name": match_name,
                "home_team": home,
                "away_team": away,
                "opening_time": opening_time,
                "closing_time": closing_time,
                "market_id": _normalize_id(market.get("id")),
                "question": question_text,
                "status": market.get("status") or "unknown",
                **norm,
            })

    return pd.DataFrame(rows)


def validate_inventory(df: pd.DataFrame) -> bool:
    errors = []

    dupes = df[df.duplicated("market_id", keep=False)]
    if len(dupes):
        errors.append(f"{len(dupes)} duplicate market_ids: {dupes['market_id'].unique()[:5].tolist()}")

    missing_match = df["match_id"].isna() | (df["match_id"] == "")
    if missing_match.any():
        errors.append(f"{missing_match.sum()} markets missing match_id")

    missing_family = df["question_family"].isna() | (df["question_family"] == "")
    if missing_family.any():
        errors.append(f"{missing_family.sum()} markets missing question_family")

    missing_tmpl = df["normalized_question_template"].isna() | (df["normalized_question_template"] == "")
    if missing_tmpl.any():
        errors.append(f"{missing_tmpl.sum()} markets missing normalized_question_template")

    if errors:
        print("VALIDATION WARNINGS:")
        for e in errors:
            print(f"  - {e}")
        return False
    else:
        print("Validation passed.")
        return True


def build_templates(df: pd.DataFrame) -> pd.DataFrame:
    templates = (
        df.groupby("normalized_question_template", dropna=False)
        .agg(
            count_markets=("market_id", "count"),
            example_questions=("question", lambda s: " | ".join(s.dropna().unique()[:3])),
            question_family=("question_family", "first"),
            outcome_variable=("outcome_variable", "first"),
            feature_set_needed=("feature_set_needed", "first"),
            likely_modeling_approach=("likely_modeling_approach", "first"),
            reusable_model_group=("reusable_model_group", "first"),
            difficulty_rating=("difficulty_rating", "first"),
            automation_feasibility=("automation_feasibility", "first"),
            notes=("notes", lambda s: " | ".join(s.dropna().unique()[:2])),
        )
        .reset_index()
        .rename(columns={"difficulty_rating": "suggested_priority"})
        .sort_values("count_markets", ascending=False)
        .reset_index(drop=True)
    )
    return templates


def print_counts(df: pd.DataFrame) -> None:
    print("\n=== Markets by match ===")
    match_counts = (
        df.groupby("match_name")["market_id"]
        .count()
        .sort_values(ascending=False)
    )
    for name, count in match_counts.items():
        print(f"  {count:4d}  {name}")

    print("\n=== Markets by question family ===")
    family_counts = (
        df.groupby("question_family")["market_id"]
        .count()
        .sort_values(ascending=False)
    )
    for family, count in family_counts.items():
        print(f"  {count:4d}  {family}")

    print(f"\nTotal: {len(df)} markets across {df['match_id'].nunique()} matches, "
          f"{df['normalized_question_template'].nunique()} unique templates")


def main() -> None:
    config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    print("Loading raw data...")
    events_data, lobbies_data, matches, markets_by_match = load_raw_data()
    print(f"  {len(matches)} matches, {sum(len(v) for v in markets_by_match.values())} total markets in raw files")

    print("Building inventory...")
    df = build_inventory(events_data, lobbies_data, matches, markets_by_match)

    if df.empty:
        print("ERROR: No markets found. Check that fetch completed successfully.")
        return

    print("Validating...")
    validate_inventory(df)

    inventory_path = config.DATA_PROCESSED / "markets_inventory.csv"
    df.to_csv(inventory_path, index=False, encoding="utf-8")
    print(f"Saved {inventory_path}")

    print("Building question templates...")
    templates = build_templates(df)
    templates_path = config.DATA_PROCESSED / "question_templates.csv"
    templates.to_csv(templates_path, index=False, encoding="utf-8")
    print(f"Saved {templates_path}")

    print_counts(df)


if __name__ == "__main__":
    main()
