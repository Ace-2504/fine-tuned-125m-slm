# Training Feedback — Day 4

Day 4 is the **confirmation round**. Days 1–3 suggested a plateau; Day 4 settles it. Builds on
`day1.md`, `day2.md`; see `v2-pivot.md` for the parked alternative.

**Curve (v1, original closed-book-heavy mix):**

| Day | Pairs | SFT-eval ppl | Retention ppl | Forgetting | Judge /5 |
| --- | --- | --- | --- | --- | --- |
| 0 (base) | 0 | 24.44 | 11.35 | — | 1.00 |
| 1 | 1,000 | 8.60 | 12.05 | +6.1% | 1.32 |
| 2 | 2,000 | 8.00 | 12.42 | +9.5% | 1.50 |
| 3 | 3,000 | 7.70 | 12.60 | +11.0% | 1.46 |
| 4 | 4,000 | 7.51 | 12.74 | **+12.2%** | **1.50** |

---

## Finding 1 — Plateau CONFIRMED; the stop rule has fired

**Severity:** decisive · this ends the v1 scaling question.

**Diagnosis.** The judge is flat across **three consecutive rounds**: 1.50 → 1.46 → 1.50 (Days 2–4),
spanning 2,000 → 4,000 pairs. Judge deltas by round: **+0.32, +0.18, −0.04, +0.04**. All the gain
arrived by Day 2; **4× the Day-1 data bought +0.18 total, and nothing at all after Day 2.**

**Recommendation.** **Stop scaling v1.** The pre-agreed stop rule (judge flat ±0.05 for two
consecutive rounds) is satisfied twice over. Further rounds on this mix are not an open question —
they are a known negative result.

---

## Finding 2 — Forgetting has doubled, and keeps climbing

**Severity:** high · the cost side of the trade is compounding.

**Diagnosis.** Retention perplexity rises every single round, monotonically:
11.35 → 12.05 → 12.42 → 12.60 → **12.74** (+6.1% → +9.5% → +11.0% → **+12.2%**). Forgetting has
**doubled since Day 1** while the judge gained nothing since Day 2. Each additional round now buys
**pure downside**: measurable erosion of the base model for zero quality gain.

**Extrapolation to 10k** (the open proposal): judge ≈ still ~1.5; retention ≈ **+18–20%** (severe
territory); cost ≈ $5 + several hours. **Strictly worse model, for money and time.**

**Recommendation.** If any further v1 rounds happen, **replay is now mandatory** (mix raw pretraining
windows into SFT) — but note replay bounds the damage, it does not create quality upside.

---

## Finding 3 — Perplexity/judge divergence is now unambiguous

**Severity:** medium (measurement discipline).

**Diagnosis.** SFT-eval perplexity improved every round — 8.60 → 8.00 → 7.70 → **7.51** — while the
judge sat flat at ~1.5. Four rounds of clean evidence that **perplexity measures distribution fit, not
answer quality**, and is actively misleading as a success metric here.

**Recommendation.** Never report SFT-eval ppl as the headline. The judge (and, per `day2.md`, a
**per-mode** judge) is the metric that matters. Retain ppl only as a sanity/diagnostic signal.

**Sample evidence (Day 4).** Mixed and not improving:
- *standard of proof* → "…is the preponderance of the evidence standard." ✓ (correct since Day 3, no further gain)
- *10-K summary* → "Summarize the report to include a 10-K annual report." (still echoes the prompt)
- *severable* → "must be severable, and the remainder of the contract must be severable." (circular — **worse** than Day 2)

---

## Carry-forward (unchanged, still open)

- **Decoding fix** (`day1.md` #1) — still unapplied on v1 (deliberately, to preserve v1's internal
  comparability). Greedy repetition still visible in Day-4 samples.
- **Closed-book unlearnability** (`day1.md` #2) — now confirmed by four rounds of flat judge.
- **Per-mode judge** (`day2.md` #3) — still the highest-value measurement change; v1's judge remains
  dominated by unlearnable recall.

---

## Verdict and recommended action

1. **Stop v1 scaling.** Days 1–4 answer the study's question conclusively: *on this mix, data volume
   does not buy answer quality — it buys forgetting.* This is a clean, publishable negative result.
2. **Do not proceed to 10k on v1.** Our own curve predicts judge ~1.5 and retention ~+18–20%. The only
   reason to run it would be to state "we scaled 10× and it stayed flat" — a rhetorical strengthening
   of an already-decisive result, at ~$5 and several hours.
3. **The only real lever left is the mix** — i.e. **v2** (`v2-pivot.md`, parked). Every round of
   feedback (Days 1, 2, 4) has now independently pointed to the same conclusion. The v1 improvement
   loop has exhausted its secondary levers (decoding and replay bound damage; neither creates quality).

**Status:** v1 scaling — **RECOMMEND STOP** (question answered). Awaiting decision: stop here, push to
10k for the rhetorical point, or unpark v2.
