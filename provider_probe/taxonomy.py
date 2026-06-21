"""
Loads question_templates.csv and exposes helpers for field mapping.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import config


def load_taxonomy(path: Path | None = None) -> pd.DataFrame:
    p = Path(path) if path else config.TAXONOMY_PATH
    return pd.read_csv(p, encoding="utf-8")


def get_required_fields(df: pd.DataFrame) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for _, row in df.iterrows():
        tmpl = row["normalized_question_template"]
        raw = str(row.get("feature_set_needed", "") or "")
        fields = [f.strip() for f in raw.split(",") if f.strip()]
        result[tmpl] = fields
    return result


def get_family_field_map(df: pd.DataFrame) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for _, row in df.iterrows():
        family = row["question_family"]
        raw = str(row.get("feature_set_needed", "") or "")
        fields = {f.strip() for f in raw.split(",") if f.strip()}
        result.setdefault(family, set()).update(fields)
    return result


def get_all_unique_fields(df: pd.DataFrame) -> list[str]:
    fields: set[str] = set()
    for raw in df["feature_set_needed"].dropna():
        for f in str(raw).split(","):
            f = f.strip()
            if f:
                fields.add(f)
    return sorted(fields)


def print_summary(df: pd.DataFrame) -> None:
    families = df["question_family"].nunique()
    templates = len(df)
    unique_fields = get_all_unique_fields(df)

    print(f"\nTaxonomy summary:")
    print(f"  Families : {families}")
    print(f"  Templates: {templates}")
    print(f"  Unique fields ({len(unique_fields)}): {', '.join(unique_fields)}")

    print("\nBy family:")
    counts = df.groupby("question_family").size().sort_values(ascending=False)
    for family, count in counts.items():
        print(f"  {count:3d}  {family}")
