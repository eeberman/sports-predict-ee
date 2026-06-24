"""Log SCO vs BRA predictions to results_log.csv and devig_bakeoff.csv."""
import sys
sys.path.insert(0, ".")
from forecasting.results_log import append as log_append
from forecasting.devig_bakeoff import append as bakeoff_append
from forecasting.compute import devig_all_methods, american_to_prob

MATCH = "SCO vs BRA"
DATE  = "2026-06-24"

rows = [
    dict(match_date=DATE, match=MATCH, status="open",
         question="Brazil more SoT than Scotland in 2H",
         our_prob=69, crowd_prob="", outcome="", rbp="",
         note="base-rate (dominant_more_2h_sot=0.64 + fav-scaling at BRA=0.755)"),
    dict(match_date=DATE, match=MATCH, status="open",
         question="Scotland caught offside 2+ times",
         our_prob=40, crowd_prob="", outcome="", rbp="",
         note="base-rate underdog (offside_2plus=0.40)"),
    dict(match_date=DATE, match=MATCH, status="open",
         question="Scotland scores first goal AND Brazil scores in 2H",
         our_prob=15, crowd_prob="", outcome="", rbp="",
         note="derived: P(SCO first)=22% x P(BRA 2H)=70%; Poisson lambda SCO=0.62 BRA=2.20"),
    dict(match_date=DATE, match=MATCH, status="open",
         question="Brazil finish with more corners than Scotland",
         our_prob=74, crowd_prob=74, outcome="", rbp="",
         note="Pinnacle 3-way OR de-vig: BRA=73.5%"),
    dict(match_date=DATE, match=MATCH, status="open",
         question="Scotland score at least 1 goal",
         our_prob=45, crowd_prob=45, outcome="", rbp="",
         note="Pinnacle+BetOnline team_totals O@0.5 OR de-vig: 45.4%"),
    dict(match_date=DATE, match=MATCH, status="open",
         question="Match has 3 or more total goals",
         our_prob=54, crowd_prob=54, outcome="", rbp="",
         note="Pooled O@2.5 (pmu_fr+unibet+pinnacle+onexbet) OR de-vig: 53.7%"),
    dict(match_date=DATE, match=MATCH, status="open",
         question="Brazil score in the second half",
         our_prob=70, crowd_prob="", outcome="", rbp="",
         note="derived: lambda_BRA=2.20, lambda_BRA_1H=1.01 from FD ladder, lambda_BRA_2H=1.19"),
    dict(match_date=DATE, match=MATCH, status="open",
         question="4 or more total cards shown",
         our_prob=39, crowd_prob=39, outcome="", rbp="",
         note="Pinnacle O@3.5=2.40/U@3.5=1.564 OR de-vig: 38.8%"),
    dict(match_date=DATE, match=MATCH, status="open",
         question="Scott McTominay have at least 1 SoT",
         our_prob=48, crowd_prob=48, outcome="", rbp="",
         note="Pool onexbet O@0.5=2.00 + WH O@0.5=1.91; 7% assumed hold OR de-vig: 47.7%"),
    dict(match_date=DATE, match=MATCH, status="open",
         question="Brazil score in the first half",
         our_prob=67, crowd_prob=67, outcome="", rbp="",
         note="FD Brazil 1H goals 3-way (+145/+135/+240) OR de-vig 63.7%; Kalshi HT cross-check 69.9%; blend 66.8%"),
]

path = log_append(rows)
print(f"Logged {len(rows)} rows to {path}")

# ── Bakeoff rows (market-backed multi-way questions only) ──────────
# Q4: corners 3-way (9.6% hold)
raw_c4 = [1/4.73, 1/9.19, 1/1.289]
m4 = devig_all_methods(raw_c4)
# Q4 YES side is BRA (index 2)

# Q5: team_totals O@0.5 pooled (4.4% hold)
raw_o5 = (1/2.10 + 1/2.10) / 2
raw_u5 = (1/1.75 + 1/1.77) / 2
raw_c5 = [raw_o5, raw_u5]
m5 = devig_all_methods(raw_c5)

# Q6: total goals O@2.5 pooled (5.4% hold)
raw_o6 = sum([1/1.70, 1/1.74, 1/1.85, 1/1.82]) / 4
raw_u6 = sum([1/2.00, 1/2.04, 1/2.07, 1/2.05]) / 4
raw_c6 = [raw_o6, raw_u6]
m6 = devig_all_methods(raw_c6)

# Q8: cards O@3.5 (5.6% hold)
raw_c8 = [1/2.40, 1/1.564]
m8 = devig_all_methods(raw_c8)

# Q9: McTominay O@0.5 (one-sided, 7% assumed hold)
raw_o9 = (1/2.00 + 1/1.91) / 2
raw_u9 = 1 + 0.07 - raw_o9
raw_c9 = [raw_o9, raw_u9]
m9 = devig_all_methods(raw_c9)

# Q10: Brazil 1H goals FD 3-way (12.8% hold)
raw_c10 = [american_to_prob(145), american_to_prob(135), american_to_prob(240)]
m10 = devig_all_methods(raw_c10)
# YES = scores (1 or 2+) = index 1+2 sum for each method
m10_yes = {mth: m10[mth][1] + m10[mth][2] for mth in m10}

def bakeoff_row(q, market, margin_pct, methods_yes, chosen="odds_ratio"):
    return dict(match_date=DATE, match=MATCH, question=q, market=market,
                margin_pct=round(margin_pct*100, 1), chosen_method=chosen,
                outcome="", status="open", note="",
                **{f"yes_{mth}": round(methods_yes[mth]*100, 1) for mth in methods_yes})

import math
def hold(raw): return sum(raw) - 1.0

bakeoff_rows = [
    bakeoff_row("Brazil finish with more corners than Scotland",
                "Pinnacle corners 3-way BRA=1.289 Draw=9.19 SCO=4.73",
                hold(raw_c4),
                {mth: m4[mth][2] for mth in m4}),       # BRA is leg 2
    bakeoff_row("Scotland score at least 1 goal",
                "Pinnacle+BetOnline team_totals Scotland O@0.5",
                hold(raw_c5),
                {mth: m5[mth][0] for mth in m5}),        # O is leg 0
    bakeoff_row("Match has 3 or more total goals",
                "Pooled O@2.5 (pmu_fr+unibet+pinnacle+onexbet)",
                hold(raw_c6),
                {mth: m6[mth][0] for mth in m6}),
    bakeoff_row("4 or more total cards shown",
                "Pinnacle O@3.5=2.40 / U@3.5=1.564",
                hold(raw_c8),
                {mth: m8[mth][0] for mth in m8}),
    bakeoff_row("Scott McTominay have at least 1 SoT",
                "Pool onexbet O@0.5=2.00 + WH O@0.5=1.91 (7% assumed hold)",
                hold(raw_c9),
                {mth: m9[mth][0] for mth in m9}),
    bakeoff_row("Brazil score in the first half",
                "FD Brazil 1H goals: 0=+145, 1=+135, 2+=+240 (YES=1+2+)",
                hold(raw_c10),
                m10_yes),
]

bp = bakeoff_append(bakeoff_rows)
print(f"Logged {len(bakeoff_rows)} bake-off rows to {bp}")
