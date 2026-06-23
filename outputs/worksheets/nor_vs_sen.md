# NOR vs SEN — forecast worksheet
**Date:** 2026-06-23 | **Event:** Jump Trading Probability Cup

---

## Odds anchors

| Market | Source | Raw | Hold |
|---|---|---|---|
| Full-game 1X2 | FanDuel | NOR +135 / Draw +230 / SEN +200 | 6.2% |
| Full-game 1X2 | Kalshi | NOR 43¢ / Tie 29¢ / SEN 31¢ | 3.0% |
| HT result | FanDuel | NOR +185 / Draw +115 / SEN +240 | 11.0% |
| HT result | Kalshi | Tie 44¢ / NOR 33¢ / SEN 25¢ | 2.0% |
| 2H result | Kalshi | NOR 39¢ / Tie 36¢ / SEN 26¢ | 1.0% |
| Total corners O/U 8.5 | FanDuel | Over -148 / Under +112 | 6.8% |
| NOR 6+ SoT | FanDuel | +165 (YES only) | one-sided |
| Mané anytime scorer | FanDuel | +260 (YES only) | one-sided |

---

## Base-rate estimates (no market)

### Q1 — Senegal caught offside 2+ times
Source: `offside_2plus` underdog prior = **40%** (SB WC n50, underdog mean 1.30 catches).
Senegal is the underdog (win prob ~30%). No team-specific offside data available to override.

### Q3 — Penalty OR red card shown
Source: `penalty_or_red` = **56%** = 1−(1−0.42)(1−0.30).
Penalty base 42% (VAR-era WC), red card 30% (2026 pace at record high). No market to cross-check.

### Q4 — Senegal more fouls than Norway
Source: `underdog_more_fouls` = **56%**. Defending/weaker side fouls more as a structural tendency.
Senegal is the underdog here → P(SEN fouls > NOR) = 56%.

### Q5 — 4+ total SoT in 2nd half
Source: `mean_2h_sot` = 4.4 → Poisson(4.4), P(X ≥ 4) = **64%**.
P(0)=1.2% P(1)=5.4% P(2)=11.9% P(3)=17.4% → P(≤3)=35.9% → P(≥4)=64.1%.

---

## De-vig steps

### Q2 — Norway more 2H goals than Senegal (DIRECT)
Kalshi 2H result: NOR 39¢ / Tie 36¢ / SEN 26¢ → sum = 101¢ (1% hold)
Proportional de-vig (all methods converge at 1% hold):
- **NOR wins 2H = 39/101 = 38.6% → 39%**
- Tie 2H = 36/101 = 35.6%
- SEN wins 2H = 26/101 = 25.7%

### Q6 — Norway win the match (DIRECT)
Primary: Kalshi NOR 43¢ / Tie 29¢ / SEN 31¢ → sum = 103¢
- **NOR win = 43/103 = 41.7% → 42%**

FanDuel cross-check (OR de-vig, 6.2% hold):
- Proportional: 40.1% | Odds-ratio: 40.3% | Shin: 40.4% | Additive: 40.5%
All methods cluster 40–41%; Kalshi (lower vig) at 42% used as primary.

### Q7 — HT match tied (DIRECT)
Primary: Kalshi Tie 44¢ / NOR 33¢ / SEN 25¢ → sum = 102¢
- **Tie = 44/102 = 43.1% → 43%**

FanDuel cross-check (OR de-vig, 11.0% hold):
- Proportional: 41.9% | Odds-ratio: 42.5% | Shin: 42.6% | Additive: 42.8%
Methods spread 42–43%; Kalshi 43% used as primary.

### Q8 — 9+ total corner kicks (DIRECT)
FanDuel O8.5 -148 / U8.5 +112 → sum = 106.8% (6.8% hold)
- Over raw: 148/248 = 59.7%
- Under raw: 100/212 = 47.2%
- Odds-ratio de-vig: **Over (YES) = 56.3% → 56%**
- Cross-check: Proportional 55.9% | Shin 56.3% | Additive 56.3% (all agree)

### Q9 — Norway 6+ shots on target (ONE-SIDED)
FanDuel: +165 → raw implied = 100/265 = **37.7% → 38%**
No NO price available; vig is embedded on the YES side → true fair prob slightly below. Treated as approximate.

### Q10 — Sadio Mané scores a goal (ONE-SIDED)
FanDuel anytime goalscorer: +260 → raw implied = 100/360 = **27.8% → 28%**
One-sided; vig embedded. Approximate.

---

## Final table

| # | Question | Fair prob | Pick | Method | Confidence |
|---|---|---|---|---|---|
| Q1 | Senegal caught offside 2+ times | **40%** | NO | base-rate (underdog prior, SB WC) | Low |
| Q2 | Norway more 2H goals than Senegal | **39%** | NO | direct 3-way (Kalshi 2H) | High |
| Q3 | Penalty OR red card shown | **56%** | YES | base-rate (pen 42% + red 30%) | Low |
| Q4 | Senegal more fouls than Norway | **56%** | YES | base-rate (underdog fouls more) | Low |
| Q5 | 4+ total SoT in 2nd half | **64%** | YES | base-rate Poisson(mean=4.4) | Low |
| Q6 | Norway win the match | **42%** | YES | direct 3-way (Kalshi) | High |
| Q7 | HT match tied | **43%** | YES | direct 3-way (Kalshi) | High |
| Q8 | 9+ total corner kicks | **56%** | YES | direct 2-way FanDuel OR | High |
| Q9 | Norway 6+ shots on target | **38%** | NO | one-sided raw (FanDuel) | Medium |
| Q10 | Sadio Mané scores a goal | **28%** | NO | one-sided raw (FanDuel) | Medium |

---

_Logged to results_log.csv (10 rows: all open) and devig_bakeoff.csv (4 rows: Q2/Q6/Q7/Q8). Q1/Q3/Q4/Q5 are base-rate only — crowd_prob blank (no market to compare against)._
