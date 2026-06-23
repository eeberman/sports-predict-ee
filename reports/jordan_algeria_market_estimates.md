# Jordan vs Algeria Market-Based Estimates

Prepared: 2026-06-23

These are market-only SportsPredict input scores for the Jordan vs Algeria Probability Cup match. Questions 1, 4, and 5 are intentionally skipped because they were not visible/inputtable in the working context.

## Final Scores

| Question | SportsPredict market | Score | Confidence | Basis |
| --- | --- | ---: | --- | --- |
| Q2 | Will there be 4 or more total shots on target in the second half? | 65 | Derived, weakest | No 2H-only SOT market found. Full-match SOT ladder and team SOT-in-each-half props imply high full-match SOT volume; half-split proxy used. |
| Q3 | Will Jordan score the first goal of the game and Algeria score in the second half? | 18 | Derived, weak | Jordan first goal devigged at 26.5%; Algeria 2H scoring proxy around 65-70% from Algeria both-halves and 1H scoring markets. |
| Q6 | Will Riyad Mahrez have at least 1 shot on target in the second half? | 49 | Derived | FanDuel inclusion-exclusion proxy from full-match 1+ SOT, 1H 1+ SOT, and each-half 1+ SOT markets. |
| Q7 | Will Jordan score at least 1 goal? | 52 | Clean | Jordan team total over 0.5 consensus was devigged; Kalshi and FanDuel cross-checks were close. |
| Q8 | At halftime, will the match be tied? | 40 | Clean | FanDuel halftime 3-way market: Jordan +500, Draw +125, Algeria +100; draw devigged. |
| Q9 | Will the match have 3 or more total goals? | 48 | Clean | Action Network consensus match total o2.5 -102 / u2.5 -120; over devigged. |
| Q10 | Will Mousa Al-Taamari have at least 1 shot on target? | 54 | Usable, one-sided | FanDuel/DraftKings one-sided 1+ SOT prices around -110 to -120; no "No" side found for full devig. |

## Calculation Notes

- American odds were converted to implied probabilities, then normalized across all sides when both sides or a 3-way market were available.
- Consensus rows were preferred when available. Otherwise, pasted book prices were used directly.
- Q3 first-goal market: Jordan +250, Algeria -250, No Goals +1200 normalized to Jordan first goal = 26.5%.
- Q3 Algeria 2H goal proxy:
  - Algeria 1H scoring from exact 1H goal market was about 58.5%.
  - Algeria to score in both halves at +146 raw implied about 40.7%.
  - Conditional proxy for Algeria 2H scoring was about 69.5%; combined with Jordan first goal gives about 18.4%.
- Q6 Mahrez 2H SOT proxy:
  - Full match 1+ SOT -270.
  - 1H 1+ SOT +120.
  - 1+ SOT in each half +370.
  - Inclusion-exclusion proxy: P(2H) = P(full) - P(1H) + P(each half) = about 49%.

## Input List

```text
Q2: 65
Q3: 18
Q6: 49
Q7: 52
Q8: 40
Q9: 48
Q10: 54
```
