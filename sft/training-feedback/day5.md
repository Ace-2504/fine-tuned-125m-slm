# Training Feedback — Day 5

**Round:** 5,000 pairs · ppl **7.37** · retention **12.90 (+13.6%)** · judge **1.52** · $0.102

First round of the chained 5→10 run. Note the context: the **stop rule had already fired at Day 4**
(judge flat 3 rounds). Days 5–10 were run by explicit decision to test the plateau at **10× scale** —
i.e. to convert "we scaled 4× and it stayed flat" into the stronger "we scaled 10× and it stayed flat."
So this round is a *confirmation* round, not an exploratory one.

---

## Finding 1 — Flat, as predicted

Judge **1.50 → 1.52 (+0.02)**. Within noise; nothing new. Cumulative movement since Day 2 (the last
real gain): **+0.02 over 3,000 additional pairs.**

## Finding 2 — Forgetting keeps climbing on schedule

Retention **12.74 → 12.90 (+12.2% → +13.6%)**. Still perfectly monotonic across all five rounds. The
cost side continues to be the only metric that responds to data.

## Finding 3 — The per-mode judge is inert on v1 (instrumentation gap)

The per-mode judge added during the v2 work reports `{'?': 1.52}` — **no mode breakdown**. Cause: v1's
eval/judge set was **frozen at Day 1**, before `build_dataset.py` learned to tag judge questions with
their mode. Freezing the eval set (correct for comparability) means v1 can never get a per-mode score
retroactively without breaking the curve.

**Implication:** the `day2.md` recommendation ("score grounded vs recall separately") is **structurally
unavailable on v1**. It will work on **v2**, whose eval set is built fresh with mode tags. Worth
recording as a lesson: **instrument the metric before freezing the eval set.**

## Sample probe

*"standard of proof"* → "…is the preponderance of the evidence standard." ✓ still correct (as since Day 3).

---

**Verdict:** no new information — exactly what a confirmation round should look like. Continue.
