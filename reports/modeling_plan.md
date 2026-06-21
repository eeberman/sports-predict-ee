# Modeling Plan — SportsPredict Probability Cup

_Generated: 2026-06-20 21:58_

## Core Answer: Do I Need One Model Per Question?

**No.** The market universe groups naturally into a small set of reusable model families.
Each family shares the same predictive logic and feature set; only the threshold or
target team changes between instances. Swapping those inputs — not rebuilding the model —
is how you cover hundreds of markets with a handful of models.

## Reusable Model Groups

### scoreline_model (81 markets)

- **Families covered:** goals_totals
- **Sample templates:** both teams score AND {N}+ total goals, match total goals over {N}, match total goals under {N}, second half more goals than first half, {HOME} score first goal AND {AWAY} score in 2H
- **Modeling approach:** poisson_model,logistic_regression
- **Feature set:** team_scoring_rate,defensive_strength,h2h,form
- **Avg difficulty:** 2.1
- **Automation:** high

### discipline_model (72 markets)

- **Families covered:** discipline, fouls
- **Sample templates:** penalty kick awarded, penalty kick awarded OR red card shown, total cards {N}+, {HOME} commit more fouls than {AWAY}, {HOME} receive more cards than {AWAY}
- **Modeling approach:** logistic_regression
- **Feature set:** referee_stats,team_aggression,match_importance
- **Avg difficulty:** 3.0
- **Automation:** medium

### shots_model (60 markets)

- **Families covered:** halftime, shots
- **Sample templates:** at halftime both teams have 1+ shot on target, total shots on target {N}+, {HOME} more shots on target than {AWAY}, {TEAM} have {N}+ shots on target
- **Modeling approach:** logistic_regression,team_stats_model
- **Feature set:** team_shot_rates,defensive_strength,match_style
- **Avg difficulty:** 3.0
- **Automation:** medium

### set_pieces_model (57 markets)

- **Families covered:** corners, halftime, offsides
- **Sample templates:** at halftime {HOME} more corner kicks than {AWAY}, total corner kicks {N}+, {HOME} more corner kicks than {AWAY}, {TEAM} caught offside {N}+ times
- **Modeling approach:** poisson_model,logistic_regression
- **Feature set:** team_attacking_depth,opponent_defensive_line
- **Avg difficulty:** 3.0
- **Automation:** medium

### player_shots_model (43 markets)

- **Families covered:** player_markets
- **Sample templates:** {PLAYER} have at least 1 shot on target
- **Modeling approach:** logistic_regression,player_prop_model
- **Feature set:** lineup,player_form,xg_per_shot
- **Avg difficulty:** 4.0
- **Automation:** low

### match_result_model (36 markets)

- **Families covered:** halftime, match_result
- **Sample templates:** at halftime match tied, at halftime {TEAM} winning, {TEAM} win the match
- **Modeling approach:** logistic_regression,elo_model,odds_implied
- **Feature set:** team_strength,h2h,form,odds
- **Avg difficulty:** 1.2
- **Automation:** high

### player_goals_model (19 markets)

- **Families covered:** player_markets
- **Sample templates:** {PLAYER} score a goal, {PLAYER} score or assist a goal
- **Modeling approach:** logistic_regression,player_prop_model
- **Feature set:** lineup,player_form,xg
- **Avg difficulty:** 4.0
- **Automation:** low

## Priority Ordering

Score = `market_count × (6 - avg_difficulty)` — higher is better ROI.

| reusable_model_group | count | avg_difficulty | score |
| --- | --- | --- | --- |
| scoreline_model | 81 | 2.1 | 317 |
| discipline_model | 72 | 3.0 | 213 |
| shots_model | 60 | 3.0 | 183 |
| match_result_model | 36 | 1.2 | 171 |
| set_pieces_model | 57 | 3.0 | 171 |
| player_shots_model | 43 | 4.0 | 86 |
| player_goals_model | 19 | 4.0 | 38 |

## Which Feature Sets Are Reusable?

| feature_set_needed | model_groups |
| --- | --- |
| lineup,player_form,xg | player_goals_model |
| lineup,player_form,xg,key_passes | player_goals_model |
| lineup,player_form,xg_per_shot | player_shots_model |
| referee_stats,team_aggression | discipline_model |
| referee_stats,team_aggression,match_importance | discipline_model |
| referee_stats,team_discipline,match_importance | discipline_model |
| team_attacking_depth,opponent_defensive_line | set_pieces_model |
| team_corner_rates,match_style | set_pieces_model |
| team_foul_rates,referee_stats | discipline_model |
| team_scoring_rate,defensive_strength,h2h | scoreline_model |
| team_scoring_rate,defensive_strength,h2h,form | scoreline_model |
| team_scoring_rate,h2h,form | scoreline_model |
| team_scoring_rate,half_goal_rates | scoreline_model |
| team_scoring_rate,half_goal_rates,defensive_strength | scoreline_model |
| team_scoring_rate,half_goal_rates,h2h | scoreline_model |
| team_shot_rates,defensive_strength | shots_model |
| team_shot_rates,defensive_strength,match_style | shots_model |
| team_strength,h2h,form,half_goal_rates | match_result_model |
| team_strength,h2h,form,odds | match_result_model |

## External Data Requirements

- **defensive_strength**: Historical match data
- **form**: Recent match results (last 5–10 games)
- **h2h**: Historical head-to-head data
- **half_goal_rates**: Source unknown — investigate
- **key_passes**: Source unknown — investigate
- **lineup**: Pre-match lineup data (SofaScore, ESPN, WhatsApp APIs) — needs fresh data
- **match_importance**: Inferred from competition stage / points position
- **match_style**: Historical team style indicators
- **odds**: Betting exchange / bookmaker odds API
- **opponent_defensive_line**: Source unknown — investigate
- **player_form**: Player-level stats — needs fresh data per gameweek
- **referee_stats**: Historical referee discipline data
- **team_aggression**: Source unknown — investigate
- **team_attacking_depth**: Source unknown — investigate
- **team_corner_rates**: Historical corner data
- **team_discipline**: Historical cards per match per team
- **team_foul_rates**: Source unknown — investigate
- **team_scoring_rate**: Historical match data (FBref, football-data.co.uk, StatsBomb)
- **team_shot_rates**: Historical shots data
- **team_strength**: Elo ratings, SPI (FiveThirtyEight), or computed from results
- **xg**: Source unknown — investigate
- **xg_per_shot**: xG data (Understat, StatsBomb)

## Next Build Steps

1. **Odds baseline** — Collect bookmaker odds for all markets in `match_result_model`
   and `scoreline_model`. Convert to probabilities. This gives you a fast, strong
   baseline for ~50% of all markets.

2. **Poisson goal model** — Fit a simple bivariate Poisson or Dixon-Coles model
   using historical match data. This covers `team_goal_model`, `scoreline_model`,
   and `margin_model` simultaneously.

3. **Half-time model** — Adapt the goal model with first/second-half goal rates.
   Covers `first_half` and `second_half` families.

4. **Tournament simulation** — If group-stage data is available, a simple Monte Carlo
   bracket sim covers all `tournament_progression_model` markets.

5. **Set pieces and discipline** — Lower priority; model if data is available and
   these market counts are material.

6. **Player markets** — Only if lineups are available before closing time. Low
   automation feasibility; handle manually for now.

7. **Manual review queue** — Review all markets flagged `manual_review_flag=True`
   one by one. Some may be mis-classified by the regex engine.
