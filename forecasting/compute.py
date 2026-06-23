"""
Deterministic forecast math for the SportsPredict Probability Cup.

Pure functions only — no I/O. Each public `forecast_*` returns a Forecast.
The constants and default factors are calibrated to reproduce the hand-derived
ESP-KSA numbers (see tests/test_compute_regression or forecasting.cli --regression).

Scoring is Brier (a proper scoring rule): we output honest calibrated
probabilities, never exaggerated. Where a market prices the exact question we
de-vig it; otherwise we fall back to empirical base rates and composition.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Sequence


# ── Result type ────────────────────────────────────────────────────────────────

@dataclass
class Forecast:
    prob: float                 # final recommended probability, 0-100
    low: float                  # plausible range lower bound, 0-100
    high: float                 # plausible range upper bound, 0-100
    evidence: str
    main_risk: str
    grounding: str              # "market" | "market+composition" | "base_rate"

    def clamp(self) -> "Forecast":
        self.prob = _clamp(self.prob)
        self.low = _clamp(self.low)
        self.high = _clamp(self.high)
        return self


def _clamp(p: float, lo: float = 1.0, hi: float = 99.0) -> float:
    return max(lo, min(hi, p))


# ── Odds conversion + de-vig ───────────────────────────────────────────────────

def american_to_prob(odds: float) -> float:
    """American odds -> raw implied probability (with vig)."""
    o = float(odds)
    return 100.0 / (o + 100.0) if o > 0 else (-o) / (-o + 100.0)


def decimal_to_prob(dec: float) -> float:
    return 1.0 / float(dec)


def cents_to_prob(cents: float) -> float:
    """Kalshi/Polymarket cent price (0-100) -> probability 0-1."""
    return float(cents) / 100.0


def devig(raw_probs: Sequence[float]) -> list[float]:
    """Normalize a set of raw implied probabilities to sum to 1 (proportional de-vig)."""
    s = sum(raw_probs)
    if s <= 0:
        raise ValueError("sum of raw probabilities must be positive")
    return [p / s for p in raw_probs]


def devig_two_way(yes_raw: float, no_raw: float) -> float:
    """Return de-vigged P(yes)."""
    return devig([yes_raw, no_raw])[0]


def devig_three_way(home_raw: float, draw_raw: float, away_raw: float) -> tuple[float, float, float]:
    h, d, a = devig([home_raw, draw_raw, away_raw])
    return h, d, a


# ── Margin-aware de-vig methods (bake-off; odds_ratio is the current default) ────
#
# Proportional splits the overround in proportion to each leg, which leaves
# longshots too high / favorites too low when a book loads extra margin onto the
# longshot (favorite-longshot bias). The methods below attribute more margin to
# the longshot. ODDS_RATIO is the current chosen default for hold > ~5%; the
# others are logged alongside it (forecasting.devig_bakeoff) so settled Brier can
# tell us empirically which method to keep. Re-evaluate as data accumulates.

DEVIG_METHODS = ("proportional", "odds_ratio", "shin", "additive")
DEFAULT_DEVIG_METHOD = "odds_ratio"


def implied_margin(raw_probs: Sequence[float]) -> float:
    """Overround / vig of a complete set of raw implied probabilities."""
    return sum(raw_probs) - 1.0


def devig_additive(raw_probs: Sequence[float]) -> list[float]:
    """Equal-margin de-vig: subtract overround/n from each leg, clamp, renormalize.

    Crude — strips proportionally more from longshots; can clamp extreme longshots.
    """
    n = len(raw_probs)
    m = (sum(raw_probs) - 1.0) / n
    adj = [max(1e-6, p - m) for p in raw_probs]
    s = sum(adj)
    return [p / s for p in adj]


def devig_odds_ratio(raw_probs: Sequence[float], tol: float = 1e-12,
                     iters: int = 300) -> list[float]:
    """Odds-ratio (Cheung/Buchdahl) de-vig.

    Assumes one constant c scales every leg's fair odds-ratio up to the quoted
    odds-ratio; recover by dividing each odds-ratio by c, solving c so the fair
    probabilities sum to 1. c = 1 means no vig. Pure curve-fit, no bettor model.
    """
    ors = [p / (1.0 - p) for p in raw_probs]

    def total(c: float) -> float:
        s = 0.0
        for o in ors:
            g = o / c
            s += g / (1.0 + g)
        return s

    lo, hi = 1.0, 2.0                       # total(1) = booksum > 1 (decreasing in c)
    while total(hi) > 1.0 and hi < 1e9:
        hi *= 2.0
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        (lo, hi) = (mid, hi) if total(mid) > 1.0 else (lo, mid)
        if hi - lo < tol:
            break
    c = 0.5 * (lo + hi)
    return [(o / c) / (1.0 + o / c) for o in ors]


def devig_shin(raw_probs: Sequence[float], tol: float = 1e-12,
               iters: int = 300) -> list[float]:
    """Shin (1992/93) de-vig.

    Attributes the overround to adverse selection from better-informed money,
    which concentrates on longshots; z is the implied informed-money fraction,
    solved so the fair probabilities sum to 1. z = 0 reproduces proportional.
    NB: the 'insider/informed' trader is a *modeling device* for sharp money —
    it does NOT assume games are fixed.
    """
    B = sum(raw_probs)

    def pi(z: float, r: float) -> float:
        return (math.sqrt(z * z + 4.0 * (1.0 - z) * r * r / B) - z) / (2.0 * (1.0 - z))

    def total(z: float) -> float:
        return sum(pi(z, r) for r in raw_probs)

    lo, hi = 0.0, 0.999                      # total(0) = sqrt(B) > 1 (decreasing in z)
    if total(hi) > 1.0:                      # degenerate; fall back to proportional
        return [r / B for r in raw_probs]
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        (lo, hi) = (mid, hi) if total(mid) > 1.0 else (lo, mid)
        if hi - lo < tol:
            break
    z = 0.5 * (lo + hi)
    return [pi(z, r) for r in raw_probs]


def devig_method(raw_probs: Sequence[float], method: str = DEFAULT_DEVIG_METHOD) -> list[float]:
    """Dispatch to a named de-vig method. Default = odds_ratio (current choice)."""
    if method == "proportional":
        return devig(raw_probs)
    if method == "odds_ratio":
        return devig_odds_ratio(raw_probs)
    if method == "shin":
        return devig_shin(raw_probs)
    if method == "additive":
        return devig_additive(raw_probs)
    raise ValueError(f"unknown devig method: {method!r}")


def devig_all_methods(raw_probs: Sequence[float]) -> dict[str, list[float]]:
    """Return every method's de-vig of the same raw set, for the bake-off log."""
    return {m: devig_method(raw_probs, m) for m in DEVIG_METHODS}


# ── Poisson helpers ─────────────────────────────────────────────────────────────

def _pois_pmf(k: int, mu: float) -> float:
    return math.exp(-mu) * mu**k / math.factorial(k)


def _pois_sf(k: int, mu: float) -> float:
    """P(X >= k)."""
    if k <= 0:
        return 1.0
    return 1.0 - sum(_pois_pmf(i, mu) for i in range(k))


def fit_poisson_mean_from_ladder(thresholds: Sequence[int], probs: Sequence[float]) -> float:
    """
    Estimate a Poisson mean from a P(X >= threshold) ladder (e.g. team-corner
    over markets). Grid search minimizing squared error on the survival function.
    """
    pairs = list(zip(thresholds, probs))
    best_mu, best_err = 1.0, float("inf")
    mu = 0.1
    while mu <= 20.0:
        err = sum((_pois_sf(t, mu) - p) ** 2 for t, p in pairs)
        if err < best_err:
            best_err, best_mu = err, mu
        mu += 0.05
    return round(best_mu, 3)


def poisson_p_a_greater_b(mu_a: float, mu_b: float, kmax: int = 30) -> float:
    """P(A > B) for independent Poissons."""
    total = 0.0
    for kb in range(kmax + 1):
        pb = _pois_pmf(kb, mu_b)
        if pb < 1e-9 and kb > mu_b:
            break
        total += pb * _pois_sf(kb + 1, mu_a)
    return total


# ── Composition (combo questions) ───────────────────────────────────────────────

def compose_btts_and_over(p_btts: float, p_1_1_given_btts: float = 0.21) -> float:
    """
    P(both teams score AND total goals >= 3).
    Given BTTS, total is already >= 2; the only excluded scoreline is 1-1.
    ESP-KSA: 0.34 * (1 - 0.21) = 0.269.
    """
    return p_btts * (1.0 - p_1_1_given_btts)


def compose_team_scores_in_half(p_team_scores: float, half_share: float = 0.60) -> float:
    """
    P(team scores >= 1 in the given half) ~= P(team scores at all) * half_share.
    ESP-KSA Q8: 0.37 * 0.60 = 0.222.
    """
    return p_team_scores * half_share


# ── Game-state tempering for 2H "dominance" questions ───────────────────────────

# When a strong favorite leads, it eases off in the 2H and the underdog pushes,
# compressing the favorite's 2H share. We shrink the raw P(favorite wins 2H X)
# toward 0.5 by an amount that grows with favorite strength.
GAME_STATE_SHRINK = 0.55   # fraction of the (raw-0.5) gap retained after tempering

def temper_2h_dominance(raw_p: float, fav_strength: float) -> float:
    """
    raw_p: bottom-up P(favorite has more of stat X in 2H).
    fav_strength: de-vigged P(favorite wins match), 0.5-1.0.
    Stronger favorite -> more easing -> more shrink toward 0.5.
    Calibrated so ESP-KSA Q2 (raw 0.85, fav 0.88) -> ~0.77.
    """
    # shrink factor: 1.0 (no shrink) at fav 0.5, down to GAME_STATE_SHRINK at fav 1.0
    keep = 1.0 - (1.0 - GAME_STATE_SHRINK) * max(0.0, (fav_strength - 0.5) / 0.5)
    return 0.5 + (raw_p - 0.5) * keep


# ── Favorite-strength scaling for non-market base-rate questions ────────────────

DOMINANCE_LIFT = 0.21   # calibrated to ESP-KSA Q3 (base 0.64, fav 0.88 -> 0.72)

def prior_with_favorite_scaling(base_rate: float, fav_strength: float,
                                lift: float = DOMINANCE_LIFT) -> float:
    """
    For 'dominant team wins 2H X' base-rate questions without a direct market:
    final = base_rate + lift * (fav_strength - 0.5), clipped to [0,1].
    """
    return max(0.0, min(1.0, base_rate + lift * (fav_strength - 0.5)))


# ── Convenience: build a Forecast from a probability ────────────────────────────

def fc(p01: float, evidence: str, main_risk: str, grounding: str,
       band: float = 0.06) -> Forecast:
    """Wrap a probability (0-1) into a Forecast on a 0-100 scale with a +/- band."""
    p = p01 * 100.0
    return Forecast(
        prob=round(p, 0),
        low=round(p - band * 100, 0),
        high=round(p + band * 100, 0),
        evidence=evidence,
        main_risk=main_risk,
        grounding=grounding,
    ).clamp()
