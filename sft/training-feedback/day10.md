# Training Feedback — Day 10 (FINAL ROUND · v1 study complete)

**Round:** 10,000 pairs · ppl **7.01** · retention **13.20 (+16.3%)** · judge **1.54** · $0.190

The 10× target is reached and the v1 data-scaling study is **complete**: 10 rounds, 0 → 10,000 pairs,
method frozen throughout. This file closes the study; per-round notes are in `day1.md`–`day9.md`.

| Round | Pairs | SFT-eval ppl | Retention ppl | Forgetting | Judge /5 |
| --- | --- | --- | --- | --- | --- |
| 0 (base) | 0 | 24.44 | 11.35 | — | 1.00 |
| 1 | 1,000 | 8.60 | 12.05 | +6.1% | 1.32 |
| 2 | 2,000 | 8.00 | 12.42 | +9.5% | **1.50** |
| 3 | 3,000 | 7.70 | 12.60 | +11.0% | 1.46 |
| 4 | 4,000 | 7.51 | 12.74 | +12.2% | 1.50 |
| 5 | 5,000 | 7.37 | 12.90 | +13.6% | 1.52 |
| 6 | 6,000 | 7.28 | 12.95 | +14.1% | 1.54 |
| 7 | 7,000 | 7.20 | 13.00 | +14.6% | 1.60 |
| 8 | 8,000 | 7.12 | 13.10 | +15.4% | 1.60 |
| 9 | 9,000 | 7.05 | 13.18 | +16.2% | 1.54 |
| **10** | **10,000** | **7.01** | **13.20** | **+16.3%** | **1.54** |

---

## Finding 1 — The plateau holds at 10× (definitive)

Judge **1.54**, identical to Day 9 and statistically identical to Day 2's **1.50**. From 2k → 10k — a
**5× data increase** — the judge moved **+0.04**, comfortably inside the **±0.07 noise band measured in
`day9.md`**. The Days 7–8 excursion to 1.60 was tested and rejected.

**Pre-registered prediction:** judge ≈ 1.5, retention ≈ +18–20%. **Realized:** judge **1.54**, retention
**+16.3%**. The plateau model predicted the outcome before the run.

**This is the strong form of the result:** *we scaled the data 10× and quality did not move.*

## Finding 2 — Forgetting: ten rounds, ten increases

Retention rose **monotonically in every single round**, 11.35 → **13.20 (+16.3%)** — nearly **tripling**
from Day 1's +6.1% while the judge stood still. Data volume had a large, consistent, measurable effect
on exactly one metric, and it was the one we didn't want. **Every round past Day 2 was pure cost.**

## Finding 3 — Quality REGRESSED at the final round (the sharpest result)

The fixed probe *"What is the standard of proof in a civil lawsuit?"*, tracked across all ten rounds:

| Rounds | Answer | |
| --- | --- | --- |
| 1–2 | circular repetition | ✗ |
| **3–9** | "…is the preponderance of the evidence (standard)." | **✓ correct** |
| **10** | "A civil action is a civil action for the recovery of money, which is generally a civil action for the recovery of money." | **✗ regressed** |

**More data made a previously-correct answer wrong.** It was right for *seven consecutive rounds* and
broke at 10k. Consistent with accumulating drift: the model is pulled away from its pretrained knowledge
(+16.3%) faster than extra closed-book examples can teach it anything, so earlier wins get overwritten.

## Finding 4 — Perplexity is definitively not a quality metric (here)

ppl improved in **all ten rounds**: 8.60 → 8.00 → 7.70 → 7.51 → 7.37 → 7.28 → 7.20 → 7.12 → 7.05 →
**7.01** — a clean monotonic decline, against a flat judge and a *regressing* sample. Reporting ppl as
the headline would have told the **exact opposite** story.

---

## Verdict — v1 CLOSED

1. **The question is answered with the strongest available evidence** (10× scale, method frozen,
   monotonic controls, competing hypothesis tested and rejected at Days 7–9). Clean **negative result**:
   *on a closed-book-heavy mix, SFT data volume does not buy answer quality in a 125M model — it buys
   catastrophic forgetting.*
2. **Do not run Round 11+.** Nothing remains to learn on the data-volume axis.
3. **The one untested lever is the mix** — **v2** (`v2-pivot.md`: open-book/grounded, shipped, parked,
   Day-1 partially generated). Every round of feedback (Days 1, 2, 3, 4, 7–9, 10) converged here.
4. **Lesson recorded (`day5.md`):** instrument metrics *before* freezing the eval set — v1 can never get
   a per-mode judge score retroactively without breaking its own comparability. v2 will have it.
5. **Cost:** ~$1.14 GPU + ~$3.50 teacher ≈ **$4.60** for 11 training runs and 10,000 pairs.

**Status:** v1 **COMPLETE — closed as a negative result.** Recommended next step: unpark v2, the one
hypothesis the data has never tested.
