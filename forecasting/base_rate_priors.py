"""
Match-agnostic empirical base-rate priors, cached to outputs/base_rate_priors.csv.

Seed values are the ones measured for the ESP-KSA work:
  - StatsBomb men's WC 2018+2022 (n=50 matches / 100 team-matches): offsides,
    2H corner/SoT dominance, penalties, red cards.
  - Football-Data.co.uk (n=7090 league matches): total SoT, corners, reds.

These are PRIORS, not final answers. compute.prior_with_favorite_scaling() and
temper_2h_dominance() adjust them per match using the match-result market.

Run `python -m forecasting.base_rate_priors` to (re)write the CSV. Pass
--recompute to re-run outputs/sb_base_rates.py + fd_base_rates.py from source
(slow, network) instead of using the cached seed values.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "outputs" / "base_rate_priors.csv"

# key, role, prior, source, notes
SEED: list[tuple[str, str, float, str, str]] = [
    # Offside P(>=2): from sb_offside_by_dominance.py (n=80 men's WC). Dominance barely
    # moves it (close 32% -> blowout 41%, plateaus). ALWAYS check the team's OWN multi-game
    # offside record first — it can override hard (e.g. Uruguay 2024: mean 2.3, P(>=2)=67%).
    ("offside_2plus", "favorite", 0.40, "sb_dominance_n80", "dominant team blowout bucket; team record overrides"),
    ("offside_2plus", "underdog", 0.40, "sb_dominance_n80", "underdog mean 1.30, P>=2 0.40"),
    ("offside_2plus", "neutral",  0.37, "statsbomb_wc_n50", "pooled team-matches"),
    ("dominant_more_2h_corners", "favorite", 0.54, "statsbomb_wc_n50", "tie-prone; lifted by fav strength + Poisson if props"),
    ("dominant_more_2h_sot",     "favorite", 0.64, "statsbomb_wc_n50", "scaled up by fav strength"),
    ("total_sot_8plus", "neutral", 0.57, "sb_wc_0.54 / fd_league_0.65", "WC cagier than leagues; blend"),
    ("penalty_in_match", "neutral", 0.42, "statsbomb_wc_n50", "VAR-era WC penalty heavy"),
    ("red_card_in_match", "neutral", 0.30, "sb_hist_0.06 -> 2026_adj", "2026 reds at record pace"),
    ("penalty_or_red", "neutral", 0.56, "composed", "1-(1-0.40)(1-0.30)"),
    ("total_corners_10plus", "neutral", 0.51, "fd_league_n7090", "mean ~9.8; market cross-check ~10.7"),
    # Poisson means for total-count questions (compute P(>=N) at any threshold via survival fn)
    ("mean_total_corners", "neutral", 9.8, "fd_league_n7090", "total corners/match"),
    ("mean_total_sot",     "neutral", 8.5, "sb_wc/fd_blend", "total shots on target/match"),
    ("mean_2h_sot",        "neutral", 4.4, "~half of total SoT", "2H total SoT"),
    ("mean_2h_cards",      "neutral", 2.6, "2026_adj", "2H total cards (booking surge)"),
    # Direct probabilities for comparison/derived questions
    ("underdog_more_fouls", "neutral", 0.56, "defending-side foul lean", "weaker/defending team fouls more"),
    ("halftime_lead_factor", "neutral", 0.74, "calib vs Kalshi 1H mkt (BEL-IRN 0.76)", "P(lead@HT)~factor*P(win); use direct 1H market when available"),
    # Player props (deferrable, low-confidence placeholders until lineup/odds)
    ("player_sot_midfielder", "neutral", 0.42, "placeholder", "midfielder 1+ SoT; refine w/ lineup/odds"),
    ("player_goal_or_assist_keyfwd", "neutral", 0.27, "placeholder", "key forward G+A; refine w/ odds"),
]


def write_seed() -> Path:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["key", "role", "prior", "source", "notes"])
        w.writerows(SEED)
    return OUT


def load() -> dict[tuple[str, str], float]:
    """Return {(key, role): prior}. Writes the seed CSV first if missing."""
    if not OUT.exists():
        write_seed()
    out: dict[tuple[str, str], float] = {}
    with OUT.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[(row["key"], row["role"])] = float(row["prior"])
    return out


def get(key: str, role: str = "neutral") -> float:
    priors = load()
    if (key, role) in priors:
        return priors[(key, role)]
    if (key, "neutral") in priors:
        return priors[(key, "neutral")]
    raise KeyError(f"no prior for {key!r}/{role!r}")


if __name__ == "__main__":
    if "--recompute" in sys.argv:
        print("Recompute path: run outputs/sb_base_rates.py and fd_base_rates.py, "
              "then update SEED. Using cached seed for now.")
    p = write_seed()
    print(f"Wrote {p}")
    for (k, r), v in load().items():
        print(f"  {k:28s} {r:9s} {v:.2f}")
