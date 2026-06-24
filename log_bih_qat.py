"""Log BIH vs QAT results + bakeoff rows."""
import sys
sys.path.insert(0, ".")
from forecasting import results_log, devig_bakeoff
from forecasting.compute import american_to_prob, decimal_to_prob, cents_to_prob, devig_all_methods, implied_margin

MATCH = "BIH vs QAT"
DATE  = "2026-06-24"

rows = [
    dict(match_date=DATE, match=MATCH, question="BIH more 2H corners than QAT",
         our_prob=65, crowd_prob=65, outcome="", rbp="", status="open",
         note="derived: ind.Poisson 2H (lam_BIH=3.18,lam_QAT=1.73); cross-check Most-corners-each-half +120 sqrt->64%"),
    dict(match_date=DATE, match=MATCH, question="BIH score more goals than QAT in 2H",
         our_prob=60, crowd_prob=60, outcome="", rbp="", status="open",
         note="direct: Kalshi 2H ML (hold 1%); BetRivers cross-check 55%"),
    dict(match_date=DATE, match=MATCH, question="QAT more SoT than BIH in 2H",
         our_prob=14, crowd_prob=10, outcome="", rbp="", status="open",
         note="derived: ind.Poisson 2H (lam_BIH=3.18,lam_QAT=1.48); crowd=FD Team Most SoT full-match proxy (OR 10%)"),
    dict(match_date=DATE, match=MATCH, question="Penalty awarded OR red card",
         our_prob=56, crowd_prob=56, outcome="", rbp="", status="open",
         note="base-rate: composed 1-(1-0.42)*(1-0.30)=0.56; no market pulled"),
    dict(match_date=DATE, match=MATCH, question="QAT commit more fouls than BIH",
         our_prob=56, crowd_prob=56, outcome="", rbp="", status="open",
         note="base-rate: underdog_more_fouls=0.56; no market"),
    dict(match_date=DATE, match=MATCH, question="BIH receive more cards than QAT",
         our_prob=40, crowd_prob=40, outcome="", rbp="", status="open",
         note="base-rate: no prior; lean QAT(underdog/defending) more cards -> BIH ~40%"),
    dict(match_date=DATE, match=MATCH, question="BIH win the match",
         our_prob=70, crowd_prob=70, outcome="", rbp="", status="open",
         note="direct: Kalshi 1X2 (hold 2%); FD h2h cross-check 70.2%"),
    dict(match_date=DATE, match=MATCH, question="Match 2 or fewer total goals",
         our_prob=41, crowd_prob=41, outcome="", rbp="", status="open",
         note="direct: FD O/U 2.5 (hold 5.1%); BetRivers cross-check 38.5%"),
    dict(match_date=DATE, match=MATCH, question="Dzeko 1+ shot on target",
         our_prob=78, crowd_prob=78, outcome="", rbp="", status="open",
         note="direct one-sided: FD -450, shave 8% hold -> 77.8%"),
    dict(match_date=DATE, match=MATCH, question="QAT caught offside 2+ times",
         our_prob=40, crowd_prob=40, outcome="", rbp="", status="open",
         note="base-rate: underdog offside_2plus=0.40; no market"),
]

p = results_log.append(rows)
print(f"Logged {len(rows)} rows -> {p}")

# Bakeoff: Q7 (Kalshi 1X2, 2% hold), Q2 (Kalshi 2H ML, 1%), Q8 (FD 2-way, 5.1%)
raw7 = [cents_to_prob(71), cents_to_prob(19), cents_to_prob(12)]
all7 = devig_all_methods(raw7)
bakeoff_rows = [
    dict(match_date=DATE, match=MATCH, question="BIH win the match",
         market="Kalshi 1X2 3-way",
         margin_pct=round(implied_margin(raw7)*100,1),
         yes_proportional=round(all7["proportional"][0]*100,1),
         yes_odds_ratio=round(all7["odds_ratio"][0]*100,1),
         yes_shin=round(all7["shin"][0]*100,1),
         yes_additive=round(all7["additive"][0]*100,1),
         chosen_method="odds_ratio", outcome="", status="open", note="BIH leg"),
]

raw2 = [cents_to_prob(60), cents_to_prob(28), cents_to_prob(13)]
all2 = devig_all_methods(raw2)
bakeoff_rows.append(
    dict(match_date=DATE, match=MATCH, question="BIH score more goals than QAT in 2H",
         market="Kalshi 2H ML 3-way",
         margin_pct=round(implied_margin(raw2)*100,1),
         yes_proportional=round(all2["proportional"][0]*100,1),
         yes_odds_ratio=round(all2["odds_ratio"][0]*100,1),
         yes_shin=round(all2["shin"][0]*100,1),
         yes_additive=round(all2["additive"][0]*100,1),
         chosen_method="odds_ratio", outcome="", status="open", note="BIH leg")
)

raw8 = [american_to_prob(-158), american_to_prob(128)]
all8 = devig_all_methods(raw8)
bakeoff_rows.append(
    dict(match_date=DATE, match=MATCH, question="Match 2 or fewer total goals",
         market="FD O/U 2.5 2-way",
         margin_pct=round(implied_margin(raw8)*100,1),
         yes_proportional=round(all8["proportional"][1]*100,1),
         yes_odds_ratio=round(all8["odds_ratio"][1]*100,1),
         yes_shin=round(all8["shin"][1]*100,1),
         yes_additive=round(all8["additive"][1]*100,1),
         chosen_method="odds_ratio", outcome="", status="open", note="Under=YES")
)

raw3 = [american_to_prob(-600), american_to_prob(1000), american_to_prob(700)]
all3 = devig_all_methods(raw3)
bakeoff_rows.append(
    dict(match_date=DATE, match=MATCH, question="QAT more SoT than BIH in 2H",
         market="FD Team Most SoT 3-way (full-match proxy)",
         margin_pct=round(implied_margin(raw3)*100,1),
         yes_proportional=round(all3["proportional"][2]*100,1),
         yes_odds_ratio=round(all3["odds_ratio"][2]*100,1),
         yes_shin=round(all3["shin"][2]*100,1),
         yes_additive=round(all3["additive"][2]*100,1),
         chosen_method="odds_ratio", outcome="", status="open",
         note="QAT leg; our_prob=14 from 2H Poisson; crowd_proxy=10 from this market")
)

pb = devig_bakeoff.append(bakeoff_rows)
print(f"Bakeoff: {len(bakeoff_rows)} rows -> {pb}")
