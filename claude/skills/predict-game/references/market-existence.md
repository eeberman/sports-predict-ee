# Market-existence map (Step 1)

Grounded in the project question taxonomy (`reports/question_taxonomy.md`,
368 markets / 37 matches). Use this to fill the "Market likely?" and
"Best proxy market" columns.

## Threshold-to-line rule

For any question with a threshold N ("N or more", "at least N"):
- **The target O/U line is (N − 0.5).** E.g. "9 or more corners" → look for `Total corners O/U 8.5`.
- Apply this mechanically; do not hunt for the exact integer line.
- If the question is a comparison ("X more than Y"), there is no threshold — use
  the direct comparison market or derive from two team lines.

## Family lookup table

| Question family / template | Market likely? | Best proxy market |
| --- | --- | --- |
| Match result — team win | Yes | 3-way 1X2; extract the team's leg |
| Match result — draw | Yes | 3-way 1X2; extract the draw leg |
| Total goals N+ (full match) | Yes | Total goals O/U **(N−0.5)** |
| Both teams to score | Yes | BTTS yes/no |
| BTTS AND N+ goals | Maybe (derive) | BTTS yes/no + total goals O/U **(N−0.5)** |
| Team to score (full match) | Yes | Team total goals O/U **0.5** |
| Team to score in 1H or 2H | Maybe | Team 1H/2H goals O/U **0.5** (else derive from HT/2H result) |
| 2H more goals than 1H | Maybe | "Half with most goals" 3-way |
| Team N+ goals (full match) | Yes | Team total goals O/U **(N−0.5)** |
| Halftime result — tied | Yes | HT 1X2; extract draw leg |
| Halftime result — team winning | Yes | HT 1X2; extract team's leg |
| Team N+ shots on target | Maybe | Team SoT O/U **(N−0.5)** |
| Total SoT N+ | Maybe | Total SoT O/U **(N−0.5)** |
| X more SoT than Y (full or 2H) | Maybe (derive) | "Team most SoT" 3-way (direct); else two team SoT O/U ladders |
| Total corners N+ | Yes | Total corners O/U **(N−0.5)** |
| X more corners than Y | Maybe (derive) | "Most corners" 3-way; else two team corner O/U ladders |
| Team N+ corners | Yes | Team corners O/U **(N−0.5)** |
| Total cards N+ | Yes | Total cards O/U **(N−0.5)** |
| X more cards than Y | Maybe | "Most cards" 3-way; else team cards O/U ladders |
| Penalty awarded OR red card | Maybe | Penalty yes/no + red card yes/no → derive P(A∪B) |
| Penalty awarded (standalone) | Unlikely | rarely a clean standalone market |
| Red card (standalone) | Unlikely | rarely a clean standalone market |
| Star player N+ SoT | Yes | Player SoT O/U **(N−0.5)** |
| Role player N+ SoT | Unlikely | usually untraded |
| Player to score a goal | Maybe (star) | Anytime goalscorer |
| Player to score or assist | Maybe (star) | Scorer-or-assist prop |
| Fouls comparison (X commit more) | Unlikely | rarely traded — base rate |
| Offside N+ | Unlikely | no standard market — base rate |
| 2H result (X more goals in 2H) | Yes | 2H moneyline 3-way (Kalshi usually has this) |

## Heuristics when a template isn't listed

- **Core match outcome** (result, totals, BTTS, team goals) → **Yes**.
- **Team-aggregate stat** (corners, cards, SoT) → **Yes** for totals, **Maybe
  (derive)** for "X more than Y" comparisons.
- **Player prop** → **Yes** for named stars in shots/scoring, **Unlikely** otherwise.
- **Exotic** (specific foul counts, first-X-of-2H, niche combos) → **Unlikely**.

"Maybe (derive)" means a direct market for the exact question is unlikely, but
the answer can be built by combining adjacent markets. Flag these in Step 1 so
the user hunts the *component* markets, and flag again in Step 3 as lower
confidence.
