# New Zealand vs EGY — forecast worksheet

**Odds anchors:** Belgium/home 0.17 / draw 0.24 / away 0.59; over 2.5 = 0.45

| Q | prob | range | grounding | evidence | main risk |
|---|------|-------|-----------|----------|-----------|
| Will Egypt be caught offside 2 or more times? | **40** | 34–46 | base_rate | SB offside>=2 favorite 0.40 | deep block / vertical attack |
| Will New Zealand commit more fouls than Egypt? | **56** | 50–62 | base_rate | underdog-fouls-more prior 0.56 (subj dog) | referee/style variance |
| In the second half, will New Zealand have more shots on target than Egypt? | **66** | 60–72 | base_rate | SB 2H-SoT dominance 0.64, fav-scaled (fav 0.59) | game-state easing / 2H tie |
| Will the second half have more goals than the first half? | **50** | 44–56 | base_rate | UNHANDLED goals_totals/half_goals_comparison | needs manual classification |
| Will Egypt finish with more corner kicks than New Zealand? | **55** | 49–61 | base_rate | 2H corner dominance, tempered | game-state easing |
| Will New Zealand win the match? | **17** | 11–23 | market | 3-way de-vig of h2h (home) | market move/late news |
| Will the match have 2 or fewer total goals? | **55** | 49–61 | market | Market under 2.5 = 0.55 | margin swing |
| Will there be 4 or more total cards shown? | **53** | 47–59 | base_rate | Poisson(mean=3.8) P(>= 4 cards) 2026 surge | calm game / lenient ref |
| Will Ben Waine have at least 1 shot on target? | **42** | 36–48 | base_rate | placeholder midfielder 1+ SoT (DEFER / paste prop) | lineup/role unknown |
| Will Mahmoud Trezeguet score or assist a goal (excluding own goals)? | **27** | 21–33 | base_rate | placeholder key-forward G+A (DEFER / paste prop) | lineup/role unknown |

_NO auto-submit. Review, paste gap markets (BTTS / corners / player props), then submit manually._