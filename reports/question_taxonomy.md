# SportsPredict Probability Cup — Question Taxonomy

_Generated: 2026-06-20 21:58_

## Summary

| Item | Count |
|------|-------|
| Total markets | 368 |
| Unique question templates | 29 |
| Question families | 9 |
| Matches covered | 37 |

## Question Families

### goals_totals (81 markets)

| normalized_question_template | count_markets | automation_feasibility | suggested_priority |
| --- | --- | --- | --- |
| both teams score AND {N}+ total goals | 15 | high | 2 |
| {TEAM} score in second half | 14 | high | 2 |
| match total goals over {N} | 11 | high | 2 |
| {TEAM} score at least 1 goal | 11 | high | 2 |
| match total goals under {N} | 10 | high | 2 |
| {HOME} score more goals than {AWAY} in second half | 6 | high | 2 |
| {HOME} score first goal AND {AWAY} score in 2H | 4 | medium | 3 |
| {TEAM} score in first half | 4 | high | 2 |
| second half more goals than first half | 3 | high | 2 |
| {TEAM} score first goal of second half | 3 | medium | 3 |

### player_markets (62 markets)

| normalized_question_template | count_markets | automation_feasibility | suggested_priority |
| --- | --- | --- | --- |
| {PLAYER} have at least 1 shot on target | 43 | low | 4 |
| {PLAYER} score or assist a goal | 12 | low | 4 |
| {PLAYER} score a goal | 7 | low | 4 |

### shots (57 markets)

| normalized_question_template | count_markets | automation_feasibility | suggested_priority |
| --- | --- | --- | --- |
| {HOME} more shots on target than {AWAY} | 29 | medium | 3 |
| {TEAM} have {N}+ shots on target | 18 | medium | 3 |
| total shots on target {N}+ | 10 | medium | 3 |

### discipline (43 markets)

| normalized_question_template | count_markets | automation_feasibility | suggested_priority |
| --- | --- | --- | --- |
| penalty kick awarded OR red card shown | 18 | medium | 3 |
| total cards {N}+ | 12 | medium | 3 |
| {HOME} receive more cards than {AWAY} | 10 | medium | 3 |
| penalty kick awarded | 3 | low | 4 |

### fouls (29 markets)

| normalized_question_template | count_markets | automation_feasibility | suggested_priority |
| --- | --- | --- | --- |
| {HOME} commit more fouls than {AWAY} | 29 | medium | 3 |

### offsides (29 markets)

| normalized_question_template | count_markets | automation_feasibility | suggested_priority |
| --- | --- | --- | --- |
| {TEAM} caught offside {N}+ times | 29 | medium | 3 |

### match_result (27 markets)

| normalized_question_template | count_markets | automation_feasibility | suggested_priority |
| --- | --- | --- | --- |
| {TEAM} win the match | 27 | high | 1 |

### corners (25 markets)

| normalized_question_template | count_markets | automation_feasibility | suggested_priority |
| --- | --- | --- | --- |
| total corner kicks {N}+ | 16 | medium | 3 |
| {HOME} more corner kicks than {AWAY} | 9 | medium | 3 |

### halftime (15 markets)

| normalized_question_template | count_markets | automation_feasibility | suggested_priority |
| --- | --- | --- | --- |
| at halftime match tied | 6 | high | 2 |
| at halftime {TEAM} winning | 3 | high | 2 |
| at halftime {HOME} more corner kicks than {AWAY} | 3 | medium | 3 |
| at halftime both teams have 1+ shot on target | 3 | high | 2 |

## Top 20 Most Common Templates

| normalized_question_template | count_markets | question_family | reusable_model_group |
| --- | --- | --- | --- |
| {PLAYER} have at least 1 shot on target | 43 | player_markets | player_shots_model |
| {HOME} commit more fouls than {AWAY} | 29 | fouls | discipline_model |
| {TEAM} caught offside {N}+ times | 29 | offsides | set_pieces_model |
| {HOME} more shots on target than {AWAY} | 29 | shots | shots_model |
| {TEAM} win the match | 27 | match_result | match_result_model |
| {TEAM} have {N}+ shots on target | 18 | shots | shots_model |
| penalty kick awarded OR red card shown | 18 | discipline | discipline_model |
| total corner kicks {N}+ | 16 | corners | set_pieces_model |
| both teams score AND {N}+ total goals | 15 | goals_totals | scoreline_model |
| {TEAM} score in second half | 14 | goals_totals | scoreline_model |
| total cards {N}+ | 12 | discipline | discipline_model |
| {PLAYER} score or assist a goal | 12 | player_markets | player_goals_model |
| match total goals over {N} | 11 | goals_totals | scoreline_model |
| {TEAM} score at least 1 goal | 11 | goals_totals | scoreline_model |
| {HOME} receive more cards than {AWAY} | 10 | discipline | discipline_model |
| match total goals under {N} | 10 | goals_totals | scoreline_model |
| total shots on target {N}+ | 10 | shots | shots_model |
| {HOME} more corner kicks than {AWAY} | 9 | corners | set_pieces_model |
| {PLAYER} score a goal | 7 | player_markets | player_goals_model |
| {HOME} score more goals than {AWAY} in second half | 6 | goals_totals | scoreline_model |

## Match Coverage

| match_name | match_id | market_count |
| --- | --- | --- |
| ALG vs AUT | c5b16a05-c823-48c9-ac79-8923c44df945 | 10 |
| ARG vs AUT | a74bb45d-e405-4acb-9783-f6e7fcf10097 | 10 |
| NOR vs FRA | 82a50c24-ee1a-4588-8652-02a0f79206e5 | 10 |
| NOR vs SEN | c83e4786-8b8d-4f53-8aec-809f721a0555 | 10 |
| New Zealand vs BEL | 790fcb5f-e9ae-4b31-9608-17977ef89a1a | 10 |
| New Zealand vs EGY | 19a6ff2c-4d39-491d-8f19-085531f55120 | 10 |
| PAN vs CRO | 48abc36d-a811-4579-983b-fe9805c1dc7b | 10 |
| PAN vs ENG | 3d8d1b96-0cca-4fd5-8f21-ad44f457d689 | 10 |
| POR vs UZB | 69befda5-5418-4a6e-9516-295139e79565 | 10 |
| RSA vs KOR | d6eae6b4-74f1-469b-8d4c-25c01622a272 | 10 |
| SCO vs BRA | 27de95f5-f061-4819-a1ce-1dd294a17d43 | 10 |
| SEN vs IRQ | 236d7678-555c-42cc-99ea-91f59c0edd9e | 10 |
| SUI vs CAN | afe9f639-489e-44cb-b903-41f18169387e | 10 |
| TUN vs JPN | f0b2f474-e506-4abc-ae8d-cf9ce8ef2d31 | 10 |
| TUN vs NED | 1838eca2-efa1-4dfc-b4f2-c38a69050049 | 10 |
| TUR vs USA | a7ab762f-7530-4cf0-a540-489b141f788a | 10 |
| URU vs CPV | 54136530-c99d-4d0b-a268-21271487c339 | 10 |
| MAR vs Haiti | 11d5723d-eb32-450b-aed1-714150081f00 | 10 |
| JPN vs SWE | d7378d49-146a-4c91-bd5c-fb491f17516a | 10 |
| JOR vs ARG | 03995b66-4456-4acf-bc95-cf9f1645be0c | 10 |
| JOR vs ALG | 5398e565-2759-4c71-abea-77f209bd75f9 | 10 |
| BEL vs IRN | 260eafaf-0e4b-468d-9418-bc05b13de89f | 10 |
| BIH vs QAT | 02e80d7b-edb2-43a1-a0b8-f1bd1c089cc6 | 10 |
| COD vs UZB | 03d5b4fb-f094-43e8-ae66-b99987ea03e7 | 10 |
| COL vs COD | 91b6a806-37ac-4799-8341-7dd80d00baeb | 10 |
| COL vs POR | d55a394e-9ba6-4a4a-8112-994724f4b464 | 10 |
| CPV vs KSA | 739bd122-6bcb-4690-8439-c5ca45f8bc22 | 10 |
| CRO vs GHA | 780369fb-f757-4166-998b-c2db986f87f4 | 10 |
| URU vs ESP | af3dcfc5-29ac-423c-b9ae-62093c105955 | 10 |
| Curacao vs CIV | 088d10e4-bdd4-4987-951a-65a978f130a3 | 10 |
| ECU vs GER | 8a2b38f9-caf6-49c0-a281-72eda09fd948 | 10 |
| EGY vs IRN | f24da99f-ccaf-451f-ae8b-f402047ee832 | 10 |
| ENG vs GHA | ffa7a87a-1a80-40af-9798-3d3dc321d17b | 10 |
| ESP vs KSA | a1ee9ab8-f139-4ec9-be33-953559565969 | 10 |
| FRA vs IRQ | e627d774-f157-458a-8b82-acd8d39d6cdc | 10 |
| PAR vs AUS | 3e92988d-4e6f-4028-92ef-2ae7cfd8fb84 | 9 |
| CZE vs MEX | e1bc50c6-c39e-454a-b6be-bbe6e3ae6261 | 9 |

## Analysis

**Repeating templates (count > 1):** 29 of 29 templates appear in more than one market.

**Model group coverage:**

| group | markets |
| --- | --- |
| scoreline_model | 81 |
| discipline_model | 72 |
| shots_model | 60 |
| set_pieces_model | 57 |
| player_shots_model | 43 |
| match_result_model | 36 |
| player_goals_model | 19 |

**Templates needing fresh external data:** 8

{PLAYER} have at least 1 shot on target, {HOME} commit more fouls than {AWAY}, penalty kick awarded OR red card shown, total cards {N}+, {PLAYER} score or assist a goal, {HOME} receive more cards than {AWAY}, {PLAYER} score a goal, penalty kick awarded

## What to Build Next

Priority order based on market count × automation feasibility:

| question_family | count | automation | score |
| --- | --- | --- | --- |
| goals_totals | 81 | high | 243 |
| shots | 57 | medium | 114 |
| discipline | 43 | medium | 86 |
| match_result | 27 | high | 81 |
| player_markets | 62 | low | 62 |
| fouls | 29 | medium | 58 |
| offsides | 29 | medium | 58 |
| corners | 25 | medium | 50 |
| halftime | 15 | high | 45 |
