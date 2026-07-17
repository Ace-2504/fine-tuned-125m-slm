# Training Feedback — Day 1

Issues recognized from the Day-1 SFT run, with diagnosis, evidence, recommended fix, and the
effect on the controlled scaling study. Source: `reports/run-01.md`, `research_log.md`.

**Day-1 recap:** SFT-eval ppl 24.44 → **8.60** · retention 11.35 → **12.05** (+6.1%, mild) ·
Gemini-judge **1.32/5** · generations degenerate (repetition / question-echo).

Interpretation: the model learned the *chat format/distribution* (ppl dropped sharply) but not good
*answer content* (judge stayed low). The two issues below explain most of that gap.

---

## Issue 1 — Greedy decoding artifact (measurement, cheap fix)

**Severity:** medium · likely *overstates* how weak the model is.

**Diagnosis.** Eval/sample generations use pure greedy decoding with no repetition control
(`sft_train_core._generate`: `do_sample=False`, no `repetition_penalty`, no `no_repeat_ngram_size`).
Greedy on a small, freshly-tuned model produces textbook repetition loops.

**Evidence.**
> "The standard of proof in a civil lawsuit is the standard of proof in a civil lawsuit."

This is a decoding pathology as much as a capability one.

**Fix.** Add `no_repeat_ngram_size=3` and `repetition_penalty≈1.3` to `_generate` (stays
deterministic → still comparable). Optionally mild sampling (temp 0.7, top_p 0.95) with a fixed seed.

**Comparability.** SAFE. Decoding does not change the trained weights. Re-run the eval/judge on the
saved day-0 and day-1 checkpoints with the new decoding and the curve stays valid. Do this FIRST as a
diagnostic — it separates "decoding artifact" from "real capability" before any bigger change.

---

## Issue 2 — Closed-book QA is largely unlearnable at this scale (design, real fix)

**Severity:** high · the main driver of the low judge score.

**Diagnosis.** 80% of QA is **closed-book**: the training example is `question → answer` with the
passage removed ("knowledge into weights"). This asks a 125M model to recall a long-tail document fact
(e.g. *"48% of the Carbon & Alloy Group's 1997 sales"*) from a **single** exposure — effectively
impossible. The model instead emits confident-but-wrong answers, which the judge correctly scores ~1.
Worse, the **judge set is drawn mostly from closed-book QA**, so we grade the model almost entirely on
the one thing it cannot learn. The RAFT/context tasks (passage IS in the prompt) are genuinely learnable
and are under-represented in scoring.

**Evidence.** Degenerate/echo answers concentrate on recall questions; ppl (distribution fit) improved
while judged correctness did not.

**Fix.** Rebalance toward **grounded** tasks:
- Increase RAFT/context share (answer present in the prompt → learnable).
- Restrict any closed-book QA to **general** knowledge (fineweb-edu), not obscure document specifics.
- Build the judge/eval set to include grounded questions, so scoring reflects what SFT can teach.

**Comparability.** BREAKS the current curve (changes an experimental variable). Cleanest path: treat as
**v2** and restart the curve (redo Day 1 with the new mix). Cheap now — only Day 1 exists (~$0.06) — and
better science: study a mix that *can* succeed. Requires new eval/judge sets (the frozen ones assume the
old mix).

---

## Issue 3 — Minor / rigor

- **Decontamination skipped** on Day 1 (HuggingFace datasets-server 503 for LexGLUE/CaseHOLD). Retry to
  cache `data/sft/eval_ngrams.json`, then rebuild, before investing in more days.
- **Judge model:** consider `gemini-3-flash-preview` (stronger, more discriminating) instead of
  `gemini-3.1-flash-lite` judging its own-family outputs. Log both if unsure.
- Baseline judge = 1.00 confirms the floor (base model can't follow instructions at all); the 1.32 delta
  is real but small.

---

## Recommended action order

1. **Diagnostic (now, ~2 min, comparability-safe):** re-decode the saved Day-1 checkpoint with
   repetition penalty + no-repeat-ngram; re-judge Day 0 and Day 1. See how much of the 1.32 is artifact.
2. **Decide the mix:** if grounded answers look decent → restart the curve with a grounded-heavy mix
   (the real fix, Issue 2). If even grounded is poor → capacity finding; more data is the only lever
   (continue the original curve).
3. Fold in Issue 3 (decontam cache, judge model) whichever path is chosen.

**Status:** OPEN — awaiting decision on step 1 before Day 2.
