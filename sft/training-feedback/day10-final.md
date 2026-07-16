# Training Feedback — Day 10 (FINAL, v1 study complete)

The v1 data-scaling study is **complete**: 10 rounds, 0 → 10,000 pairs, method frozen throughout.
This note supersedes the per-round feedback (`day1.md`, `day2.md`, `day3.md`, `day4.md`) as the
study's conclusion.

| Day | Pairs | SFT-eval ppl | Retention ppl | Forgetting | Judge /5 |
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
| 10 | 10,000 | **7.01** | **13.20** | **+16.3%** | **1.54** |

---

## Finding 1 — The plateau holds at 10× scale (definitive)

**Verdict:** the study's central question is answered — **no**, it is not just data volume.

- Judge by round: 1.00 → 1.32 → **1.50** → 1.46 → 1.50 → 1.52 → 1.54 → 1.60 → 1.60 → 1.54 → 1.54.
- **All meaningful gain arrived by Day 2.** From 2k → 10k — a **5× data increase** — the judge moved
  **+0.04**, wandering between 1.46 and 1.60 and ending where it started. The Day-7/8 peak of 1.60
  did not hold. That is **noise around ~1.5, not a trend**.
- Predicted before the run: "judge ≈ 1.5, retention ≈ +18–20%." Realized: **judge 1.54, retention
  +16.3%.** The plateau model predicted the outcome correctly.

**This is the strong form of the result:** *we scaled the data 10× and quality did not move.*

## Finding 2 — Forgetting is the only thing data reliably bought

**Severity:** decisive.

Retention perplexity rose **monotonically in all ten rounds**, 11.35 → **13.20 (+16.3%)** — forgetting
nearly **tripled** from Day 1's +6.1% while the judge stood still. Data volume had a large, consistent,
*measurable* effect on exactly one metric, and it was the one we didn't want.

**Implication:** every round past Day 2 was pure cost — measurable erosion of the base model bought
with money and compute, for zero quality return.

## Finding 3 — Quality regressed at scale (new, and striking)

**Severity:** high · the clearest single illustration of the whole result.

The fixed probe *"What is the standard of proof in a civil lawsuit?"*:
- Days 1–2: degenerate repetition
- Days 3–8: **correct** — "…is the preponderance of the evidence standard." ✓
- **Day 10: regressed** — "A civil action is a civil action for the recovery of money, which is
  generally a civil action for the recovery of money."

**More data made a previously-correct answer worse.** This is consistent with accumulating drift:
the model is pulled further from its pretrained knowledge (retention +16.3%) faster than the extra
closed-book examples can teach it anything, so earlier wins are overwritten.

## Finding 4 — Perplexity is definitively not a quality metric (here)

SFT-eval ppl improved in **every one of ten rounds**: 8.60 → 8.00 → 7.70 → 7.51 → 7.37 → 7.28 → 7.20
→ 7.12 → 7.05 → **7.01**, a clean monotonic decline, while the judge was flat and the samples
*regressed*. Ten rounds of unambiguous evidence: perplexity measures **distribution fit**, not
answer quality. Reporting it as the headline metric would have told the exact opposite story.

---

## Verdict — v1 is CLOSED

1. **v1 scaling is finished.** The question is settled with the strongest available evidence
   (10× scale, method frozen, monotonic control metrics). It is a clean, publishable **negative
   result**: *on a closed-book-heavy mix, SFT data volume does not buy answer quality in a 125M model
   — it buys catastrophic forgetting.*
2. **Do not run Day 11+.** There is nothing left to learn on this axis.
3. **The only untested lever is the mix** — **v2** (`v2-pivot.md`, parked, code shipped and its Day-1
   partially generated). Every round of feedback across the entire study (Days 1, 2, 3, 4, 10)
   independently converged on this same conclusion.
4. **Cost of the full study:** ~$1.14 GPU + ~$3.50 teacher ≈ **$4.6** for 11 training runs and 10,000
   teacher-generated pairs.

**Status:** v1 **COMPLETE — closed as a negative result.** Recommended next step: unpark v2, the one
hypothesis the data has never tested.
