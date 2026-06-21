"""
python -m sportspredict_inventory.report

Reads data/processed/markets_inventory.csv and question_templates.csv
and writes:
  reports/question_taxonomy.md
  reports/modeling_plan.md
"""

from datetime import datetime
from pathlib import Path

import pandas as pd

from . import config


def _load_csvs() -> tuple[pd.DataFrame, pd.DataFrame]:
    inv_path = config.DATA_PROCESSED / "markets_inventory.csv"
    tmpl_path = config.DATA_PROCESSED / "question_templates.csv"
    for p in (inv_path, tmpl_path):
        if not p.exists():
            raise FileNotFoundError(
                f"Missing {p}. Run 'python -m sportspredict_inventory.categorize' first."
            )
    return pd.read_csv(inv_path, dtype=str), pd.read_csv(tmpl_path, dtype=str)


def _md_table(rows: list[dict], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    lines = [header, sep]
    for row in rows:
        cells = [str(row.get(c, "")) for c in columns]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def build_taxonomy(inv: pd.DataFrame, templates: pd.DataFrame) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total_markets = len(inv)
    unique_templates = inv["normalized_question_template"].nunique()
    unique_families = inv["question_family"].nunique()
    unique_matches = inv["match_id"].nunique()

    lines = [
        "# SportsPredict Probability Cup — Question Taxonomy",
        "",
        f"_Generated: {now}_",
        "",
        "## Summary",
        "",
        f"| Item | Count |",
        f"|------|-------|",
        f"| Total markets | {total_markets} |",
        f"| Unique question templates | {unique_templates} |",
        f"| Question families | {unique_families} |",
        f"| Matches covered | {unique_matches} |",
        "",
    ]

    # ── Families section ───────────────────────────────────────────────────────
    lines.append("## Question Families")
    lines.append("")

    family_counts = (
        inv.groupby("question_family")["market_id"]
        .count()
        .sort_values(ascending=False)
    )

    for family, count in family_counts.items():
        lines.append(f"### {family} ({count} markets)")
        lines.append("")

        family_templates = templates[templates["question_family"] == family].copy()
        if not family_templates.empty:
            family_templates["count_markets"] = pd.to_numeric(
                family_templates["count_markets"], errors="coerce"
            ).fillna(0).astype(int)
            family_templates = family_templates.sort_values("count_markets", ascending=False)

            rows = family_templates[
                ["normalized_question_template", "count_markets", "automation_feasibility", "suggested_priority"]
            ].to_dict("records")
            lines.append(_md_table(rows, ["normalized_question_template", "count_markets", "automation_feasibility", "suggested_priority"]))
        else:
            lines.append("_No templates found._")
        lines.append("")

    # ── Top 20 templates ───────────────────────────────────────────────────────
    lines.append("## Top 20 Most Common Templates")
    lines.append("")

    top20 = templates.copy()
    top20["count_markets"] = pd.to_numeric(top20["count_markets"], errors="coerce").fillna(0).astype(int)
    top20 = top20.sort_values("count_markets", ascending=False).head(20)

    rows = top20[["normalized_question_template", "count_markets", "question_family", "reusable_model_group"]].to_dict("records")
    lines.append(_md_table(rows, ["normalized_question_template", "count_markets", "question_family", "reusable_model_group"]))
    lines.append("")

    # ── Manual review ──────────────────────────────────────────────────────────
    manual = inv[inv.get("manual_review_flag", pd.Series(dtype=str)).fillna("False") == "True"]
    if not manual.empty:
        lines.append("## Markets Requiring Manual Review")
        lines.append("")
        lines.append(f"_{len(manual)} markets flagged for manual review._")
        lines.append("")
        sample = manual[["match_name", "question", "normalized_question_template"]].head(20)
        lines.append(_md_table(sample.to_dict("records"), ["match_name", "question", "normalized_question_template"]))
        lines.append("")

    # ── Match coverage ─────────────────────────────────────────────────────────
    lines.append("## Match Coverage")
    lines.append("")

    match_summary = (
        inv.groupby(["match_name", "match_id"])["market_id"]
        .count()
        .reset_index()
        .rename(columns={"market_id": "market_count"})
        .sort_values("market_count", ascending=False)
    )
    rows = match_summary.to_dict("records")
    lines.append(_md_table(rows, ["match_name", "match_id", "market_count"]))
    lines.append("")

    # ── Analysis answers ───────────────────────────────────────────────────────
    lines.append("## Analysis")
    lines.append("")

    # Which types repeat?
    repeated = templates[pd.to_numeric(templates["count_markets"], errors="coerce").fillna(0) > 1]
    lines.append(f"**Repeating templates (count > 1):** {len(repeated)} of {len(templates)} templates appear in more than one market.")
    lines.append("")

    # Which can share model logic?
    group_counts = inv.groupby("reusable_model_group")["market_id"].count().sort_values(ascending=False)
    lines.append("**Model group coverage:**")
    lines.append("")
    rows = [{"group": g, "markets": c} for g, c in group_counts.items()]
    lines.append(_md_table(rows, ["group", "markets"]))
    lines.append("")

    # Which need external data?
    needs_external = templates[
        templates["feature_set_needed"].str.contains("news|lineup|injury|weather|referee", case=False, na=False)
    ]
    if not needs_external.empty:
        lines.append(f"**Templates needing fresh external data:** {len(needs_external)}")
        lines.append("")
        lines.append(", ".join(needs_external["normalized_question_template"].tolist()[:10]))
        lines.append("")

    # What to build next?
    lines.append("## What to Build Next")
    lines.append("")
    lines.append("Priority order based on market count × automation feasibility:")
    lines.append("")

    priority_map = {"high": 3, "medium": 2, "low": 1, "manual": 0}
    family_agg = inv.groupby("question_family").agg(
        count=("market_id", "count"),
        automation=("automation_feasibility", lambda s: s.mode()[0] if not s.empty else "manual"),
    ).reset_index()
    family_agg["score"] = (
        family_agg["count"]
        * family_agg["automation"].map(priority_map).fillna(0)
    )
    family_agg = family_agg.sort_values("score", ascending=False)

    rows = family_agg[["question_family", "count", "automation", "score"]].to_dict("records")
    lines.append(_md_table(rows, ["question_family", "count", "automation", "score"]))
    lines.append("")

    return "\n".join(lines)


def build_modeling_plan(inv: pd.DataFrame, templates: pd.DataFrame) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# Modeling Plan — SportsPredict Probability Cup",
        "",
        f"_Generated: {now}_",
        "",
        "## Core Answer: Do I Need One Model Per Question?",
        "",
        "**No.** The market universe groups naturally into a small set of reusable model families.",
        "Each family shares the same predictive logic and feature set; only the threshold or",
        "target team changes between instances. Swapping those inputs — not rebuilding the model —",
        "is how you cover hundreds of markets with a handful of models.",
        "",
    ]

    # ── Reusable model groups ──────────────────────────────────────────────────
    lines.append("## Reusable Model Groups")
    lines.append("")

    group_summary = (
        inv.groupby("reusable_model_group")
        .agg(
            market_count=("market_id", "count"),
            families=("question_family", lambda s: ", ".join(sorted(s.unique()))),
            templates=("normalized_question_template", lambda s: ", ".join(sorted(s.unique())[:5])),
            approach=("likely_modeling_approach", "first"),
            features=("feature_set_needed", "first"),
            difficulty=("difficulty_rating", lambda s: pd.to_numeric(s, errors="coerce").mean().round(1)),
            automation=("automation_feasibility", lambda s: s.mode()[0] if not s.empty else "manual"),
        )
        .reset_index()
        .sort_values("market_count", ascending=False)
    )

    for _, row in group_summary.iterrows():
        group = row["reusable_model_group"]
        count = row["market_count"]
        lines.append(f"### {group} ({count} markets)")
        lines.append("")
        lines.append(f"- **Families covered:** {row['families']}")
        lines.append(f"- **Sample templates:** {row['templates']}")
        lines.append(f"- **Modeling approach:** {row['approach']}")
        lines.append(f"- **Feature set:** {row['features']}")
        lines.append(f"- **Avg difficulty:** {row['difficulty']}")
        lines.append(f"- **Automation:** {row['automation']}")
        lines.append("")

    # ── Priority ordering ──────────────────────────────────────────────────────
    lines.append("## Priority Ordering")
    lines.append("")
    lines.append("Score = `market_count × (6 - avg_difficulty)` — higher is better ROI.")
    lines.append("")

    difficulty_map = inv.copy()
    difficulty_map["difficulty_rating"] = pd.to_numeric(
        difficulty_map["difficulty_rating"], errors="coerce"
    ).fillna(3)
    priority = (
        difficulty_map.groupby("reusable_model_group")
        .agg(
            count=("market_id", "count"),
            avg_difficulty=("difficulty_rating", "mean"),
        )
        .reset_index()
    )
    priority["score"] = priority["count"] * (6 - priority["avg_difficulty"])
    priority = priority.sort_values("score", ascending=False)
    priority["avg_difficulty"] = priority["avg_difficulty"].round(1)
    priority["score"] = priority["score"].round(0).astype(int)

    rows = priority.to_dict("records")
    lines.append(_md_table(rows, ["reusable_model_group", "count", "avg_difficulty", "score"]))
    lines.append("")

    # ── Which families share feature sets? ────────────────────────────────────
    lines.append("## Which Feature Sets Are Reusable?")
    lines.append("")

    feature_groups = (
        inv.groupby("feature_set_needed")["reusable_model_group"]
        .agg(lambda s: ", ".join(sorted(s.unique())))
        .reset_index()
        .rename(columns={"reusable_model_group": "model_groups"})
    )
    rows = feature_groups.to_dict("records")
    lines.append(_md_table(rows, ["feature_set_needed", "model_groups"]))
    lines.append("")

    # ── Manual review / ignore ─────────────────────────────────────────────────
    manual_df = inv[
        inv["automation_feasibility"].fillna("").isin(["manual"])
    ]
    if not manual_df.empty:
        lines.append("## Markets to Handle Manually or Ignore")
        lines.append("")
        lines.append(f"_{len(manual_df)} markets flagged as manual or low-automation._")
        lines.append("")
        sample = manual_df[["match_name", "question", "question_family"]].drop_duplicates("question").head(20)
        lines.append(_md_table(sample.to_dict("records"), ["match_name", "question", "question_family"]))
        lines.append("")

    # ── External data requirements ─────────────────────────────────────────────
    lines.append("## External Data Requirements")
    lines.append("")

    all_features = set()
    for feat_str in inv["feature_set_needed"].dropna().unique():
        all_features.update(f.strip() for f in feat_str.split(","))

    feature_source_map = {
        "team_scoring_rate": "Historical match data (FBref, football-data.co.uk, StatsBomb)",
        "defensive_strength": "Historical match data",
        "h2h": "Historical head-to-head data",
        "form": "Recent match results (last 5–10 games)",
        "odds": "Betting exchange / bookmaker odds API",
        "team_strength": "Elo ratings, SPI (FiveThirtyEight), or computed from results",
        "lineup": "Pre-match lineup data (SofaScore, ESPN, WhatsApp APIs) — needs fresh data",
        "player_form": "Player-level stats — needs fresh data per gameweek",
        "xg_per_shot": "xG data (Understat, StatsBomb)",
        "referee_stats": "Historical referee discipline data",
        "team_discipline": "Historical cards per match per team",
        "match_importance": "Inferred from competition stage / points position",
        "group_table": "Tournament/group table — needs live data",
        "match_schedule": "Tournament fixture list",
        "team_corner_rates": "Historical corner data",
        "team_shot_rates": "Historical shots data",
        "team_possession_rates": "Historical possession data",
        "match_style": "Historical team style indicators",
        "manual_review": "No automated source — manual research required",
    }

    for feat in sorted(all_features):
        source = feature_source_map.get(feat, "Source unknown — investigate")
        lines.append(f"- **{feat}**: {source}")
    lines.append("")

    # ── One-off markets ────────────────────────────────────────────────────────
    other_df = inv[inv["question_family"] == "other"]
    if not other_df.empty:
        lines.append("## One-Off Markets (difficulty=5, not worth modeling initially)")
        lines.append("")
        lines.append(f"_{len(other_df)} markets in the 'other' category._")
        lines.append("")
        sample = other_df[["match_name", "question"]].drop_duplicates("question").head(25)
        lines.append(_md_table(sample.to_dict("records"), ["match_name", "question"]))
        lines.append("")

    # ── Next steps ─────────────────────────────────────────────────────────────
    lines.append("## Next Build Steps")
    lines.append("")
    lines.append("1. **Odds baseline** — Collect bookmaker odds for all markets in `match_result_model`")
    lines.append("   and `scoreline_model`. Convert to probabilities. This gives you a fast, strong")
    lines.append("   baseline for ~50% of all markets.")
    lines.append("")
    lines.append("2. **Poisson goal model** — Fit a simple bivariate Poisson or Dixon-Coles model")
    lines.append("   using historical match data. This covers `team_goal_model`, `scoreline_model`,")
    lines.append("   and `margin_model` simultaneously.")
    lines.append("")
    lines.append("3. **Half-time model** — Adapt the goal model with first/second-half goal rates.")
    lines.append("   Covers `first_half` and `second_half` families.")
    lines.append("")
    lines.append("4. **Tournament simulation** — If group-stage data is available, a simple Monte Carlo")
    lines.append("   bracket sim covers all `tournament_progression_model` markets.")
    lines.append("")
    lines.append("5. **Set pieces and discipline** — Lower priority; model if data is available and")
    lines.append("   these market counts are material.")
    lines.append("")
    lines.append("6. **Player markets** — Only if lineups are available before closing time. Low")
    lines.append("   automation feasibility; handle manually for now.")
    lines.append("")
    lines.append("7. **Manual review queue** — Review all markets flagged `manual_review_flag=True`")
    lines.append("   one by one. Some may be mis-classified by the regex engine.")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    config.REPORTS.mkdir(parents=True, exist_ok=True)

    print("Loading processed data...")
    inv, templates = _load_csvs()
    print(f"  {len(inv)} markets, {len(templates)} templates")

    print("Writing question_taxonomy.md...")
    taxonomy = build_taxonomy(inv, templates)
    (config.REPORTS / "question_taxonomy.md").write_text(taxonomy, encoding="utf-8")
    print(f"  Saved {config.REPORTS / 'question_taxonomy.md'}")

    print("Writing modeling_plan.md...")
    plan = build_modeling_plan(inv, templates)
    (config.REPORTS / "modeling_plan.md").write_text(plan, encoding="utf-8")
    print(f"  Saved {config.REPORTS / 'modeling_plan.md'}")

    print("Done.")


if __name__ == "__main__":
    main()
