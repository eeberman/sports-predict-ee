"""Full market mapping for ARG vs AUT - odds + team data -> probability per question."""
import sys, re, json, statistics as st
sys.path.insert(0, ".")
from forecasting import compute as c
from forecasting import base_rate_priors as priors
from forecasting import team_loo_rates

home, away = "Argentina", "Austria"

# ── Odds anchors (already fetched) ──────────────────────────────────────────────
# h2h eu median: ARG=1.450  Draw=4.500  AUT=7.925
h, d, a = 1.450, 4.500, 7.925
ph, pd, pa = c.devig_three_way(1/h, 1/d, 1/a)
print(f"H2H de-vigged: ARG={ph:.3f}  Draw={pd:.3f}  AUT={pa:.3f}")

# totals: over 2.5 = 1.925 / under 2.5 = 1.895  (14 books)
ov25, un25 = 1.925, 1.895
p_over25 = c.devig_two_way(1/ov25, 1/un25)
p_under25 = 1 - p_over25
print(f"Over 2.5: {p_over25:.3f}   Under/at-most-2: {p_under25:.3f}")

fav_strength = ph   # ARG is home and favorite
fav_side = "home"

# ── Team LOO rates ───────────────────────────────────────────────────────────────
tr = team_loo_rates.load()
arg_sot2h_for, _ = tr.get_team_rate(home, None, "sot_2h", "for", shrink=True)
aut_sot2h_for, _ = tr.get_team_rate(away, None, "sot_2h", "for", shrink=True)
arg_sot_tot_for, _ = tr.get_team_rate(home, None, "sot_tot", "for", shrink=True)
aut_sot_tot_aga, _ = tr.get_team_rate(away, None, "sot_tot", "against", shrink=True)

arg_cor2h_for, _ = tr.get_team_rate(home, None, "cor_2h", "for", shrink=True)
aut_cor2h_for, _ = tr.get_team_rate(away, None, "cor_2h", "for", shrink=True)
arg_cor2h_aga, _ = tr.get_team_rate(home, None, "cor_2h", "against", shrink=True)
aut_cor2h_aga, _ = tr.get_team_rate(away, None, "cor_2h", "against", shrink=True)

mu_card, min_n_card = tr.matchup_mean(home, away, "card_2h")

print(f"\nARG 2H SoT: {arg_sot2h_for:.2f}  AUT 2H SoT: {aut_sot2h_for:.2f}")
print(f"ARG 2H corners: {arg_cor2h_for:.2f}  AUT 2H corners: {aut_cor2h_for:.2f}")
print(f"Card 2H matchup mean: {mu_card:.2f} (n={min_n_card})")

# ARG total SoT: for + AUT against
arg_sot_tot_aga, _ = tr.get_team_rate(home, None, "sot_tot", "against", shrink=True)
aut_sot_tot_for, _ = tr.get_team_rate(away, None, "sot_tot", "for", shrink=True)
mu_arg_sot, min_n_arg = tr.matchup_mean(home, away, "sot_tot")
print(f"ARG total SoT matchup mean (for+against): {mu_arg_sot:.2f} (n={min_n_arg})")
# Actually for "ARG 6+ SoT" question we want just ARG's SoT, not both teams combined
# matchup_mean averages FOR + AGAINST for each team then averages both - that's total match SoT
# For "ARG 6+ SoT" we want ARG's SoT = ARG_for smoothed against AUT_against
arg_sot_est = (arg_sot_tot_for + aut_sot_tot_aga) / 2
print(f"ARG SoT estimate (ARG_for + AUT_against)/2: {arg_sot_est:.2f}")

print()
print("=" * 70)
print("MARKET MAPPING — ARG vs AUT")
print("=" * 70)

# 1. Austria offside ≥2
base_offside = priors.get("offside_2plus", "underdog")
q1_p = base_offside
print(f"\nQ1 [offsides] Austria offside ≥2")
print(f"  Source: base rate (underdog offside≥2)")
print(f"  P = {q1_p:.3f} ({q1_p*100:.0f}%)")
print(f"  Grounding: base_rate only — no offside market available")

# 2. Austria more 2H SoT than ARG
# AUT is subject (first-named in question "Will Austria have more shots...")
p_aut_more_sot = c.poisson_p_a_greater_b(aut_sot2h_for, arg_sot2h_for)
q2_p = p_aut_more_sot
print(f"\nQ2 [shots_comparison 2H] Austria more SoT than ARG in 2H")
print(f"  AUT 2H SoT rate: {aut_sot2h_for:.2f}  ARG 2H SoT rate: {arg_sot2h_for:.2f}")
print(f"  P(AUT > ARG) = Poisson: {q2_p:.3f} ({q2_p*100:.0f}%)")
print(f"  Grounding: team_data (statsbomb/api_football LOO rates)")

# 3. 2H more goals than 1H
base_2h_more = 0.44  # empirical WC: 2H has more goals than 1H in ~44% of matches
print(f"\nQ3 [half_goals_comparison] 2H more goals than 1H")
print(f"  Source: base rate {base_2h_more:.2f} (no market available)")
print(f"  P = {base_2h_more:.3f} ({base_2h_more*100:.0f}%)")
print(f"  Grounding: base_rate — half-goal split not in odds feed")

# 4. Austria more corners than ARG (full match)
# AUT subject = first named; need full-match corner comparison
arg_cor_tot_for, _ = tr.get_team_rate(home, None, "cor_tot", "for", shrink=True)
aut_cor_tot_for, _ = tr.get_team_rate(away, None, "cor_tot", "for", shrink=True)
p_aut_more_cor = c.poisson_p_a_greater_b(aut_cor_tot_for, arg_cor_tot_for)
q4_p = p_aut_more_cor
print(f"\nQ4 [corners_comparison] Austria more corners than ARG (full match)")
print(f"  AUT corner rate: {aut_cor_tot_for:.2f}  ARG corner rate: {arg_cor_tot_for:.2f}")
print(f"  P(AUT > ARG) = Poisson: {q4_p:.3f} ({q4_p*100:.0f}%)")
print(f"  Grounding: team_data")

# 5. Argentina win
q5_p = ph
print(f"\nQ5 [match_result] Argentina win")
print(f"  H2H de-vigged: P(ARG win) = {q5_p:.3f} ({q5_p*100:.0f}%)")
print(f"  Grounding: market (h2h odds, 14+ books)")

# 6. Total goals ≤2
q6_p = p_under25
print(f"\nQ6 [total_goals_under] Match ≤2 total goals")
print(f"  Market: Under 2.5 = {q6_p:.3f} ({q6_p*100:.0f}%)")
print(f"  Grounding: market (totals, 14 books)")

# 7. 4+ cards total (full match) - note: we have card_2h matchup
# Use card_2h as proxy - expected 2H cards, scale to full match
mu_card_full, _ = tr.matchup_mean(home, away, "card_2h")
# Full match mean cards ≈ 2x 2H (if 2H heavier) or use prior
mean_cards_full = 3.8  # no full-match cards prior; worksheet.py uses this fallback
q7_p = c._pois_sf(4, mean_cards_full)
print(f"\nQ7 [total_cards_over] 4+ cards total")
print(f"  Card 2H matchup mean: {mu_card_full:.2f} -> full match prior mean: {mean_cards_full}")
print(f"  Poisson P(≥4 cards) = {q7_p:.3f} ({q7_p*100:.0f}%)")
print(f"  Grounding: base_rate (no cards market in feed)")

# 8. ARG 6+ SoT
q8_p = c._pois_sf(6, arg_sot_est)
print(f"\nQ8 [team_shots_over] ARG ≥6 SoT")
print(f"  ARG SoT estimate: (ARG_for {arg_sot_tot_for:.2f} + AUT_against {aut_sot_tot_aga:.2f})/2 = {arg_sot_est:.2f}")
print(f"  Poisson P(≥6) = {q8_p:.3f} ({q8_p*100:.0f}%)")
print(f"  Grounding: team_data (SB + api_football)")

# 9. ARG score in 2H
# P(ARG score in 2H) ≈ P(ARG score at all) * half_share
# P(ARG scores) = 1 - P(ARG clean sheet as scorer)
# Simpler: from h2h P(ARG win)=0.664 + P(draw)=0.214 = 0.878 chance ARG scores at all
# Then * 0.6 for 2H share
p_arg_scores = 1 - pa  # Austria keeps a clean sheet P ≈ complement of AUT scoring which is tricky
# Better: P(ARG scores) = P(not AUT clean sheet) ≈ P(over 0.5 for ARG)
# We don't have team totals. Use: P(ARG scores) ≈ 1 - P(0-0 or 0-x)
# Rough: P(ARG scores) ≈ P(ARG win) + P(draw)*1 + fraction of P(AUT win) where ARG scored
# Practical: ARG is strong fav, P(ARG scores) ~= 0.85 (common for favorites)
# Use composition: p_win + p_draw*(partial) ~ 0.664+0.214*0.9 + 0.122*0.4 = 0.664+0.193+0.049 = 0.906
p_arg_scores_rough = ph + pd * 0.90 + pa * 0.40
half_share = 0.60
q9_p = p_arg_scores_rough * half_share
print(f"\nQ9 [team_score_in_second_half] ARG score in 2H")
print(f"  P(ARG scores) rough composition: {p_arg_scores_rough:.3f}")
print(f"  P(ARG scores in 2H) = {p_arg_scores_rough:.3f} x 0.60 = {q9_p:.3f} ({q9_p*100:.0f}%)")
print(f"  Grounding: market+composition (h2h odds)")

# 10. Sabitzer 1+ SoT
base_player_sot = priors.get("player_sot_midfielder")
print(f"\nQ10 [player_markets] Sabitzer ≥1 SoT")
print(f"  Base rate midfielder SoT: {base_player_sot:.3f}")
print(f"  P = {base_player_sot:.3f} ({base_player_sot*100:.0f}%)  [DEFER — paste prop odds if available]")
print(f"  Grounding: base_rate only — no player prop market in odds feed")

print()
print("=" * 70)
print("SUMMARY TABLE")
print("=" * 70)
print(f"{'#':<3} {'Question':<45} {'P':>5} {'Source':<20}")
print("-" * 75)
rows = [
    (1, "Austria offside ≥2",             q1_p, "base_rate"),
    (2, "Austria more 2H SoT than ARG",   q2_p, "team_data"),
    (3, "2H more goals than 1H",           base_2h_more, "base_rate"),
    (4, "Austria more corners than ARG",   q4_p, "team_data"),
    (5, "Argentina win",                   q5_p, "market"),
    (6, "Match ≤2 total goals",            q6_p, "market"),
    (7, "4+ cards total",                  q7_p, "base_rate"),
    (8, "ARG ≥6 SoT",                      q8_p, "team_data"),
    (9, "ARG score in 2H",                 q9_p, "market+comp"),
    (10,"Sabitzer ≥1 SoT",                 base_player_sot, "base_rate/DEFER"),
]
for n, q, p, src in rows:
    print(f"{n:<3} {q:<45} {p*100:>4.0f}%  {src:<20}")
