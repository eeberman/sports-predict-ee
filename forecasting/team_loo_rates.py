"""
Team leave-one-out (LOO) rate lookups for live forecasting.

Loads cached WC 2018+2022 match data, builds per-team per-stat LOO rates,
applies k=3 shrinkage, and serves them up for comparison (who-does-more) and
threshold (total ≥ N) question types.

Compared to generic favorite-scaling, team-shrunk rates add real resolution on
comparison questions (who-more fouls +0.0171, corners +0.0177); on thresholds
(total SoT ≥8, corners ≥10, etc), only the matchup signal (for-rate +
opponent-against-rate) recovers any edge.
"""
from __future__ import annotations

from pathlib import Path
import csv
from collections import defaultdict, Counter
from statistics import mean, stdev

K_SHRINK = 3  # Empirical-Bayes shrinkage constant (optimized via k-sweep)
MIN_GAMES = 4  # Require ≥4 LOO games before using a team rate
STATS = ["off", "sot_tot", "sot_2h", "cor_tot", "cor_2h", "card_2h", "foul"]

# Map column suffixes in backtest_features.csv to stat names
CSV_COLS = {
    "off": ("off_h", "off_a"),
    "sot_tot": ("sot_tot_h", "sot_tot_a"),
    "sot_2h": ("sot_2h_h", "sot_2h_a"),
    "cor_tot": ("cor_tot_h", "cor_tot_a"),
    "cor_2h": ("cor_2h_h", "cor_2h_a"),
    "card_2h": ("card_2h_h", "card_2h_a"),
    "foul": ("foul_h", "foul_a"),
}

class TeamRates:
    """Load backtest data, build LOO rates, serve shrunk rates for live matches."""

    def __init__(self, features_csv: Path | str = None):
        outputs = Path(__file__).resolve().parents[2] / "outputs"
        if features_csv is None:
            # Prefer the extended pool (StatsBomb + API-Football national teams); fall
            # back to the original StatsBomb-only table if the extract hasn't run yet.
            extended = outputs / "team_features_extended.csv"
            features_csv = extended if extended.exists() else outputs / "backtest_features.csv"
        self.features_csv = Path(features_csv)
        self.matches = []
        self.records = defaultdict(list)  # team -> list of {mid, for, against, source}
        self.team_sources = defaultdict(Counter)  # team -> Counter(source -> n_games)
        self.pop_means = {}  # stat -> per-game mean
        self._load()

    def _load(self):
        """Load backtest features, build match records and population means."""
        with open(self.features_csv, encoding="utf-8") as fh:
            rdr = csv.DictReader(fh)
            for row in rdr:
                # Cast numerics
                for k in row:
                    if k not in ("match_id", "date", "home", "away"):
                        try:
                            row[k] = int(row[k])
                        except (ValueError, TypeError):
                            pass
                self.matches.append(row)

        # Build team records: {team: [{mid, for: {...}, against: {...}, source}]}
        for m in self.matches:
            mid = m["match_id"]
            home, away = m["home"], m["away"]
            source = m.get("source", "statsbomb")
            for team, side in [(home, "h"), (away, "a")]:
                opp_side = "a" if side == "h" else "h"
                for_rates = {}
                against_rates = {}
                for stat in STATS:
                    col_h, col_a = CSV_COLS[stat]
                    for_rates[stat] = m[col_h] if side == "h" else m[col_a]
                    against_rates[stat] = m[col_a] if side == "h" else m[col_h]
                self.records[team].append({
                    "mid": mid,
                    "for": for_rates,
                    "against": against_rates,
                    "source": source,
                })
                self.team_sources[team][source] += 1

        # Build population means (per-stat per-game average for-side, across all teams/matches)
        for stat in STATS:
            rates = []
            for team, recs in self.records.items():
                for rec in recs:
                    rates.append(rec["for"][stat])
            self.pop_means[stat] = mean(rates) if rates else 0

    def loo_mean(self, team: str, mid: int = None, stat: str = None, side: str = "for") -> tuple[float, int]:
        """
        Mean of stat for team. If mid is provided, excludes that match (LOO).
        If mid is None, uses full-sample mean (for live matches not in backtest).

        Returns (mean, n_games). Falls back to (pop_mean, 0) if team not found
        or n < MIN_GAMES.
        """
        if team not in self.records:
            return self.pop_means.get(stat, 0), 0

        rates = []
        for rec in self.records[team]:
            if mid is None or rec["mid"] != mid:
                rates.append(rec[side][stat])

        if len(rates) < MIN_GAMES:
            return self.pop_means.get(stat, 0), len(rates)

        return mean(rates), len(rates)

    def shrink(self, raw: float, n: int, pop: float | None = None) -> float:
        """Apply empirical-Bayes shrinkage: (n * raw + k * pop) / (n + k)."""
        if pop is None:
            pop = 0
        if n == 0:
            return pop
        return (n * raw + K_SHRINK * pop) / (n + K_SHRINK)

    def get_team_rate(self, team: str, mid: int, stat: str, side: str = "for", shrink: bool = True) -> tuple[float, int]:
        """
        Get team rate for a stat, LOO, optionally shrunk.

        Returns (rate, n_games). If n_games < MIN_GAMES, returns (pop_mean, 0).
        """
        raw, n = self.loo_mean(team, mid, stat, side)
        if n < MIN_GAMES:
            return self.pop_means.get(stat, 0), 0
        if shrink:
            shrunken = self.shrink(raw, n, self.pop_means.get(stat, 0))
            return shrunken, n
        return raw, n

    def source_tag(self, team: str) -> str:
        """Provenance label for evidence text: the dominant data source for a team."""
        c = self.team_sources.get(team)
        if not c:
            return "none"
        return c.most_common(1)[0][0]

    def matchup_mean(self, home: str, away: str, stat: str) -> tuple[float, int]:
        """
        Matchup signal for thresholds: (home_for + away_against) full-sample rates shrunk.

        For threshold questions like "total SoT ≥ 8", this is more powerful than
        either team alone. Returns the composite Poisson mean and the min n.
        """
        home_for, n_hf = self.get_team_rate(home, None, stat, "for", shrink=True)
        away_against, n_aa = self.get_team_rate(away, None, stat, "against", shrink=True)
        min_n = min(n_hf, n_aa)
        return home_for + away_against, min_n


# Singleton cache
_cache = None

def load() -> TeamRates:
    """Load or return cached team rates."""
    global _cache
    if _cache is None:
        _cache = TeamRates()
    return _cache
