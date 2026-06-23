"""
Persistent results log for settled/in-play Probability Cup questions.

Appends to outputs/results/results_log.csv so we can track out-of-sample
calibration (our prob vs crowd vs outcome vs RBP) across matches over time.

Brier per row = (our_prob/100 - outcome)^2 when outcome is known (0/1).
Use `python -m forecasting.results_log --summary` to print running calibration.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

LOG = Path(__file__).resolve().parents[1] / "outputs" / "results" / "results_log.csv"
FIELDS = ["match_date", "match", "question", "our_prob", "crowd_prob",
          "outcome", "rbp", "status", "note"]


def append(rows: list[dict]) -> Path:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    exists = LOG.exists()
    with LOG.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if not exists:
            w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})
    return LOG


def summary() -> None:
    if not LOG.exists():
        print("no log yet"); return
    rows = list(csv.DictReader(LOG.open(encoding="utf-8")))
    settled = [r for r in rows if r["status"] == "settled" and r["our_prob"] not in ("", None)]
    n = len(settled)
    if not n:
        print(f"{len(rows)} rows, none settled-with-forecast yet"); return
    briers, crowd_briers, rbp_sum = [], [], 0.0
    for r in settled:
        o = 1.0 if r["outcome"] == "YES" else 0.0
        briers.append((float(r["our_prob"])/100 - o) ** 2)
        if r["crowd_prob"]:
            crowd_briers.append((float(r["crowd_prob"])/100 - o) ** 2)
        if r["rbp"]:
            rbp_sum += float(r["rbp"])
    print(f"Settled (with our forecast): {n}")
    print(f"  Our mean Brier:   {sum(briers)/n:.4f}")
    if crowd_briers:
        print(f"  Crowd mean Brier: {sum(crowd_briers)/len(crowd_briers):.4f}")
    print(f"  Total RBP:        {rbp_sum:+.2f}")
    beat = sum(1 for r in settled if r["rbp"] and float(r["rbp"]) > 0)
    print(f"  Beat crowd on:    {beat}/{n}")


# ── ESP-KSA seed (from platform 'SETTLING' view, 2026-06-21) ────────────────────
ESP_KSA = [
    dict(match_date="2026-06-21", match="ESP vs KSA", question="Spain more 2H corners than Saudi",
         our_prob=77, crowd_prob=75, outcome="", rbp="", status="in_play", note="provisional YES, +3"),
    dict(match_date="2026-06-21", match="ESP vs KSA", question="Spain more SoT than Saudi 2H",
         our_prob=72, crowd_prob=77, outcome="", rbp="", status="in_play", note="below crowd; if NO +10"),
    dict(match_date="2026-06-21", match="ESP vs KSA", question="Spain caught offside 2+ times",
         our_prob=36, crowd_prob=54, outcome="YES", rbp=-16.47, status="settled",
         note="CONTRARIAN MISS: base-rate said favorite low-offside; vs ultra-deep block Spain played more through-balls and got caught MORE"),
    dict(match_date="2026-06-21", match="ESP vs KSA", question="BTTS AND 3+ goals",
         our_prob=25, crowd_prob=33, outcome="", rbp="", status="in_play", note="Spain 4-0 -> BTTS NO provisional, +7"),
    dict(match_date="2026-06-21", match="ESP vs KSA", question="Spain win",
         our_prob=88, crowd_prob=85, outcome="YES", rbp=2.54, status="settled", note="beat crowd; market-anchored"),
    dict(match_date="2026-06-21", match="ESP vs KSA", question="Saudi score in 2H",
         our_prob=21, crowd_prob=28, outcome="NO", rbp=5.40, status="settled", note="beat crowd"),
    dict(match_date="2026-06-21", match="ESP vs KSA", question="8+ total shots on target",
         our_prob=62, crowd_prob=65, outcome="YES", rbp=1.02, status="settled", note="beat crowd"),
    dict(match_date="2026-06-21", match="ESP vs KSA", question="Al-Dawsari score",
         our_prob=9, crowd_prob=18, outcome="NO", rbp=5.15, status="settled", note="beat crowd; market-anchored"),
    dict(match_date="2026-06-21", match="ESP vs KSA", question="Saudi caught offside 2+ times",
         our_prob="", crowd_prob=42, outcome="YES", rbp="", status="settled", note="WE SKIPPED — left points; both teams hit 2+ offsides in a 4-0"),
    dict(match_date="2026-06-21", match="ESP vs KSA", question="Penalty OR red card",
         our_prob="", crowd_prob=38, outcome="", rbp="", status="pending", note="WE SKIPPED"),
]


# ── BEL-IRN slate (pending; submitted manually from user account 2026-06-21) ─────
def _r(q, p, note):
    return dict(match_date="2026-06-21", match="BEL vs IRN", question=q, our_prob=p,
                crowd_prob="", outcome="", rbp="", status="pending", note=note)

BEL_IRN = [
    _r("Iran more fouls than Belgium", 66, "API-Football: Iran 12.7 vs Belgium 8.8 fouls/g; HOLD LOOSELY (thin)"),
    _r("2+ total cards in 2nd half", 82, "referee Herrera 5.6-5.85 cards/g (verified)"),
    _r("BTTS AND 3+ goals", 39, "Kalshi BTTS 47.5% - P(1-1)"),
    _r("Belgium more SoT than Iran 2H", 72, "FanDuel SoT ladders + each-half validation"),
    _r("4+ total SoT in 2H", 68, "FanDuel total-SoT mean 9.3 halved (symmetric; 2H-skew = upside, not priced)"),
    _r("Belgium win", 68, "Odds API h2h 9 books + Kalshi cross-check"),
    _r("Belgium winning at halftime", 51, "Kalshi 1H result de-vig"),
    _r("Tielemans 1+ SoT", 48, "FanDuel prop -105 de-vigged"),
    _r("Taremi score or assist", 25, "FanDuel Score-or-Assist +280 de-vigged"),
    _r("9+ total corners", 56, "FanDuel corners ladder de-vig (was base-rate 64)"),
]


# ── URU-CPV slate (submitted from user account 2026-06-21; Q3/Q5 skipped) ────────
def _u(q, p, status, note):
    return dict(match_date="2026-06-21", match="URU vs CPV", question=q, our_prob=p,
                crowd_prob="", outcome="", rbp="", status=status, note=note)

URU_CPV = [
    _u("Uruguay caught offside 2+ times", 60, "pending",
       "TRIANGULATED: league blowout 41% + Uruguay own record (Copa24 mean 2.3, P>=2 67%; +6 vs Saudi)"),
    _u("Both teams 1+ SoT in 2H", 67, "pending", "FanDuel SoT each-half (URU 0.95 x CPV 0.75)"),
    _u("Cape Verde more cards than Uruguay", "", "skipped", "thin CPV data; user skipped"),
    _u("Penalty awarded in match", 43, "pending", "SB WC base 0.42; lenient ref Eskas"),
    _u("Uruguay more fouls than Cape Verde", "", "skipped", "thin CPV data; user skipped"),
    _u("Cape Verde 2+ SoT in 2H", 41, "pending", "FanDuel CPV per-half SoT mean 1.40"),
    _u("Uruguay win", 68, "pending", "FanDuel h2h de-vig"),
    _u("Cape Verde score in 2H", 25, "pending", "FanDuel team total x 2H share"),
    _u("Darwin Nunez score or assist", 52, "pending", "FanDuel scorer+assist"),
    _u("Uruguay 6+ SoT", 56, "pending", "FanDuel Uruguay SoT ladder, mean 6.1"),
]


# ── ARG-AUT slate (settled; market-only approach, 2026-06-22) ────────────────────
# Pure single-market de-vig. 7 forecast, 3 skipped (no market: offside, 2H-SoT-h2h, cards).
ARG_AUT = [
    dict(match_date="2026-06-22", match="ARG vs AUT", question="2H more goals than 1H",
         our_prob=43, crowd_prob=51, outcome="NO", rbp=9.16, status="settled",
         note="beat crowd; Half-with-Most-Goals 3-way de-vig (8.1% hold, our noisiest); crowd's late-goals heuristic lost"),
    dict(match_date="2026-06-22", match="ARG vs AUT", question="Austria more corners than Argentina",
         our_prob=20, crowd_prob=30, outcome="YES", rbp=-13.35, status="settled",
         note="MISS below crowd; independent-Poisson on team corner ladders overstated favorite (corners +correlated within match); crowd 30 was sharper"),
    dict(match_date="2026-06-22", match="ARG vs AUT", question="Argentina win",
         our_prob=66, crowd_prob=70, outcome="YES", rbp=-0.44, status="settled",
         note="below crowd; h2h 3-way de-vig (3.8% hold); fav won, tiny loss to crowd's fav-bias"),
    dict(match_date="2026-06-22", match="ARG vs AUT", question="Match 2 or fewer total goals",
         our_prob=50, crowd_prob=44, outcome="YES", rbp=8.5, status="settled",
         note="beat crowd; O/U 2.5 under de-vig; crowd over/action-bias lost"),
    dict(match_date="2026-06-22", match="ARG vs AUT", question="Argentina 6+ SoT",
         our_prob=49, crowd_prob=54, outcome="NO", rbp=8.34, status="settled",
         note="beat crowd; ARG SoT ladder fit (mean 5.85, P>=6 ~50%); crowd fav-bias overrated dominance"),
    dict(match_date="2026-06-22", match="ARG vs AUT", question="Argentina score in 2H",
         our_prob=66, crowd_prob=68, outcome="YES", rbp=0.42, status="settled",
         note="beat crowd (thin); derived from 3 de-vigged ARG goal lines"),
    dict(match_date="2026-06-22", match="ARG vs AUT", question="Sabitzer 1+ SoT",
         our_prob=49, crowd_prob=43, outcome="YES", rbp=9.37, status="settled",
         note="beat crowd; player prop -105 de-vig (yes-only, est ~6% hold); crowd underrated"),
    # ── Skipped (no market) — recorded for learning ──
    dict(match_date="2026-06-22", match="ARG vs AUT", question="Austria caught offside 2+ times",
         our_prob="", crowd_prob=48, outcome="NO", rbp="", status="skipped",
         note="WE SKIPPED (no market). Base-rate would've said ~40% -> playing NO would have beaten crowd"),
    dict(match_date="2026-06-22", match="ARG vs AUT", question="Austria more SoT than Argentina 2H",
         our_prob="", crowd_prob=27, outcome="NO", rbp="", status="skipped",
         note="WE SKIPPED (no market). GOOD skip: team-data calc earlier said ~50%; crowd nailed 27% on a NO -> we'd have lost big"),
    dict(match_date="2026-06-22", match="ARG vs AUT", question="4+ total cards shown",
         our_prob="", crowd_prob=45, outcome="YES", rbp="", status="skipped",
         note="WE SKIPPED (no market). Crowd played safe at 45 and lost; referee card-avg would be the signal here"),
]


if __name__ == "__main__":
    if "--summary" in sys.argv:
        summary()
    elif "--seed-esp-ksa" in sys.argv:
        p = append(ESP_KSA)
        print(f"Appended {len(ESP_KSA)} ESP-KSA rows -> {p}")
        summary()
    elif "--seed-bel-irn" in sys.argv:
        p = append(BEL_IRN)
        print(f"Appended {len(BEL_IRN)} BEL-IRN rows (pending) -> {p}")
    elif "--seed-uru-cpv" in sys.argv:
        p = append(URU_CPV)
        sub = sum(1 for r in URU_CPV if r["status"] == "pending")
        print(f"Appended {len(URU_CPV)} URU-CPV rows ({sub} pending, {len(URU_CPV)-sub} skipped) -> {p}")
    elif "--seed-arg-aut" in sys.argv:
        p = append(ARG_AUT)
        settled = sum(1 for r in ARG_AUT if r["status"] == "settled")
        print(f"Appended {len(ARG_AUT)} ARG-AUT rows ({settled} settled, {len(ARG_AUT)-settled} skipped) -> {p}")
        summary()
    else:
        print("usage: --seed-esp-ksa | --seed-bel-irn | --seed-uru-cpv | --seed-arg-aut | --summary")
