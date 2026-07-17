# Training Feedback — Day 6

**Round:** 6,000 pairs · ppl **7.28** · retention **12.95 (+14.1%)** · judge **1.54** · $0.122

---

## Finding 1 — Still flat (6× the Day-1 data, +0.04 since Day 2)

Judge **1.52 → 1.54 (+0.02)**. Four consecutive rounds now sitting in the 1.46–1.54 band. Cumulative:
since Day 2's 1.50, **4,000 additional pairs have bought +0.04** — comfortably inside judge noise.

## Finding 2 — Forgetting: the slope is flattening slightly, but never reverses

Retention **12.90 → 12.95 (+13.6% → +14.1%)**. The per-round increment is shrinking (+0.70, +0.37,
+0.18, +0.14, +0.16, +0.05 across rounds 1–6) — forgetting is **decelerating but still strictly
monotonic**. It never once improved in any round.

**Reading:** the model appears to be converging toward a new (chat-shifted) equilibrium ~+15–16% worse
on the pretraining distribution, rather than degrading without bound. Bad, but bounded.

## Finding 3 — Perplexity keeps improving, uselessly

ppl **7.37 → 7.28**. Six consecutive rounds of monotonic improvement against a flat judge. Each round
adds another data point to the same conclusion: **ppl tracks distribution fit, not quality.**

## Sample probe

*"standard of proof"* → "…is the preponderance of the evidence standard." ✓ still correct.

---

**Verdict:** confirmation continues; nothing has changed. Halfway to the 10× target.
