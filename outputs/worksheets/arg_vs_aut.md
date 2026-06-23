# ARG vs AUT — forecast worksheet

**Odds anchors:** Belgium/home 0.66 / draw 0.21 / away 0.12; over 2.5 = 0.49

| Q | prob | range | grounding | evidence | main risk |
|---|------|-------|-----------|----------|-----------|
| Will Austria be caught offside 2 or more times? | **40** | 34–46 | base_rate | SB offside>=2 underdog 0.40 | deep block / vertical attack |
| Will Austria have more shots on target than Argentina in the second half? | **50** | 44–56 | team_data | 2H SoT: Argentina 2.84 vs Austria 3.34 (8 g, statsbomb/api_football) | teammate variance |
| Will the second half have more goals than the first half? | **50** | 44–56 | base_rate | UNHANDLED goals_totals/half_goals_comparison | needs manual classification |
| Will Austria finish with more corner kicks than Argentina? | **39** | 33–45 | team_data | 2H corners: Argentina 2.41 vs Austria 2.34 (8 g, statsbomb/api_football) | game-state variance |
| Will Argentina win the match? | **66** | 60–72 | market | 3-way de-vig of h2h (home) | market move/late news |
| Will the match have 2 or fewer total goals? | **51** | 45–57 | market | Market under 2.5 = 0.51 | margin swing |
| Will there be 4 or more total cards shown? | **53** | 47–59 | base_rate | Poisson(mean=3.8) P(>= 4 cards) 2026 surge | calm game / lenient ref |
| Will Argentina have 6 or more shots on target? | **50** | 44–56 | base_rate | UNHANDLED shots/team_shots_over | needs manual classification |
| Will Argentina score in the second half? | **50** | 44–56 | base_rate | UNHANDLED goals_totals/team_score_in_second_half | needs manual classification |
| Will Marcel Sabitzer have at least 1 shot on target? | **42** | 36–48 | base_rate | placeholder midfielder 1+ SoT (DEFER / paste prop) | lineup/role unknown |

_NO auto-submit. Review, paste gap markets (BTTS / corners / player props), then submit manually._