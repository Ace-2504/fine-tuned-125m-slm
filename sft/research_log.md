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

## Scaling curve (so far)

| Day | Train pairs | SFT-eval ppl | Retention ppl (Δ vs base) | Judge /5 |
| --- | --- | --- | --- | --- |
| 0 (base) | 0 | 24.44 | 11.35 (—) | 1.00 |
| 1 | 1,000 | 8.60 | 12.05 (+6.1%) | 1.32 |
| 2 | 2,000 | 8.00 | 12.42 (+9.5%) | 1.50 |

**Read so far:** the judge score **is** climbing with data (1.00 → 1.32 → 1.50), but slowly, while
forgetting creeps up (+6.1% → +9.5%). Trend is consistent with the Day-1 feedback: the closed-book
QA share caps quality. **Next:** Day 3 (+1,000 → 3,000), or act on `training-feedback/day1.md`
(grounded-heavy v2 + decoding fix) if the slow climb persists.
