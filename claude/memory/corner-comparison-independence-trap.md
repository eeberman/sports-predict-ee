---
name: corner-comparison-independence-trap
description: "no market prices the corner head-to-head, so it must be derived; anchor on the most relevant comparison market, NOT a blind shrink — the old +correlation 'shrink favorite' rationale was wrong"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 98c9b0c5-edfa-4705-9d91-a0ce02554442
---

On "Will team A finish with more corners than team B?" there is usually **no single market** pricing the head-to-head, so the answer must be derived by joining separate markets — and the join needs a dependence assumption you can't see. The failure mode is the *method*, not the data source (inputs can be 100% real corner ladders). See [[market-devig-methodology]] for direct-vs-derived.

**What holds up (the durable rule):**
1. First hunt a market that prices the comparison directly or semi-directly — a full-match "Most Corners" 3-way (A / Tie / B), or a per-half "Most Corners in Each Half" line. De-vig that; it's the best anchor and needs no copula assumption.
2. If only separate team total-corner ladders exist, the independent-Poisson P(A>B) is a **Low-confidence** number. Report it as-is. Do **not** bolt on a directional "shrink the favorite toward 50" — that lean is unproven (see below).

**Correction (2026-06-22, FRA vs IRQ).** The earlier version of this note told you to "shrink the favorite hard toward the crowd" and justified it with "corners are +correlated → independence overstates the favorite." **That mechanism is backwards.** Var(A−B) = VarA + VarB − 2·Cov; *positive* inter-team correlation *lowers* the variance of the difference, which pushes the **underdog down**, not up. For the underdog to beat independence you'd need *negative* correlation (a possession see-saw). The real sign is ambiguous and small — so there is no justified blind shrink in either direction.

**Evidence is thin (n=1).** ARG vs AUT (2026-06-22): per-team ladders only; independent-Poisson → AUT 20% to out-corner ARG, crowd 30%, AUT did it → −13.35 RBP (worst question on a +22 slate). That's one event at 20–30% — weak proof of a systematic bias, and not enough to support a standing lean. It does support rule #1: a real comparison market (crowd 30) beat the independent reconstruction (20).

**FRA vs IRQ (2026-06-22):** dropped the shrink. Q1 (Iraq more 1H corners) anchored on the *Most Corners in Each Half: France -290* market → Iraq ~10%, with independent-Poisson (~8%) as cross-check; our = crowd = 10. This and future corner-comparison rows are the clean test of whether any directional correction is ever warranted. See [[deviation-evidence-strength-rule]] and [[lean-rule-validation]].
