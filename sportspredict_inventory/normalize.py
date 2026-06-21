"""
Question normalization: converts raw question text into structured fields.

Patterns are derived from the actual 368 Probability Cup question texts pulled
from the SportsPredict API. The question style is creative comparison questions,
not standard betting-market lines.

Call normalize_market(market_dict, match_dict) to get a dict of normalization
fields ready to merge into a CSV row.
"""

import re
from dataclasses import dataclass
from typing import Optional

# ── Text helpers ───────────────────────────────────────────────────────────────

def _get_question_text(market: dict) -> str:
    for field in ("question", "title", "name", "description"):
        val = market.get(field)
        if val and isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def _clean(text: str) -> str:
    """Lowercase, collapse whitespace, strip trailing punctuation."""
    return re.sub(r"\s+", " ", text.lower()).strip().rstrip("?.")


# ── Structural detection ──────────────────────────────────────────────────────

_AT_HALFTIME = re.compile(r"^at halftime", re.IGNORECASE)
_IN_SECOND_HALF = re.compile(r"\bin the second half\b|\bsecond half\b", re.IGNORECASE)
_IN_FIRST_HALF = re.compile(r"\bin the first half\b|\bfirst half\b", re.IGNORECASE)

# N or more / N or fewer / at least N / N+
_N_OR_MORE = re.compile(r"(\d+(?:\.\d+)?)\s+or\s+more|at\s+least\s+(\d+(?:\.\d+)?)", re.IGNORECASE)
_N_OR_FEWER = re.compile(r"(\d+(?:\.\d+)?)\s+or\s+fewer|(\d+(?:\.\d+)?)\s+or\s+less", re.IGNORECASE)
_OVER_N = re.compile(r"\bover\s+(\d+(?:\.\d+)?)\b|\bmore\s+than\s+(\d+(?:\.\d+)?)\b", re.IGNORECASE)
_UNDER_N = re.compile(r"\bunder\s+(\d+(?:\.\d+)?)\b|\bfewer\s+than\s+(\d+(?:\.\d+)?)\b|\bless\s+than\s+(\d+(?:\.\d+)?)\b", re.IGNORECASE)

def _extract_n(text: str) -> tuple[str, Optional[float]]:
    """
    Find the first threshold in text (N or more / at least N / over N / N or fewer / under N).
    Returns (text_with_{N}, float_value_or_None).
    """
    for pat in (_N_OR_MORE, _N_OR_FEWER, _OVER_N, _UNDER_N):
        m = pat.search(text)
        if m:
            raw = next(g for g in m.groups() if g is not None)
            value = float(raw)
            text = text[:m.start()] + "{N}" + text[m.end():]
            return text, value
    return text, None


# ── Team replacement ──────────────────────────────────────────────────────────

def _replace_teams(text: str, home: str, away: str) -> tuple[str, Optional[str]]:
    """
    Replace home/away team names with {HOME}/{AWAY}.
    Also handles known alternate spellings (e.g. "Curaçao" / "Curacao").
    Returns (modified_text, target: "home"|"away"|"both"|None).
    """
    found_home = found_away = False

    def _sub(name: str, placeholder: str, t: str) -> tuple[str, bool]:
        if not name:
            return t, False
        # Try exact match and a few accent-stripped variants
        variants = {name}
        # strip accents for matching (e.g. Türkiye → Turkiye, Curaçao → Curacao)
        import unicodedata
        nfkd = unicodedata.normalize("NFKD", name)
        ascii_name = "".join(c for c in nfkd if not unicodedata.combining(c))
        if ascii_name != name:
            variants.add(ascii_name)
        found = False
        for v in variants:
            pat = re.compile(r"(?<!\w)" + re.escape(v) + r"(?!\w)", re.IGNORECASE)
            if pat.search(t):
                t = pat.sub(placeholder, t)
                found = True
        return t, found

    text, found_home = _sub(home, "{HOME}", text)
    text, found_away = _sub(away, "{AWAY}", text)

    if found_home and found_away:
        target = "both"
    elif found_home:
        target = "home"
    elif found_away:
        target = "away"
    else:
        target = None

    return text, target


# ── Result dataclass ─────────────────────────────────────────────────────────

@dataclass
class NormResult:
    normalized_question_template: str
    question_family: str
    question_subtype: str
    target_team_or_side: Optional[str]
    threshold_value: Optional[float]
    time_scope: str
    outcome_variable: str
    feature_set_needed: str
    likely_modeling_approach: str
    reusable_model_group: str
    difficulty_rating: int
    automation_feasibility: str
    manual_review_flag: bool
    notes: str

    def as_dict(self) -> dict:
        return self.__dict__


# ── Pattern matchers ─────────────────────────────────────────────────────────
# Each function receives the LOWERCASED, team-replaced question text.
# Returns NormResult or None.

_HOME = r"(?<!\w)\{HOME\}"
_AWAY = r"(?<!\w)\{AWAY\}"
_TEAM = rf"(?:{_HOME}|{_AWAY})"   # matches either placeholder
_ANY_TEAM = _TEAM                  # alias for readability


def _r(p: str) -> re.Pattern:
    return re.compile(p, re.IGNORECASE)


def _match(pattern: re.Pattern, text: str) -> bool:
    return bool(pattern.search(text))


# ── Match result ─────────────────────────────────────────────────────────────

_WIN_MATCH = _r(rf"{_TEAM}\s+win the match|will {_TEAM} win")

def _try_match_result(text: str, raw: str, home: str, away: str, time_scope: str) -> Optional[NormResult]:
    if _match(_WIN_MATCH, text):
        t = re.sub(r"^will\s+", "", raw.lower()).strip().rstrip("?")
        return NormResult(
            normalized_question_template=f"{{TEAM}} win the match",
            question_family="match_result",
            question_subtype="team_win",
            target_team_or_side=_which_team(text),
            threshold_value=None,
            time_scope="regulation",
            outcome_variable="match_win",
            feature_set_needed="team_strength,h2h,form,odds",
            likely_modeling_approach="logistic_regression,elo_model,odds_implied",
            reusable_model_group="match_result_model",
            difficulty_rating=1,
            automation_feasibility="high",
            manual_review_flag=False,
            notes="",
        )
    return None


def _which_team(text: str) -> Optional[str]:
    has_home = bool(re.search(r"\{HOME\}", text))
    has_away = bool(re.search(r"\{AWAY\}", text))
    if has_home and has_away:
        return "both"
    if has_home:
        return "home"
    if has_away:
        return "away"
    return None


# ── Total goals ──────────────────────────────────────────────────────────────

_TOTAL_GOALS_RE = _r(r"\b(?:the match|total|the game)\b.*?\bgoals?\b|\bgoals?.*?\b(?:total|in the match)\b")
_SECOND_HALF_GOALS_VS_FIRST = _r(r"second half.*?more goals.*?first half|more goals.*?first half.*?second half")
_SECOND_HALF_GOALS_N = _r(r"second half.*?\bgoals?\b|\bgoals?.*?second half")
_FIRST_HALF_GOALS_N = _r(r"first half.*?\bgoals?\b|\bgoals?.*?first half")
_BOTH_SCORE_AND_GOALS = _r(r"both teams score and.*?\bgoals?\b|\bboth teams.*?score.*?(?:and|or).*?\bgoals?\b")

def _try_goals(text: str, time_scope: str) -> Optional[NormResult]:
    # "both teams score AND N or more goals"
    if _match(_BOTH_SCORE_AND_GOALS, text):
        t, val = _extract_n(text)
        return NormResult(
            normalized_question_template="both teams score AND {N}+ total goals",
            question_family="goals_totals",
            question_subtype="btts_and_over",
            target_team_or_side="both",
            threshold_value=val,
            time_scope="regulation",
            outcome_variable="btts_and_total_goals",
            feature_set_needed="team_scoring_rate,defensive_strength,h2h,form",
            likely_modeling_approach="bivariate_poisson,logistic_regression",
            reusable_model_group="scoreline_model",
            difficulty_rating=2,
            automation_feasibility="high",
            manual_review_flag=False,
            notes="",
        )

    # "second half more goals than first half"
    if _match(_SECOND_HALF_GOALS_VS_FIRST, text):
        return NormResult(
            normalized_question_template="second half more goals than first half",
            question_family="goals_totals",
            question_subtype="half_goals_comparison",
            target_team_or_side=None,
            threshold_value=None,
            time_scope="second_half",
            outcome_variable="second_half_goals_gt_first",
            feature_set_needed="team_scoring_rate,half_goal_rates,h2h",
            likely_modeling_approach="poisson_model,logistic_regression",
            reusable_model_group="scoreline_model",
            difficulty_rating=2,
            automation_feasibility="high",
            manual_review_flag=False,
            notes="",
        )

    # Match total goals over/under
    if _match(_TOTAL_GOALS_RE, text):
        t, val = _extract_n(text)
        direction = "under" if re.search(r"\bor fewer\b|\bor less\b|\bfewer than\b", text, re.IGNORECASE) else "over"
        return NormResult(
            normalized_question_template=f"match total goals {direction} {{N}}",
            question_family="goals_totals",
            question_subtype=f"total_goals_{direction}",
            target_team_or_side=None,
            threshold_value=val,
            time_scope="regulation",
            outcome_variable="total_goals",
            feature_set_needed="team_scoring_rate,defensive_strength,h2h,form",
            likely_modeling_approach="poisson_model,logistic_regression",
            reusable_model_group="scoreline_model",
            difficulty_rating=2,
            automation_feasibility="high",
            manual_review_flag=False,
            notes="",
        )

    # Second half goals N+
    if _match(_SECOND_HALF_GOALS_N, text) and "score" not in text:
        t, val = _extract_n(text)
        return NormResult(
            normalized_question_template="second half {N}+ goals",
            question_family="goals_totals",
            question_subtype="second_half_goals",
            target_team_or_side=None,
            threshold_value=val,
            time_scope="second_half",
            outcome_variable="second_half_goals",
            feature_set_needed="team_scoring_rate,half_goal_rates,h2h",
            likely_modeling_approach="poisson_model,logistic_regression",
            reusable_model_group="scoreline_model",
            difficulty_rating=2,
            automation_feasibility="high",
            manual_review_flag=False,
            notes="",
        )

    return None


# ── Team scores ───────────────────────────────────────────────────────────────

_TEAM_SCORE_GOAL = _r(rf"{_ANY_TEAM}\s+score(?:\s+at\s+least\s+1\s+goal|\s+a\s+goal)?$")
_TEAM_SCORE_IN_HALF = _r(rf"{_ANY_TEAM}\s+score in the (?:first|second) half")
_TEAM_SCORE_FIRST_GOAL_AND = _r(rf"{_ANY_TEAM}\s+score the first goal.*?{_ANY_TEAM}\s+score")
_TEAM_SCORE_FIRST_GOAL_HALF = _r(rf"{_ANY_TEAM}\s+score the first goal of the second half")
_TEAM_SCORE_MORE_GOALS = _r(rf"{_ANY_TEAM}\s+score more goals than {_ANY_TEAM}")

def _try_team_scores(text: str, time_scope: str) -> Optional[NormResult]:
    # "TEAM score first goal AND TEAM score in second half" (combo)
    if _match(_TEAM_SCORE_FIRST_GOAL_AND, text) and "second half" in text:
        return NormResult(
            normalized_question_template="{HOME} score first goal AND {AWAY} score in 2H",
            question_family="goals_totals",
            question_subtype="first_goal_and_team_scores",
            target_team_or_side="both",
            threshold_value=None,
            time_scope="regulation",
            outcome_variable="first_goal_and_comeback",
            feature_set_needed="team_scoring_rate,h2h,form",
            likely_modeling_approach="scoreline_simulation",
            reusable_model_group="scoreline_model",
            difficulty_rating=3,
            automation_feasibility="medium",
            manual_review_flag=False,
            notes="Combined market — requires scoreline simulation",
        )

    # "TEAM score the first goal of the second half"
    if _match(_TEAM_SCORE_FIRST_GOAL_HALF, text):
        target = _which_team(text)
        return NormResult(
            normalized_question_template="{TEAM} score first goal of second half",
            question_family="goals_totals",
            question_subtype="first_goal_second_half",
            target_team_or_side=target,
            threshold_value=None,
            time_scope="second_half",
            outcome_variable="first_goal_second_half",
            feature_set_needed="team_scoring_rate,half_goal_rates",
            likely_modeling_approach="poisson_model,logistic_regression",
            reusable_model_group="scoreline_model",
            difficulty_rating=3,
            automation_feasibility="medium",
            manual_review_flag=False,
            notes="",
        )

    # "TEAM score more goals than TEAM in second half"
    if _match(_TEAM_SCORE_MORE_GOALS, text):
        return NormResult(
            normalized_question_template="{HOME} score more goals than {AWAY} in second half",
            question_family="goals_totals",
            question_subtype="team_goals_comparison_2h",
            target_team_or_side="both",
            threshold_value=None,
            time_scope="second_half",
            outcome_variable="team_goals_comparison",
            feature_set_needed="team_scoring_rate,half_goal_rates,defensive_strength",
            likely_modeling_approach="bivariate_poisson,logistic_regression",
            reusable_model_group="scoreline_model",
            difficulty_rating=2,
            automation_feasibility="high",
            manual_review_flag=False,
            notes="",
        )

    # "TEAM score in the first/second half"
    if _match(_TEAM_SCORE_IN_HALF, text):
        target = _which_team(text)
        t_scope = "first_half" if "first half" in text else "second_half"
        return NormResult(
            normalized_question_template=f"{{TEAM}} score in {t_scope.replace('_',' ')}",
            question_family="goals_totals",
            question_subtype=f"team_score_in_{t_scope}",
            target_team_or_side=target,
            threshold_value=None,
            time_scope=t_scope,
            outcome_variable="team_scores_in_half",
            feature_set_needed="team_scoring_rate,half_goal_rates,defensive_strength",
            likely_modeling_approach="poisson_model,logistic_regression",
            reusable_model_group="scoreline_model",
            difficulty_rating=2,
            automation_feasibility="high",
            manual_review_flag=False,
            notes="",
        )

    # "TEAM score at least 1 goal" / "TEAM score"
    if _match(_TEAM_SCORE_GOAL, text):
        target = _which_team(text)
        return NormResult(
            normalized_question_template="{TEAM} score at least 1 goal",
            question_family="goals_totals",
            question_subtype="team_scores",
            target_team_or_side=target,
            threshold_value=1.0,
            time_scope="regulation",
            outcome_variable="team_scores",
            feature_set_needed="team_scoring_rate,defensive_strength,h2h",
            likely_modeling_approach="poisson_model,logistic_regression",
            reusable_model_group="scoreline_model",
            difficulty_rating=2,
            automation_feasibility="high",
            manual_review_flag=False,
            notes="",
        )

    return None


# ── Shots on target ──────────────────────────────────────────────────────────

_SHOTS_COMPARISON = _r(rf"{_ANY_TEAM}\s+(?:have\s+)?more shots on target than {_ANY_TEAM}")
_SHOTS_BOTH_AT_LEAST_1 = _r(r"both teams have at least 1 shot on target")
_SHOTS_TOTAL_N = _r(r"(?:there be|total)\s+.*?\bshots? on target\b|\bshots? on target\b.*?(?:there be|total|\bin the)")
_SHOTS_TEAM_N = _r(rf"{_ANY_TEAM}\s+have\s+.*?\bshots? on target\b")
_PLAYER_SHOTS = _r(r"have at least \d+ shot(?:s)? on target")

def _try_shots(text: str, time_scope: str) -> Optional[NormResult]:
    # "TEAM more shots on target than TEAM (in second half)"
    if _match(_SHOTS_COMPARISON, text):
        t_scope = "second_half" if "second half" in text else "regulation"
        return NormResult(
            normalized_question_template="{HOME} more shots on target than {AWAY}",
            question_family="shots",
            question_subtype="shots_comparison",
            target_team_or_side="both",
            threshold_value=None,
            time_scope=t_scope,
            outcome_variable="shots_on_target_comparison",
            feature_set_needed="team_shot_rates,defensive_strength,match_style",
            likely_modeling_approach="logistic_regression,team_stats_model",
            reusable_model_group="shots_model",
            difficulty_rating=3,
            automation_feasibility="medium",
            manual_review_flag=False,
            notes="",
        )

    # "both teams have at least 1 shot on target"
    if _match(_SHOTS_BOTH_AT_LEAST_1, text):
        t_scope = "second_half" if "second half" in text else ("first_half" if "first half" in text else "regulation")
        return NormResult(
            normalized_question_template="both teams have at least 1 shot on target",
            question_family="shots",
            question_subtype="both_teams_sot",
            target_team_or_side="both",
            threshold_value=None,
            time_scope=t_scope,
            outcome_variable="both_teams_shot_on_target",
            feature_set_needed="team_shot_rates,defensive_strength",
            likely_modeling_approach="logistic_regression",
            reusable_model_group="shots_model",
            difficulty_rating=2,
            automation_feasibility="high",
            manual_review_flag=False,
            notes="",
        )

    # "there be N or more total shots on target"
    if re.search(r"\bthere be\b.*\bshots? on target\b|\bshots? on target\b.*?\bthere be\b|\btotal shots? on target\b", text, re.IGNORECASE):
        t, val = _extract_n(text)
        t_scope = "second_half" if "second half" in text else "regulation"
        return NormResult(
            normalized_question_template="total shots on target {N}+",
            question_family="shots",
            question_subtype="total_shots_over",
            target_team_or_side=None,
            threshold_value=val,
            time_scope=t_scope,
            outcome_variable="total_shots_on_target",
            feature_set_needed="team_shot_rates,defensive_strength",
            likely_modeling_approach="poisson_model,logistic_regression",
            reusable_model_group="shots_model",
            difficulty_rating=3,
            automation_feasibility="medium",
            manual_review_flag=False,
            notes="",
        )

    # "TEAM have N or more shots on target"
    if _match(_SHOTS_TEAM_N, text):
        target = _which_team(text)
        t, val = _extract_n(text)
        t_scope = "second_half" if "second half" in text else "regulation"
        return NormResult(
            normalized_question_template="{TEAM} have {N}+ shots on target",
            question_family="shots",
            question_subtype="team_shots_over",
            target_team_or_side=target,
            threshold_value=val,
            time_scope=t_scope,
            outcome_variable="team_shots_on_target",
            feature_set_needed="team_shot_rates,defensive_strength",
            likely_modeling_approach="poisson_model,logistic_regression",
            reusable_model_group="shots_model",
            difficulty_rating=3,
            automation_feasibility="medium",
            manual_review_flag=False,
            notes="",
        )

    return None


# ── Corners ──────────────────────────────────────────────────────────────────

_CORNERS_COMPARISON = _r(rf"{_ANY_TEAM}\s+(?:have\s+)?more corner kicks? than {_ANY_TEAM}|{_ANY_TEAM}\s+finish with more corner kicks? than {_ANY_TEAM}")
_CORNERS_TOTAL_N = _r(r"\bthere be\b.*?\bcorner kicks?\b|\bcorner kicks?\b.*?\bthere be\b|\btotal.*?\bcorner kicks?\b|\bcorner kicks?\b.*?\bor more\b")
_CORNERS_TEAM_N = _r(rf"{_ANY_TEAM}.*?\bcorner kicks?\b|corner kicks?.*?{_ANY_TEAM}")

def _try_corners(text: str, time_scope: str) -> Optional[NormResult]:
    if _match(_CORNERS_COMPARISON, text):
        t_scope = "second_half" if "second half" in text else ("first_half" if "halftime" in text or "first half" in text else "regulation")
        return NormResult(
            normalized_question_template="{HOME} more corner kicks than {AWAY}",
            question_family="corners",
            question_subtype="corners_comparison",
            target_team_or_side="both",
            threshold_value=None,
            time_scope=t_scope,
            outcome_variable="corner_kicks_comparison",
            feature_set_needed="team_corner_rates,match_style",
            likely_modeling_approach="logistic_regression,team_stats_model",
            reusable_model_group="set_pieces_model",
            difficulty_rating=3,
            automation_feasibility="medium",
            manual_review_flag=False,
            notes="",
        )

    if re.search(r"\bcorner kicks?\b", text, re.IGNORECASE):
        t, val = _extract_n(text)
        target = _which_team(text)
        t_scope = "second_half" if "second half" in text else ("first_half" if "first half" in text or "halftime" in text else "regulation")
        if target:
            tmpl = "{TEAM} {N}+ corner kicks"
            sub = "team_corners_over"
        else:
            tmpl = "total corner kicks {N}+"
            sub = "total_corners_over"
        return NormResult(
            normalized_question_template=tmpl,
            question_family="corners",
            question_subtype=sub,
            target_team_or_side=target,
            threshold_value=val,
            time_scope=t_scope,
            outcome_variable="corner_kicks",
            feature_set_needed="team_corner_rates,match_style",
            likely_modeling_approach="poisson_model,logistic_regression",
            reusable_model_group="set_pieces_model",
            difficulty_rating=3,
            automation_feasibility="medium",
            manual_review_flag=False,
            notes="",
        )

    return None


# ── Offsides ─────────────────────────────────────────────────────────────────

_OFFSIDE_RE = _r(rf"{_ANY_TEAM}.*?offside|offside.*?{_ANY_TEAM}")

def _try_offsides(text: str) -> Optional[NormResult]:
    if re.search(r"\boffside\b", text, re.IGNORECASE):
        target = _which_team(text)
        _, val = _extract_n(text)
        return NormResult(
            normalized_question_template="{TEAM} caught offside {N}+ times",
            question_family="offsides",
            question_subtype="team_offsides",
            target_team_or_side=target,
            threshold_value=val,
            time_scope="regulation",
            outcome_variable="offside_count",
            feature_set_needed="team_attacking_depth,opponent_defensive_line",
            likely_modeling_approach="poisson_model,logistic_regression",
            reusable_model_group="set_pieces_model",
            difficulty_rating=3,
            automation_feasibility="medium",
            manual_review_flag=False,
            notes="",
        )
    return None


# ── Fouls ─────────────────────────────────────────────────────────────────────

_FOULS_RE = _r(r"\bfouls?\b")
_FOULS_MORE_THAN = _r(rf"{_ANY_TEAM}\s+commit more fouls? than {_ANY_TEAM}")

def _try_fouls(text: str) -> Optional[NormResult]:
    if _match(_FOULS_MORE_THAN, text):
        return NormResult(
            normalized_question_template="{HOME} commit more fouls than {AWAY}",
            question_family="fouls",
            question_subtype="fouls_comparison",
            target_team_or_side="both",
            threshold_value=None,
            time_scope="regulation",
            outcome_variable="fouls_comparison",
            feature_set_needed="team_foul_rates,referee_stats",
            likely_modeling_approach="logistic_regression,team_stats_model",
            reusable_model_group="discipline_model",
            difficulty_rating=3,
            automation_feasibility="medium",
            manual_review_flag=False,
            notes="",
        )
    if _match(_FOULS_RE, text):
        target = _which_team(text)
        _, val = _extract_n(text)
        return NormResult(
            normalized_question_template="{TEAM} {N}+ fouls",
            question_family="fouls",
            question_subtype="team_fouls_total",
            target_team_or_side=target,
            threshold_value=val,
            time_scope="regulation",
            outcome_variable="fouls",
            feature_set_needed="team_foul_rates,referee_stats",
            likely_modeling_approach="poisson_model,logistic_regression",
            reusable_model_group="discipline_model",
            difficulty_rating=3,
            automation_feasibility="medium",
            manual_review_flag=False,
            notes="",
        )
    return None


# ── Cards ─────────────────────────────────────────────────────────────────────

_CARDS_COMPARISON = _r(rf"{_ANY_TEAM}\s+receive more cards? than {_ANY_TEAM}|{_ANY_TEAM}\s+(?:have|get) more cards? than {_ANY_TEAM}")
_CARDS_TOTAL_N = _r(r"\bthere be\b.*?\bcards?\b|\btotal.*?\bcards?\b|\bcards?\b.*?\bthere be\b")
_CARDS_TEAM = _r(rf"{_ANY_TEAM}.*?\bcards?\b|\bcards?\b.*?{_ANY_TEAM}")
_PENALTY_OR_RED = _r(r"penalty kick.*?red card|red card.*?penalty kick|penalty kick be awarded or a red card")
_PENALTY_ONLY = _r(r"penalty kick be awarded")

def _try_cards(text: str) -> Optional[NormResult]:
    # Penalty OR red card combo
    if _match(_PENALTY_OR_RED, text):
        return NormResult(
            normalized_question_template="penalty kick awarded OR red card shown",
            question_family="discipline",
            question_subtype="penalty_or_red_card",
            target_team_or_side=None,
            threshold_value=None,
            time_scope="regulation",
            outcome_variable="penalty_or_red_card",
            feature_set_needed="referee_stats,team_aggression,match_importance",
            likely_modeling_approach="logistic_regression",
            reusable_model_group="discipline_model",
            difficulty_rating=3,
            automation_feasibility="medium",
            manual_review_flag=False,
            notes="",
        )

    if _match(_PENALTY_ONLY, text):
        return NormResult(
            normalized_question_template="penalty kick awarded",
            question_family="discipline",
            question_subtype="penalty_awarded",
            target_team_or_side=None,
            threshold_value=None,
            time_scope="regulation",
            outcome_variable="penalty_awarded",
            feature_set_needed="referee_stats,team_aggression",
            likely_modeling_approach="logistic_regression",
            reusable_model_group="discipline_model",
            difficulty_rating=4,
            automation_feasibility="low",
            manual_review_flag=False,
            notes="",
        )

    # Team receives more cards than opponent
    if _match(_CARDS_COMPARISON, text):
        return NormResult(
            normalized_question_template="{HOME} receive more cards than {AWAY}",
            question_family="discipline",
            question_subtype="cards_comparison",
            target_team_or_side="both",
            threshold_value=None,
            time_scope="regulation",
            outcome_variable="cards_comparison",
            feature_set_needed="referee_stats,team_discipline,match_importance",
            likely_modeling_approach="logistic_regression",
            reusable_model_group="discipline_model",
            difficulty_rating=3,
            automation_feasibility="medium",
            manual_review_flag=False,
            notes="",
        )

    # Total cards
    if re.search(r"\bcards?\b", text, re.IGNORECASE):
        _, val = _extract_n(text)
        target = _which_team(text)
        t_scope = "second_half" if "second half" in text else "regulation"
        if target:
            tmpl = "{TEAM} {N}+ cards"
            sub = "team_cards_total"
        else:
            tmpl = "total cards {N}+"
            sub = "total_cards_over"
        return NormResult(
            normalized_question_template=tmpl,
            question_family="discipline",
            question_subtype=sub,
            target_team_or_side=target,
            threshold_value=val,
            time_scope=t_scope,
            outcome_variable="cards",
            feature_set_needed="referee_stats,team_discipline,match_importance",
            likely_modeling_approach="poisson_model,logistic_regression",
            reusable_model_group="discipline_model",
            difficulty_rating=3,
            automation_feasibility="medium",
            manual_review_flag=False,
            notes="",
        )

    return None


# ── Halftime state ────────────────────────────────────────────────────────────

def _try_halftime(text: str) -> Optional[NormResult]:
    if not _match(_AT_HALFTIME, text):
        return None

    # "at halftime, will TEAM be winning?"
    if re.search(r"\{(?:HOME|AWAY)\}\s+be winning", text, re.IGNORECASE):
        target = _which_team(text)
        return NormResult(
            normalized_question_template="at halftime {TEAM} winning",
            question_family="halftime",
            question_subtype="halftime_team_winning",
            target_team_or_side=target,
            threshold_value=None,
            time_scope="first_half",
            outcome_variable="halftime_lead",
            feature_set_needed="team_strength,h2h,form,half_goal_rates",
            likely_modeling_approach="logistic_regression,elo_model",
            reusable_model_group="match_result_model",
            difficulty_rating=2,
            automation_feasibility="high",
            manual_review_flag=False,
            notes="",
        )

    # "at halftime, will the match be tied?"
    if re.search(r"match be tied|be tied", text, re.IGNORECASE):
        return NormResult(
            normalized_question_template="at halftime match tied",
            question_family="halftime",
            question_subtype="halftime_tied",
            target_team_or_side=None,
            threshold_value=None,
            time_scope="first_half",
            outcome_variable="halftime_draw",
            feature_set_needed="team_strength,h2h,form,half_goal_rates",
            likely_modeling_approach="logistic_regression,elo_model",
            reusable_model_group="match_result_model",
            difficulty_rating=2,
            automation_feasibility="high",
            manual_review_flag=False,
            notes="",
        )

    # "at halftime, will both teams have at least 1 shot on target?"
    if re.search(r"both teams have at least 1 shot on target", text, re.IGNORECASE):
        return NormResult(
            normalized_question_template="at halftime both teams have 1+ shot on target",
            question_family="halftime",
            question_subtype="halftime_both_teams_sot",
            target_team_or_side="both",
            threshold_value=None,
            time_scope="first_half",
            outcome_variable="halftime_both_sot",
            feature_set_needed="team_shot_rates,defensive_strength",
            likely_modeling_approach="logistic_regression",
            reusable_model_group="shots_model",
            difficulty_rating=2,
            automation_feasibility="high",
            manual_review_flag=False,
            notes="",
        )

    # "at halftime, will TEAM have more corner kicks than TEAM?"
    if re.search(r"corner kicks?", text, re.IGNORECASE):
        return NormResult(
            normalized_question_template="at halftime {HOME} more corner kicks than {AWAY}",
            question_family="halftime",
            question_subtype="halftime_corners_comparison",
            target_team_or_side="both",
            threshold_value=None,
            time_scope="first_half",
            outcome_variable="halftime_corners_comparison",
            feature_set_needed="team_corner_rates,match_style",
            likely_modeling_approach="logistic_regression",
            reusable_model_group="set_pieces_model",
            difficulty_rating=3,
            automation_feasibility="medium",
            manual_review_flag=False,
            notes="",
        )

    # Generic halftime fallback
    return NormResult(
        normalized_question_template="at halftime: (other)",
        question_family="halftime",
        question_subtype="halftime_other",
        target_team_or_side=_which_team(text),
        threshold_value=None,
        time_scope="first_half",
        outcome_variable="halftime_state",
        feature_set_needed="team_strength,half_goal_rates",
        likely_modeling_approach="logistic_regression",
        reusable_model_group="match_result_model",
        difficulty_rating=3,
        automation_feasibility="medium",
        manual_review_flag=True,
        notes="Halftime market not fully classified",
    )


# ── Player markets ────────────────────────────────────────────────────────────

# A "player market" subject line does NOT match any known team placeholder.
# We detect them by the question structure: "[Name] have at least 1 shot on target"
# or "[Name] score or assist a goal"

_PLAYER_SOT = _r(r"have at least \d+ shot(?:s)? on target")
_PLAYER_SCORE_OR_ASSIST = _r(r"score or assist a goal")
_PLAYER_SCORE_GOAL = _r(r"score a goal \(excluding own goals\)|score a goal$")

def _try_player(text: str) -> Optional[NormResult]:
    # Only treat as player market if neither {HOME} nor {AWAY} appears in the question
    has_team = bool(re.search(r"\{(?:HOME|AWAY)\}", text))

    if _match(_PLAYER_SOT, text):
        t_scope = "second_half" if "second half" in text else "regulation"
        return NormResult(
            normalized_question_template="{PLAYER} have at least 1 shot on target",
            question_family="player_markets",
            question_subtype="player_shot_on_target",
            target_team_or_side=None,
            threshold_value=1.0,
            time_scope=t_scope,
            outcome_variable="player_shot_on_target",
            feature_set_needed="lineup,player_form,xg_per_shot",
            likely_modeling_approach="logistic_regression,player_prop_model",
            reusable_model_group="player_shots_model",
            difficulty_rating=4,
            automation_feasibility="low",
            manual_review_flag=False,
            notes="Needs lineup data",
        )

    if _match(_PLAYER_SCORE_OR_ASSIST, text):
        return NormResult(
            normalized_question_template="{PLAYER} score or assist a goal",
            question_family="player_markets",
            question_subtype="player_goal_or_assist",
            target_team_or_side=None,
            threshold_value=None,
            time_scope="regulation",
            outcome_variable="player_goal_or_assist",
            feature_set_needed="lineup,player_form,xg,key_passes",
            likely_modeling_approach="logistic_regression,player_prop_model",
            reusable_model_group="player_goals_model",
            difficulty_rating=4,
            automation_feasibility="low",
            manual_review_flag=False,
            notes="Needs lineup data",
        )

    if _match(_PLAYER_SCORE_GOAL, text):
        return NormResult(
            normalized_question_template="{PLAYER} score a goal",
            question_family="player_markets",
            question_subtype="player_goal",
            target_team_or_side=None,
            threshold_value=None,
            time_scope="regulation",
            outcome_variable="player_goal",
            feature_set_needed="lineup,player_form,xg",
            likely_modeling_approach="logistic_regression,player_prop_model",
            reusable_model_group="player_goals_model",
            difficulty_rating=4,
            automation_feasibility="low",
            manual_review_flag=False,
            notes="Needs lineup data",
        )

    return None


# ── Public entry point ────────────────────────────────────────────────────────

_DISPATCH = [
    _try_halftime,         # must be before other patterns (starts with "at halftime,")
    _try_player,           # before team patterns to avoid player names matching team rules
    _try_offsides,
    _try_fouls,
    _try_cards,
    _try_shots,
    _try_corners,
    _try_goals,
    _try_team_scores,
    _try_match_result,
]


def normalize_market(market: dict, match: dict) -> dict:
    question = _get_question_text(market)
    if not question:
        return _fallback("", None)

    home = match.get("home_team") or ""
    away = match.get("away_team") or ""

    text_replaced, target = _replace_teams(question, home, away)
    text_lower = _clean(text_replaced)

    # Determine time scope for fields that need it
    time_scope = (
        "first_half" if _match(_IN_FIRST_HALF, question) else
        "second_half" if _match(_IN_SECOND_HALF, question) else
        "first_half" if _match(_AT_HALFTIME, question) else
        "regulation"
    )

    for fn in _DISPATCH:
        import inspect
        sig = inspect.signature(fn)
        n_params = len(sig.parameters)
        if n_params == 1:
            result = fn(text_lower)
        elif n_params == 2:
            result = fn(text_lower, time_scope)
        else:
            result = fn(text_lower, question, home, away, time_scope)
        if result is not None:
            # Override target if the function didn't set it
            if result.target_team_or_side is None:
                result.target_team_or_side = target
            return result.as_dict()

    return _fallback(question, target)


def _fallback(question: str, target) -> dict:
    cleaned = re.sub(r"\s+", " ", question).strip()
    return {
        "normalized_question_template": cleaned,
        "question_family": "other",
        "question_subtype": "unclassified",
        "target_team_or_side": target,
        "threshold_value": None,
        "time_scope": "unknown",
        "outcome_variable": "unknown",
        "feature_set_needed": "manual_review",
        "likely_modeling_approach": "manual",
        "reusable_model_group": "none",
        "difficulty_rating": 5,
        "automation_feasibility": "manual",
        "manual_review_flag": True,
        "notes": "Pattern not matched — needs manual classification",
    }
