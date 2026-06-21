# Referee Source Recommendations

## Context

**Discipline/fouls templates requiring referee features (5 total):**
- {HOME} commit more fouls than {AWAY}
- penalty kick awarded OR red card shown
- total cards {N}+
- {HOME} receive more cards than {AWAY}
- penalty kick awarded

**Required referee fields (from taxonomy `feature_set_needed`):** match_importance, referee_stats, team_aggression, team_discipline, team_foul_rates

---

## Q1: Is StatBunker usable for MVP referee features?

**Yes.** StatBunker was successfully fetched and parsed.

- URL: `https://www.statbunker.com/competitions/RefereeYellowCards?comp_id=776`
- Competition tested: **Premier League**
- Referees in table: 23 referees, current season Premier League
- Sample referee: Lewis Smith

**Fields confirmed directly from parsed table:**

| Field | Available |
|---|---|
| referee_name | yes |
| matches (P) | yes |
| yellow_cards | yes |
| red_cards | yes |
| red_yellow_cards (2nd bookings) | yes |
| yellow_per_match | yes |
| cards_per_match | yes |
| home_cards | yes |
| away_cards | yes |
| first_half_cards | yes |
| second_half_cards | yes |
| fouls | no |
| penalties | no |

**Automation feasibility:** medium

**Risk:** HTML structure may change without notice; no official API. Personal/research use only — do not scrape at high frequency. Correct comp_id must be identified per tournament (not auto-discoverable for international events).

---

## Q2: If yes, what fields can we use?

All fields in the table are parseable with BeautifulSoup (`html.parser`).
No JavaScript execution required — the page is server-rendered.

**Usable for model features:**
- `yellow_per_match` — primary yellow card tendency feature
- `cards_per_match` — total card rate (yellow + red)
- `red_cards` / `matches` — derived red card rate
- `home_cards` / `away_cards` — home/away card bias
- `fh_cards_avg_minute` / `sh_cards_avg_minute` — first/second half card timing

**Not available from StatBunker:**
- Fouls per match — not in this table; see FootyStats
- Penalty data — not in this table

**To find the correct comp_id for your tournament:**
1. Visit `https://www.statbunker.com/`
2. Click the competition you need
3. Extract `comp_id=NNN` from the URL
4. Fetch `https://www.statbunker.com/competitions/RefereeYellowCards?comp_id=NNN`

---

## Q3: If no (or for fouls data), which source should be tested next?

**FootyStats** is the recommended next candidate — the only free source observed to include fouls per game.

- URL: `https://footystats.org/referees`
- Known fields: referee_name, competition, season, matches, yellow_cards, red_cards, yellow_per_match, red_per_match, fouls_per_game
- Fouls available: **yes**
- Automation feasibility: low
- Risk: ToS restricts automated scraping. Free tier has full table access but limited historical depth. Referee pages exist per competition and per season.

For MVP, a manual one-time export from FootyStats covers the fouls feature for the ~5-8 referees in the tournament.

---

## Q4: Should referee data remain in the MVP?

**Yes, with scoped ambition.**

StatBunker provides referee card tendency data sufficient to cover the core discipline templates:

| Template | Referee feature needed | Source |
|---|---|---|
| `penalty kick awarded OR red card shown` | red card rate | StatBunker |
| `total cards N+` | cards per match | StatBunker |
| `{HOME} receive more cards than {AWAY}` | home/away card split | StatBunker |
| `{HOME} commit more fouls than {AWAY}` | fouls per match | FootyStats (manual) |
| `penalty kick awarded` | penalty rate | not available (drop from MVP) |

**Keep** referee features for: red card / total card / home-away card templates.
**Defer** fouls features until FootyStats manual extraction is done.
**Drop** penalty rate features — no free source available.

---

## Q5: Minimum viable referee feature set

| Field | Source | Availability | Used for |
|---|---|---|---|
| `referee_name` | API-Football fixture.referee | direct | join key |
| `ref_matches` | StatBunker | direct | denominator |
| `ref_yellow_total` | StatBunker | direct | feature |
| `ref_red_total` | StatBunker | direct | feature |
| `ref_yellow_per_match` | StatBunker | direct | primary card tendency |
| `ref_cards_per_match` | StatBunker | direct | total card rate |
| `ref_red_rate` | derived (red/matches) | derived | red card risk |
| `ref_home_cards` | StatBunker | direct | home/away bias |
| `ref_away_cards` | StatBunker | direct | home/away bias |

**Nice-to-have (not MVP):**
- `ref_fouls_per_match` — FootyStats manual
- `ref_fh_cards`, `ref_sh_cards` — StatBunker (available but lower priority)
- `ref_penalty_rate` — no free source identified

---

## Q6: How to combine referee features with API-Football team card stats

Use a **two-layer feature approach** for discipline markets:

**Layer 1 — Team card history (API-Football, historical fixtures)**
```
home_yellow_per_match_last10   # from /fixtures/statistics history
away_yellow_per_match_last10
home_fouls_per_match_last10
away_fouls_per_match_last10
```
These are match-time values derived from each team's last 10 fixtures.

**Layer 2 — Referee tendency prior (StatBunker, pre-match)**
```
ref_yellow_per_match           # from StatBunker competition table
ref_cards_per_match
ref_red_rate
ref_home_card_bias             # = ref_home_cards / ref_matches
ref_away_card_bias             # = ref_away_cards / ref_matches
```
These are static per-referee averages updated once per season.

**Timing:**
- Referee assignment (`fixture.referee`) is published 1-3 days before kickoff
- Until assignment is known, use a competition-average referee prior as fallback
- StatBunker lookup: fetch once per competition, cache the full table in memory/CSV

**Feature vector per discipline market at prediction time:**
```
ref_yellow_per_match      # referee baseline
ref_cards_per_match       # referee baseline
ref_red_rate              # referee baseline
home_yellow_per_match     # team history
away_yellow_per_match     # team history
home_fouls_per_match      # team history
away_fouls_per_match      # team history
match_importance          # group vs knockout
```