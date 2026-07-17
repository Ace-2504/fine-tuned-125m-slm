# Training Feedback — Day 3

> **Note:** backfilled — this round's feedback was skipped at the time and written after Day 4.
> The analysis below is from the **Day-3 data point** (i.e. what Day 3 revealed on its own,
> before Day 4 confirmed it). Kept for a complete per-round record.

**Curve at Day 3:**

| Day | Pairs | SFT-eval ppl | Retention ppl | Forgetting | Judge /5 |
| --- | --- | --- | --- | --- | --- |
| 1 | 1,000 | 8.60 | 12.05 | +6.1% | 1.32 |
| 2 | 2,000 | 8.00 | 12.42 | +9.5% | 1.50 |
| 3 | 3,000 | 7.70 | 12.60 | **+11.0%** | **1.46** |

---

## Finding 1 — First plateau signal (the judge stopped climbing)

**Severity:** high · this is the round where the trend broke.

**Diagnosis.** The judge went **1.50 → 1.46** — the **first non-positive delta** of the study.
Deltas so far: +0.32, +0.18, **−0.04**. Adding a third 1,000 pairs bought *nothing*; within judge
noise it is flat, and the direction is down rather than up.

**Implication.** Day 2 read the trend as "climbing, but slowly." Day 3 says it isn't climbing at
all any more. The Day-2 extrapolation (~+0.18 judge per +1,000 pairs → usable at ~8 more days) was
**too optimistic** — the curve did not decay gracefully, it **flattened outright**.

**Recommendation (as of Day 3).** One more round to distinguish "noise dip" from "true plateau."
Two flat rounds in a row would satisfy the stop rule. *(Day 4 subsequently returned 1.50 —
confirming the plateau.)*

---

## Finding 2 — Forgetting crossed "notable" earlier than projected

**Severity:** medium-high.

**Diagnosis.** Retention hit **12.60 (+11.0%)**, crossing the 10% "notable" line. Day 2 projected
this would happen around **Day 5**; it arrived at **Day 3**. Forgetting is therefore growing
*faster* than the linear model suggested, while the judge grows slower.

**Implication.** The cost/benefit of each additional round is worse than Day 2 estimated — on both
axes simultaneously.

**Recommendation.** Treat retention as a first-class stopping criterion, not just a logged metric.

---

## Finding 3 — Nuance: common facts DO get learned (refines the Day-1 claim)

**Severity:** low (but scientifically important).

**Diagnosis.** The fixed sample *"What is the standard of proof in a civil lawsuit?"* became
**correct** for the first time — "…is the preponderance of the evidence standard." Days 1–2 produced
circular repetition on this same prompt.

**Implication.** Day-1's "closed-book QA is unlearnable" needs refining: **high-frequency, general
facts are learnable** with enough exposures (the preponderance standard recurs across the legal
corpus). What stays unlearnable is the **long-tail, document-specific** fact (a single company's 1997
sales percentage), seen once. So the aggregate judge can plateau *even while individual common facts
improve* — because the eval is dominated by long-tail recall.

**Recommendation.** This strengthens (not weakens) the v2 case: restrict closed-book QA to
**general knowledge** and put document-specific questions in **grounded** form. It also reinforces
`day2.md` Finding 3 — score the judge **per mode**, since aggregate scores hide this effect.

---

## Verdict (as of Day 3)

- The judge has **stopped improving**; forgetting is **accelerating past projection**.
- Not yet conclusive on its own (one flat round could be noise) → **run one confirmation round**.
- If Day 4 is also flat → stop v1 scaling and pivot to the mix (v2).

**Status:** superseded by `day4.md` — Day 4 returned 1.50, confirming the plateau and firing the
stop rule.
