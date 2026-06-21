# Provider Recommendations — SportsPredict Probability Cup

## 1. Executive Recommendation

Use **API-Football** as the primary data source for all match statistics (goals, shots, fouls, cards, corners, offsides, lineups, referee assignments). Use **The Odds API** for betting odds and implied probabilities. Use **Open-Meteo** for weather (free, no key). Skip **Sportmonks** for MVP — no key configured.

Priority integration order: API-Football → The Odds API → Open-Meteo.

## 2. Best Source for Odds

**The Odds API** — probe status: `ok`.
Covers: moneyline (h2h), totals, spreads/handicaps, BTTS. Implied probabilities derivable as 1/decimal_odds.
Player props (shot on target, goal scorer) depend on sport availability and bookmaker coverage — may not be available for all international tournaments.
Market availability for FIFA/international tournaments outside major leagues is limited; verify sport key availability before committing.

## 3. Best Source for Football Results / Events / Stats

**API-Football v3** — probe status: `ok`.
Covers all core team stats: goals, halftime score, shots on goal, total shots, fouls, yellow/red cards, corners, offsides, possession, goalkeeper saves.
Player stats (goals, assists, shots, minutes) available via /fixtures/players.
xG (expected_goals) present in statistics for some fixtures — not guaranteed for all competitions.
Match mapping via team name search is reliable; FIFA codes resolved via the existing FIFA_CODE_TO_NAME map.

## 4. Best Source for Confirmed Lineups

**API-Football v3** — probe status: `ok`.
Starting XI and substitutes available for completed fixtures. For upcoming fixtures, lineup data appears ~1h before kickoff.
**There is no explicit 'confirmed' flag** — treat any pre-match lineup as predicted until kickoff.
Player IDs and formations included.

## 5. Best Source for Weather

**Open-Meteo** (free, no key) — probe status: `ok`.
Hourly forecast (temperature, precipitation probability, wind speed, weather code) and historical actuals both available.
**Dependency**: Open-Meteo requires lat/lon coordinates per venue. API-Football provides venue.city but not coordinates.
Manual action required: build a venue → (lat, lon) lookup table for the ~10 stadiums used in this tournament, or integrate a geocoding step.

## 6. Referee Data: Include or Drop?

Referee assignment is available from API-Football (fixture.referee field). Historical tendency derivation is possible but quota-intensive (1 statistics call per historical fixture). **Recommendation: Include referee assignment only. Skip historical tendency stats for MVP — reopen after obtaining a paid API-Football plan or caching historical data.**

## 7. Biggest Missing Fields

All required fields are available (directly or derivable) from the tested providers.

## 8. Which Source to Integrate First

**API-Football** — covers 17 of 21 required field categories (directly or derived). Single HTTP client handles stats, lineups, and referee data.
Start with: GET /status → GET /fixtures (by team, completed) → GET /fixtures/statistics → GET /fixtures/lineups.

## 9. Which Source to Ignore for Now

**Sportmonks** — no API key configured; cannot assess. Its data quality for international fixtures is strong, but the free tier is limited. Revisit if API-Football gaps emerge.
**Player props from The Odds API** — low coverage for international tournaments; not reliable enough for MVP. Use API-Football /fixtures/players instead.

## 10. Manual Checks Required

1. **Venue coordinates**: Build a stadium → (lat, lon) table for the ~10 tournament venues. Open-Meteo cannot look up by name.
2. **Lineup timing**: Verify exactly when lineups appear on API-Football for these specific tournament matches. May differ from domestic leagues.
3. **Sport key for The Odds API**: Confirm which sport_key covers these matches (World Cup 2026, Copa América, AFCON, etc.) and that bookmakers offer the required market types.
4. **API-Football fixture mapping**: Validate that team name searches correctly resolve FIFA codes for all 45+ teams in the tournament, not just the tested sample.
5. **xG availability**: Confirm expected_goals is present in /fixtures/statistics for this specific competition — it is not guaranteed for all events.