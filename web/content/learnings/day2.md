# Training Feedback — Day 2

Feedback from the Day-2 run, focused on what the **second data point** reveals that Day 1 could
not (trends, not snapshots). Builds on `day1.md` — its two issues (greedy-decoding artifact,
closed-book QA being unlearnable) remain **open**; this note adds trend-level findings.

**Curve so far:**

| Day | Pairs | SFT-eval ppl | Retention ppl | Forgetting | Judge /5 |
| --- | --- | --- | --- | --- | --- |
| 0 (base) | 0 | 24.44 | 11.35 | — | 1.00 |
| 1 | 1,000 | 8.60 | 12.05 | +6.1% | 1.32 |
| 2 | 2,000 | 8.00 | 12.42 | +9.5% | 1.50 |

---

## Finding 1 — Data volume is a weak, diminishing lever (quantified)

**Severity:** high · this is the headline result of Day 2.

**Diagnosis.** Doubling the data (1,000 → 2,000) moved the judge only **+0.18** (1.32 → 1.50) and
SFT-eval ppl only **−0.60** (8.60 → 8.00, already near-flat). Perplexity has essentially saturated;
the judge is rising but slowly and likely sub-linearly.

**Extrapolation.** At the observed slope (~+0.18 judge / +1,000 pairs, and almost certainly
decelerating), reaching a *usable* judge (~3/5) would need **~8+ more days** if linear — and it
won't be linear. This is strong evidence that the **task mix**, not data volume, is the binding
constraint — exactly the Day-1 hypothesis, now backed by a trend rather than a single point.

**Recommendation.** The evidence now **favors the v2 pivot** (grounded-heavy mix, per `day1.md`
Issue 2) over continuing to scale the current mix. Continuing Day 3+ is still worthwhile *only* as
a deliberate "is it just volume?" confirmation — not as the path to a good model.

---

## Finding 2 — Forgetting grows monotonically with data (new tradeoff)

**Severity:** medium · worsens as the study continues.

**Diagnosis.** Retention perplexity rises every round: 11.35 → 12.05 → 12.42 (**+6.1% → +9.5%**),
~+0.37 ppl per +1,000 cumulative pairs. Each round trains from base, yet more data ⇒ more drift
toward the chat distribution ⇒ more "data loss."

**Extrapolation.** At this slope, Day 5 (~5k pairs) ≈ 13.5 ppl (**~+19%**, "notable"); Day 8 (~8k) ≈
"severe". So scaling the current approach **trades growing forgetting for shrinking judge gains** —
the worst side of both curves.

**Recommendation.** If the study continues on the current mix, add a documented mitigation:
mix a small fraction of raw pretraining windows into SFT (**replay**), and/or lower the LR. If we
pivot to v2, re-baseline the forgetting curve from scratch. Either way, keep reporting retention
every run (already done).

---

## Finding 3 — Measurement blind spot: the judge tests mostly the *unlearnable*

**Severity:** high (measurement) · likely hiding real capability.

**Diagnosis.** The 50 judge questions are drawn from QA, most of which are **closed-book recall** —
the one thing a 125M model cannot learn from few exposures. So the 1.50 is dominated by the model's
worst task, while the **learnable** tasks (RAFT / summarize / extract / rewrite, where the source is
in the prompt) are under-measured. Day-2 samples support this: the grounded-flavored severability
answer improved to essentially correct, while the two pure-recall answers stayed degenerate.

**Recommendation.** Instrument the eval to report the judge score **per mode** — grounded
(context-in-prompt) vs closed-book (recall) — as separate numbers. This almost certainly shows the
model is *decent* at the learnable tasks and *bad* only at recall, which is a fairer and more useful
picture, and directly motivates the v2 mix. Cheap: reuse the existing judge with a mode tag.

---

## Carry-forward from Day 1 (still open)

- **Greedy-decoding artifact** (`day1.md` Issue 1): still unfixed; Day-2 samples still show greedy
  repetition ("…is not a standard of proof, but is a standard of proof…"). Adding
  `no_repeat_ngram_size=3` + `repetition_penalty≈1.3` remains a cheap, comparability-safe fix.
- **Closed-book QA unlearnable** (`day1.md` Issue 2): now corroborated by the trend — the core
  reason for the slow climb.
- **Decontamination cache**: verify `eval_ngrams.json` got cached this run (HF was flaky on Day 1);
  if still empty, retry before more days.

---

## Recommended action order

1. **Instrument per-mode judge** (Finding 3) + apply the **decoding fix** (`day1.md` #1) — both cheap,
   both improve the *measurement*. Re-score Days 0–2 to keep the curve comparable.
2. **Decide continue vs pivot:** the data now leans toward **v2 (grounded-heavy restart)**. Run Day 3
   only if you want an explicit volume-plateau confirmation on the current mix.
3. If continuing the current mix beyond ~Day 3, add **replay** to bound forgetting (Finding 2).

**Status:** OPEN — recommendation: instrument measurement, then pivot to v2 rather than scale further.
