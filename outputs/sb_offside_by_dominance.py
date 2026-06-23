"""
Offside base rate CONDITIONED ON DOMINANCE.

Question: when a team heavily out-shoots its opponent (the 'favorite bombarding a
deep block' archetype, e.g. Uruguay vs Cape Verde), how often is that DOMINANT
team caught offside 2+ times?

Builds a real sample from StatsBomb men's WC 2018+2022 instead of one game.
Offside = StatsBomb 'Offside' event OR a pass with outcome 'Pass Offside'.
Dominance = total shots differential (dominant team - opponent).
"""
import csv, json, sys, time, urllib.request
from pathlib import Path
from collections import defaultdict

BASE="https://raw.githubusercontent.com/statsbomb/open-data/master/data"
MAN=Path(__file__).resolve().parent.parent/"sports-predict-ee"/"raw_manifest.csv"
N=int(sys.argv[1]) if len(sys.argv)>1 else 80

def get(u):
    r=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(r,timeout=30) as x: return json.loads(x.read())

ing=set()
for row in csv.DictReader(open(MAN,encoding="utf-8")):
    if row["source_name"]=="statsbomb_open_data" and row["entity_name"]=="events":
        ing.add(row["source_url"].rstrip(".json").split("/")[-1])

wc=[]
for s in ("3","106"):
    try:
        for m in get(f"{BASE}/matches/43/{s}.json"):
            if str(m["match_id"]) in ing: wc.append(str(m["match_id"]))
    except Exception as e: print("matches err",e)
    time.sleep(0.4)
sample=wc[:N]
print(f"analyzing {len(sample)} men's WC matches\n")

rows=[]  # (shot_diff, dom_offsides, sub_offsides)
for mid in sample:
    try: ev=get(f"{BASE}/events/{mid}.json")
    except Exception: continue
    time.sleep(0.3)
    shots=defaultdict(int); offs=defaultdict(int); teams=set()
    for e in ev:
        t=e.get("type",{}).get("name"); tm=e.get("team",{}).get("name")
        if tm: teams.add(tm)
        if t=="Shot": shots[tm]+=1
        elif t=="Offside": offs[tm]+=1
        elif t=="Pass" and e.get("pass",{}).get("outcome",{}).get("name")=="Pass Offside": offs[tm]+=1
    if len(teams)!=2: continue
    a,b=list(teams)
    dom,sub=(a,b) if shots[a]>=shots[b] else (b,a)
    rows.append((shots[dom]-shots[sub], offs[dom], offs[sub]))

def bucket(lo,hi):
    sel=[r for r in rows if lo<=r[0]<hi]
    if not sel: return None
    n=len(sel); do=[r[1] for r in sel]
    p2=sum(1 for x in do if x>=2)/n
    return n, sum(do)/n, p2

print("DOMINANT team's offsides, by how lopsided the shot count was:")
print(f"{'shot diff bucket':18s} {'N':>4} {'mean off':>9} {'P(>=2)':>7}")
for lo,hi,lab in [(0,5,'0-4 (close)'),(5,10,'5-9 (clear)'),(10,99,'10+ (blowout)')]:
    r=bucket(lo,hi)
    if r: print(f"{lab:18s} {r[0]:>4} {r[1]:>9.2f} {r[2]*100:>6.0f}%")
# overall dominant
n=len(rows); do=[r[1] for r in rows]
print(f"\nAll dominant teams (N={n}): mean {sum(do)/n:.2f}, P(>=2)={sum(1 for x in do if x>=2)/n*100:.0f}%")
sub=[r[2] for r in rows]
print(f"All underdog teams (N={n}): mean {sum(sub)/n:.2f}, P(>=2)={sum(1 for x in sub if x>=2)/n*100:.0f}%")
