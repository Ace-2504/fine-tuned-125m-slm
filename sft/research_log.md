# SLM-125M SFT — Research Log

Per-day record of the cumulative data-scaling study (Plan A). Generation stats live here;
per-training-run reports live in `reports/`. Costs are $0 while the teacher stays on free tier.

---

## Teacher availability finding (2026-07-13)

- Planned teacher `gemini-2.5-flash` (and the whole 2.5 family, incl. `gemini-2.5-flash-lite`)
  returns **404 "no longer available to new users"** on this free-tier key.
- Stable full-flash aliases `gemini-flash-latest`, `gemini-3.5-flash` → **persistent 503**.
- `gemini-2.0-flash` → 429 quota. `gemini-flash-latest` unusable.
- **Reliable on this key:** `gemini-3-flash-preview` (full flash, 4/4) and **`gemini-3.1-flash-lite`**.
- **Chosen teacher: `gemini-3.1-flash-lite`** — released (stable for a controlled study),
  ample for grounded QA, and best RPD headroom for hitting ~345 requests/day.

---

## Day 1 — 2026-07-13

**Generation** (`gen_qa.py --day 1`)

| Metric | Value |
| --- | --- |
| Teacher | `gemini-3.1-flash-lite` |
| Requests | 345 (planned 345) · 1 retry · **no RPD wall** → free-tier RPD ≥ 345 |
| Teacher tokens | 468,035 in / 158,404 out (626,439 total) |
| Wall clock | 3,169.6 s (~53 min) — dominated by the ~6.5 s/request RPM pacing |
| Cost | **$0** (free tier) |
| Raw pairs | 1,721 — qa 920 · summarize 335 · extract 246 · rewrite 170 · refusal 50 |

**Filtering / build** (`build_dataset.py`)

| Stage | Pairs |
| --- | --- |
| raw | 1,721 |
| format ok | 1,715 |
| grounding gate | 1,687 |
| exact-hash dedup | 1,687 |
| embedding dedup (MiniLM cos>0.90) | 1,684 |
| decontaminate | 1,684 (LexGLUE/CaseHOLD fetch 503 — **skipped**; corpus was pre-decontaminated in pretraining) |
| eval quarantine (100 chunks) | train pool 1,382 |
| balance → task mix | 1,000 |
| context-fit (≤1024 tok) | 1,000 |

**Day-1 dataset (frozen eval + cumulative train)**

- **Eval (fixed, built once):** 100 pairs — qa 55 · summarize 20 · extract 15 · rewrite 10; 50 judge questions. Chunk-quarantined, zero train leakage.
- **Train `pairs.jsonl`:** **1,000 pairs**
  - task: qa 550 · summarize 200 · extract 150 · rewrite 100
  - mode: closed_book 417 · raft 133 · context 450
  - domain: sec 420 · case-law 352 · fineweb-edu 228

**Notes / issues**
- Decontamination against LexGLUE/CaseHOLD skipped this run (HF datasets-server 503). Low risk:
  the source corpus was already decontaminated during pretraining. Retry on a later day to
  cache `data/sft/eval_ngrams.json`, then rebuild.
- `gemini-3.1-flash-lite` sustained the full day with 1 retry and no daily wall.

**Training** (`modal_sft.py`, Modal **L4**) — full report in `reports/run-01.md`

| Metric | Baseline (day 0) | Day 1 (1,000 pairs) | Δ |
| --- | --- | --- | --- |
| SFT-eval perplexity | 24.44 | **8.60** | −15.84 (2.8× better) |
| Retention perplexity (pretrain val) | 11.35 | **12.05** | +0.69 (**+6.1%**, mild) |
| Gemini-judge (1–5) | 1.00 | **1.32** | +0.32 |
| Train steps / wall | 0 | 189 (3 ep) / **79 s** | — |
| Peak GPU mem | — | 11.5 GB | — |
| Cost | $0.028 | $0.029 | ~$0.06 total |

**Data loss / forgetting:** retention ppl rose 11.35 → 12.05 (**+6.1%, mild**) — the small
chat-distribution shift we predicted, **not** catastrophic. Base retention validated exactly
(day-0 = 11.3546 vs known 11.35).

**Honest finding — the important one:** perplexity improved sharply (task distribution learned),
but the **Gemini-judge score is only 1.32/5** and sample generations are degenerate (repetition /
question-echo, e.g. *"The standard of proof in a civil lawsuit is the standard of proof in a
civil lawsuit."*). At 1,000 pairs the 125M model learns the **chat format** but not yet good
**answer content** — classic undertraining. This is exactly the signal the scaling study exists
to measure.

## Day 2 — 2026-07-15

**Generation:** hit the shared free-tier **RPD wall** partway (Day-1 + reports had drained the
day's ~500 quota) — 680 raw QA pairs, saved cleanly. Added an **intra-day top-up resume** to
`gen_qa.py` (commit `1c8af61`); after the quota reset, a resume issued only the remaining ~209
requests → Day-2 raw complete (~1,717 pairs, full task coverage). Cost $0.

**Build:** cumulative raw 3,438 → **2,000** train pairs (qa 1100 / summarize 400 / extract 300 /
rewrite 200; sec 834 / case 717 / edu 449; day1 913 + day2 1087). Eval set stayed frozen.

**Training** (Modal L4, `reports/run-02.md`): 375 steps (3 ep), 164 s, $0.049.

**Result:** SFT-eval ppl 8.60 → **8.00**; retention 12.05 → **12.42** (+9.5% vs base, still mild);
**Gemini-judge 1.32 → 1.50**. Samples marginally better — the severability answer flipped from
wrong ("not severable") to essentially correct — but recall questions still degenerate (the
closed-book limitation flagged in `training-feedback/day1.md`).

## Day 3 — 2026-07-15

**Generation:** completed in one shot (no RPD wall) — 1,725 raw pairs, 345 requests. Free-tier RPD is
higher than the earlier ~500 estimate. **Build:** cumulative raw 5,163 → **3,000** train pairs
(qa 1650 / summarize 600 / extract 450 / rewrite 300; day1 859 + day2 1070 + day3 1071). Eval frozen.

**Training** (Modal L4, `reports/run-03.md`): 564 steps (3 ep), 241 s, $0.064.

**Result — the plateau:** SFT-eval ppl 8.00 → **7.70** (still slowly dropping); retention 12.42 →
**12.60** (**+11.0%** vs base — now "notable", crossed 10%); **Gemini-judge 1.50 → 1.46** (flat/dip,
within noise). Doubling→tripling data did NOT raise the judge. Samples mixed: standard-of-proof became
**correct** ("preponderance of the evidence"), but the 10-K summary still echoes and severability got
muddier.

## Day 4 — 2026-07-15 (billing enabled)

**Billing on** → no RPD wall; request pacing 6.5 s → 0.5 s, so a 1,000-pair day generates in **~15 min**
(was ~53). Generation: 1,721 raw pairs, 345 requests, 0 retries, $≈0.50.

**Build:** cumulative raw 6,884 → **4,000** train pairs (qa 2200 / sum 800 / ext 600 / rew 400;
day1 870 + day2 1038 + day3 1056 + day4 1036). **Training** (L4): 750 steps, 331 s, $0.085.

**Result — plateau CONFIRMED:** SFT-eval ppl 7.70 → **7.51**; retention 12.60 → **12.74** (**+12.2%**);
judge 1.46 → **1.50**. The judge is **flat across three consecutive rounds** (1.50 / 1.46 / 1.50) while
forgetting has **doubled** since Day 1. Stop rule (flat ±0.05 × 2 rounds) fired. See
`training-feedback/day4.md`.

## Days 5–10 — 2026-07-16/17 (chained, method frozen)

Run automatically via `chain_days.sh 5 10` (generate → build → upload → train → report per day),
method **frozen** so only dataset size varies. All six rounds completed cleanly; a report exists for
every day (`reports/run-05…10.md`). Final dataset: **9,999 pairs**, balanced (qa 5500 / sum 2000 /
ext 1499 / rew 1000), ~1,000 per day across all 10 days.

## Scaling curve — FINAL (v1, 10 rounds, 0 → 10,000 pairs)

| Day | Train pairs | SFT-eval ppl | Retention ppl (Δ vs base) | Judge /5 |
| --- | --- | --- | --- | --- |
| 0 (base) | 0 | 24.44 | 11.35 (—) | 1.00 |
| 1 | 1,000 | 8.60 | 12.05 (+6.1%) | 1.32 |
| 2 | 2,000 | 8.00 | 12.42 (+9.5%) | **1.50** |
| 3 | 3,000 | 7.70 | 12.60 (+11.0%) | 1.46 |
| 4 | 4,000 | 7.51 | 12.74 (+12.2%) | 1.50 |
| 5 | 5,000 | 7.37 | 12.90 (+13.6%) | 1.52 |
| 6 | 6,000 | 7.28 | 12.95 (+14.1%) | 1.54 |
| 7 | 7,000 | 7.20 | 13.00 (+14.6%) | 1.60 |
| 8 | 8,000 | 7.12 | 13.10 (+15.4%) | 1.60 |
| 9 | 9,000 | 7.05 | 13.18 (+16.2%) | 1.54 |
| 10 | **10,000** | **7.01** | **13.20 (+16.3%)** | **1.54** |

**FINAL CONCLUSION — v1 (definitive):**

- **Judge:** 1.32 (1k) → 1.54 (10k). **Essentially all gain arrived by Day 2** (1.50). From 2k → 10k
  — a **5× increase in data** — the judge moved **+0.04**, wandering 1.46–1.60 (peak 1.60 at Days 7–8,
  back to 1.54). That is **noise around ~1.5, not a trend**.
- **Retention:** rose **monotonically every single round**, 11.35 → **13.20 (+16.3%)** — forgetting
  nearly **tripled** while quality stood still. This is the only variable that responded to data.
- **SFT-eval ppl:** fell monotonically 8.60 → **7.01**, proving conclusively that **perplexity does not
  measure answer quality** here.
- **Regression at scale:** the fixed sample *"standard of proof"* was **correct at Days 3–8**
  ("preponderance of the evidence") and **regressed to degenerate circularity at Day 10** — more data
  made a previously-correct answer worse, consistent with accumulating drift/forgetting.
- **Cost:** ~$1.14 GPU + ~$3.50 teacher ≈ **$4.6** for 10 rounds.

**The question is answered: scaling data 10× on the closed-book-heavy mix does not buy answer
quality — it buys forgetting.** A clean negative result. The remaining lever is the **mix** (v2).

---

# v2 — Grounded-heavy pivot

**Decision (2026-07-15):** switch to v2 (see `training-feedback/v2-pivot.md`). v1 is paused at Day 3
(plateau); its Day-4 option is preserved. v2 runs on a **separate track** (`SFT_TRACK=v2` →
`data/sft-v2/`, `reports-v2/`, Modal app `slm-125m-sft-v2`, volume `/sft-v2/`, ckpts
`/checkpoints/sft-v2/`) so nothing v1 is touched. Changes: mode {closed_book .15, raft .85}, task
{qa .40, sum .25, ext .20, rew .15}, closed-book only from fineweb-edu, decoding
`no_repeat_ngram_size=3`+`repetition_penalty=1.3`, per-mode judge (grounded vs recall).
