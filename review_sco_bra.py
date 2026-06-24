import csv
from pathlib import Path

LOG = Path("outputs/results/results_log.csv")
rows = [r for r in csv.DictReader(LOG.open(encoding="utf-8")) if r["match"] == "SCO vs BRA"]

print(f"{'#':>2}  {'Prob':>5}  {'Pick':>4}  Question")
print("-" * 80)
for i, r in enumerate(rows, 1):
    p = int(r["our_prob"])
    pick = "YES" if p > 50 else "NO"
    flag = " <<< COIN FLIP" if 47 <= p <= 53 else (" <<< THIN EDGE" if 51 <= p <= 55 else "")
    print(f"{i:>2}  {p:>4}%  {pick:>4}  {r['question']}{flag}")
