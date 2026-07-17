# Training Feedback — Day 7

**Round:** 7,000 pairs · ppl **7.20** · retention **13.00 (+14.6%)** · judge **1.60** · $0.139

> **The interesting round.** For the first time since Day 2, the judge moved meaningfully.

---

## Finding 1 — A real jump: judge 1.54 → 1.60 (+0.06)

**This is the largest single-round gain since Day 2** and the **highest score of the study so far**.
It is the first evidence in five rounds that could contradict the plateau conclusion.

**Two competing readings — and we must not pick prematurely:**

1. **Late climb (plateau is wrong).** Something genuinely started working at ~7k pairs; the curve
   isn't flat, it just has a long shoulder. If real, this would overturn the Day-4 verdict and argue
   for pushing *past* 10k.
2. **Noise (plateau holds).** The judge scores 50 questions on a 1–5 integer scale; a +0.06 mean shift
   is **3 questions moving up by one point**. That is well inside plausible round-to-round variance —
   especially given Day 3 already produced a −0.04 wobble in the other direction.

**Prior evidence favours (2):** the judge has wandered 1.46 → 1.50 → 1.52 → 1.54 → 1.60 with no
mechanism to explain a sudden gain — the mix, LR, epochs, and decoding are all **frozen**, and the only
changing variable (data) has been inert for five rounds.

**Do not update the conclusion on one round.** The falsifiable test is simple: **if this is a real
trend, Day 8 and Day 9 should hold at ≥1.60 or continue climbing. If it collapses back to ~1.54, it was
noise** — and we will have measured the judge's noise band, which is itself useful.

## Finding 2 — Nothing else moved

Retention **12.95 → 13.00 (+14.6%)** — monotonic as ever. ppl **7.28 → 7.20**. The probe answer is
unchanged ("…is the preponderance of the evidence" ✓). **No qualitative change accompanies the judge
bump**, which is itself weak evidence for the noise reading — a real capability gain would usually show
up somewhere in the samples.

---

**Verdict:** flagged, not concluded. The next two rounds decide whether Day 7 is signal or noise. This
is exactly why the 10× run was worth doing rather than stopping at Day 4 on a 4-round trend.
