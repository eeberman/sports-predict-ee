# BEL vs IRN — forecast worksheet

**Odds anchors:** Belgium/home 0.68 / draw 0.20 / away 0.12; over 2.5 = 0.53

| Q | prob | range | grounding | evidence | main risk |
|---|------|-------|-----------|----------|-----------|
| Will there be 2 or more total cards shown in the second half? | **73** | 67–79 | base_rate | Poisson(mean=2.6) P(>= 2 cards) 2026 surge | calm game / lenient ref |
| Will Mehdi Taremi score or assist a goal (excluding own goals)? | **27** | 21–33 | base_rate | placeholder key-forward G+A (DEFER / paste prop) | lineup/role unknown |
| Will Belgium have more shots on target than Iran in the second half? | **68** | 62–74 | base_rate | SB 2H-SoT dominance 0.64, fav-scaled (fav 0.68) | game-state easing / 2H tie |
| Will Belgium win the match? | **68** | 62–74 | market | 3-way de-vig of h2h (home) | market move/late news |
| Will there be 4 or more total shots on target in the second half? | **64** | 58–70 | base_rate | Poisson(mean=4.4) P(>= 4) | compact match / few shots |
| Will there be 9 or more total corner kicks? | **64** | 58–70 | base_rate | Poisson(mean=9.8) P(>= 9 corners) [PASTE corner mkt to sharpen] | low-tempo match |
| Will both teams score AND the match have 3 or more total goals? | **37** | 31–43 | base_rate | BTTS modeled from over 2.5 (no BTTS market — PASTE) | favorite clean sheet |
| Will Youri Tielemans have at least 1 shot on target? | **42** | 36–48 | base_rate | placeholder midfielder 1+ SoT (DEFER / paste prop) | lineup/role unknown |
| Will Iran commit more fouls than Belgium? | **56** | 50–62 | base_rate | underdog-fouls-more prior 0.56 (subj dog) | referee/style variance |
| At halftime, will Belgium be winning? | **44** | 38–50 | base_rate | P(lead@HT) = 0.65 x P(win) 0.68 | 1H cagey / early goal swing |

_NO auto-submit. Review, paste gap markets (BTTS / corners / player props), then submit manually._