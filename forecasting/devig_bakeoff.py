"""
De-vig method bake-off log.

For every question answered off a real multi-way market with margin, we record
what EACH de-vig method (proportional / odds_ratio / shin / additive) would have
said for the YES side — alongside the eventual outcome. `odds_ratio` is the
current chosen default; this log is how we re-evaluate that choice empirically.

Once outcomes are filled, `--summary` Brier-scores each method head-to-head over
settled rows. The method with the lowest mean Brier is the candidate default;
don't switch on a handful of rows — wait for the sample to mean something.

Rows where every method agrees (near-vig-free markets, e.g. low-hold Kalshi
3-ways) are still logged: they cost nothing and confirm method-invariance.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

LOG = Path(__file__).resolve().parents[1] / "outputs" / "results" / "devig_bakeoff.csv"
METHODS = ["proportional", "odds_ratio", "shin", "additive"]
FIELDS = (["match_date", "match", "question", "market", "margin_pct"]
          + [f"yes_{m}" for m in METHODS]
          + ["chosen_method", "outcome", "status", "note"])


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
        print("no bake-off log yet"); return
    rows = [r for r in csv.DictReader(LOG.open(encoding="utf-8"))
            if r["status"] == "settled" and r["outcome"] in ("YES", "NO")]
    if not rows:
        print(f"{_count()} rows logged, none settled yet"); return
    print(f"De-vig bake-off — {len(rows)} settled rows")
    print(f"{'method':14} {'mean Brier':>12} {'vs chosen':>12}")
    briers = {}
    for m in METHODS:
        errs = []
        for r in rows:
            col = r.get(f"yes_{m}", "")
            if col in ("", None):
                continue
            o = 1.0 if r["outcome"] == "YES" else 0.0
            errs.append((float(col) / 100 - o) ** 2)
        briers[m] = sum(errs) / len(errs) if errs else None
    base = briers.get("odds_ratio")
    for m in METHODS:
        b = briers[m]
        if b is None:
            print(f"{m:14} {'—':>12}")
            continue
        delta = "" if base is None else f"{b - base:+.4f}"
        star = "  <- chosen" if m == "odds_ratio" else ""
        print(f"{m:14} {b:>12.4f} {delta:>12}{star}")
    best = min((m for m in METHODS if briers[m] is not None), key=lambda m: briers[m])
    print(f"\nlowest Brier so far: {best}"
          + ("" if best == "odds_ratio" else "  (candidate — needs more rows before switching)"))


def _count() -> int:
    return sum(1 for _ in csv.DictReader(LOG.open(encoding="utf-8")))


if __name__ == "__main__":
    if "--summary" in sys.argv:
        summary()
    else:
        print("usage: python -m forecasting.devig_bakeoff --summary")
