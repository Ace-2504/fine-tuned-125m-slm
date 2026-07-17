# Fine-Tuning Plan — SLM-125M Supervised Fine-Tuning (Phase 2: Plan)

> **STATUS: EXECUTED & SUPERSEDED (2026-07-17).** This is the original Phase-2 planning document,
> kept as a historical record of what was planned *before* the study ran. Two things diverged in
> execution:
> 1. **Scale:** planned as an open-ended ~1,000-pairs/day curve; actually ran **10 rounds to 10,000
>    pairs** and closed as a negative result (judge flat ~1.5/5, forgetting +6.1% → +16.3%).
> 2. **Quota:** planned entirely around the free tier (500 RPD, ~$0). Billing was enabled at Day 4,
>    removing the RPD wall and cutting generation from ~53 min to ~15 min/round. Actual study cost
>    ≈ **$4.60** (~$1.14 GPU + ~$3.50 teacher), not $1–3.
>
> For what actually happened, read `sft/research_log.md` and `sft/training-feedback/day1…day10.md`.
> Published write-up: https://ace-2504.github.io/fine-tuned-125m-slm/

**Project:** turn `Ace-2504/slm-125m-base` (a 125.8M-param, 1024-ctx, legal/financial
Llama-style base model) into an **instruction-following domain assistant** via
supervised fine-tuning, using a **Gemini 3.1 Flash-Lite** teacher (the planned Gemini 2.5
Flash is unavailable on the free-tier key — see §3) to synthesize a high-quality,
high-diversity, deduplicated QnA dataset from the **same corpus the base was pretrained
on** — run as a **data-scaling study** (Plan A).

Treated as a **research project**: every measurable detail of generation, training,
and the Modal runtime is logged for a later observations write-up (style ref:
https://ace-2504.github.io/slm-125m-observations/ — produced LATER, not now).

Founding brief: [`fine-training-prompt.md`](fine-training-prompt.md) ·
Q&A decisions: [`agent-questions-during-fine-tuning.md`](agent-questions-during-fine-tuning.md)

---

## 0. Locked decisions

| # | Decision |
|---|---|
| **Research design** | **Plan A — cumulative data-scaling study**: each day +1,000 fresh pairs; re-fine-tune **from base** on the *cumulative* set; evaluate on a **fixed held-out eval set**; plot quality vs #pairs |
| Daily generation | **1,000 new pairs/day** (~360 requests) — fits the **500 RPD** free tier with margin |
| Epochs | **3, fixed across all rounds** (1-epoch constraint relaxed for the study; epochs held constant so dataset size is the only variable) |
| Batch size | **16** (fixed) |
| Fine-tune type | **Full fine-tune** — NOT LoRA, NOT QLoRA (see §5) |
| GPU | **Single L4 24 GB** (best value; job is overhead-bound). A100/H100 available but worse value here |
| Init each round | Fresh from HF base `Ace-2504/slm-125m-base` (clean, controlled) |
| Behavior | 80% **closed-book** (Q→A) + 20% **RAFT** (answer-from-context / "not stated") |
| Persona | **Legal + financial domain assistant** |
| Task mix | QA 55% · Summarize 20% · Extract-to-JSON 15% · Rewrite 10% |
| Domain mix | Mirror pretraining: **SEC 42% · case-law 35% · fineweb-edu 23%** |
| Turns | **Single-turn** |
| System prompt | Small set of **varied** domain system prompts |
| Teacher | **`gemini-3.1-flash-lite`**, free tier (2.5 Flash blocked for new users — see §3); teacher-agnostic generator, `gemini-3-flash-preview` higher-quality alt, Groq/Llama-3.3-70B fallback |
| Thinking | Off for bulk QA, on only for the Evol-Instruct slice |
| Gen granularity | ~500-token chunks, ~5 QA each |
| Dedup | **Global across all days** — local `all-MiniLM-L6-v2` cosine > 0.9 + exact-hash + MinHash |
| Grounding | String-overlap + NLI gate (local), batched Flash self-check on borderline |
| Eval | **Fixed** held-out set (built day 1, never trained on) + val loss + **Gemini-as-judge** (1–5 rubric); decontaminate vs LexGLUE / CaseHOLD |
| **Retention / "data loss"** | After **every** run, measure perplexity on the **original pretraining val set** (`data/tokens/val`) → catastrophic-forgetting check vs base (base PPL **11.35**) and vs previous run's checkpoint |
| **Per-run report** | After **every** training run, emit a **detailed report** (all params + data-loss/forgetting + perplexity comparison vs previous checkpoint, or vs base for run 1) — see §9b |
| Output | HF repo **`Ace-2504/fine-tuned-125m-slm`** + chat template + demo update |
| Logging | Capture **everything**, per day (see §9) |

---

## 1. Research design — Plan A (cumulative data-scaling study)

The core experiment: **how much SFT data does a 125M base model need before instruction-
following quality saturates?** Answered with a controlled scaling curve.

| Day | New pairs | Train set (cumulative) | Fine-tune from | Eval on |
|---|---|---|---|---|
| 1 | +1,000 | 1,000 | base (fresh) | fixed eval set |
| 2 | +1,000 | 2,000 | base (fresh) | fixed eval set |
| 3 | +1,000 | 3,000 | base (fresh) | fixed eval set |
| … | … | … | base (fresh) | fixed eval set |
| N | +1,000 | N×1,000 | base (fresh) | fixed eval set |

**Deliverable:** a curve of quality (val loss + Gemini-judge score + qualitative samples)
vs dataset size. Stop the day it plateaus.

**Validity rules (what makes the curve meaningful):**
- **Fresh from base every round** — isolates dataset-size effect; no optimization-path or
  catastrophic-forgetting confound. (Continual daily SFT is a *separate, later* experiment —
  not this one.)
- **Fixed eval set** built on day 1, guaranteed leakage-free (embedding + n-gram check vs all
  training data), never trained on.
- **Global dedup across days** — day-N pairs cannot duplicate any earlier day.
- **Only dataset size varies** — epochs (3), batch (16), LR, seed, prompts all held constant.
- **Fixed generation seed** for eval-response sampling so day-to-day samples are comparable.

---

## 2. Data source (no re-streaming needed)

The cleaned, deduplicated, decontaminated pretraining corpus already exists locally:

```
Replicate-the-125M-SLM-Data-Pipeline/data/corpus/
  case-law/    ~3.1 GB   (~23k docs/shard × 5)
  sec/         ~4.1 GB   (~8.6k docs/shard × 5)
  fineweb-edu/ ~1.9 GB   (~83k docs/shard × 5)
```

One document per line, already cleaned/deduped/decontaminated by the pretraining pipeline —
so teacher passages are already clean and inherit the LexGLUE/CaseHOLD decontamination.
**This is the QA source** (~670k docs, far more than the study will consume).

**Chunking:** stream corpus lines; split long docs into ~500-token windows (project
tokenizer), keep short docs whole. Each day, sample **~334 fresh chunks** stratified to the
domain mix, skipping any `chunk_id` used on a prior day. Record `chunk_id`, `source`, `sha256`.

---

## 3. Per-day request budget & total cost

> **Teacher availability finding (2026-07):** the planned `gemini-2.5-flash` — and the whole
> 2.5 family — returns 404 *"no longer available to new users"* on this free-tier key. The
> stable full-flash aliases (`gemini-flash-latest`, `gemini-3.5-flash`) return persistent 503.
> Tested-reliable on this key: **`gemini-3.1-flash-lite`** (chosen — released, RPD headroom,
> stable for a controlled study) and `gemini-3-flash-preview` (full flash, 4/4, higher quality
> but "preview"). Actual free-tier RPD for the chosen model is discovered empirically at run
> time; the resumable generator absorbs any daily-wall.

**Per day (fits ONE free-tier day at 500 RPD):**

```
generation  : 1,000 ÷ 3  (5 QA/chunk × 0.6 keep-rate) ≈ 334 chunk requests
self-checks : batched (~10 pairs/call)                ≈  25 requests
judge eval  : batched (~10 responses/call)            ≈  15 requests
------------------------------------------------------------------------
total ≈ 375 requests/day   vs 500 RPD → ~125 margin
RPM ~10 → ~40 min wall-clock (with backoff)
```

**Realized per-1,000 counts (each day's new pairs):**

| Mode | | Task | | Domain | |
|---|---|---|---|---|---|
| Closed-book 800 | | QA 550 | | SEC 420 | |
| RAFT 200 | | Summarize 200 | | case-law 350 | |
| | | Extract 150 | | fineweb-edu 230 | |
| | | Rewrite 100 | | | |

**Cost (verify current prices):**

| Item | Estimate |
|---|---|
| Teacher — `gemini-3.1-flash-lite`, free tier (~375 req/day < 500 RPD) | **$0** |
| Embedding dedup (local MiniLM) | $0 |
| Modal fine-tune — **L4**, 3 epochs, per day (grows with cumulative data) | ~$0.06–0.15/run |
| **Whole multi-day study (GPU)** | **~$1–3 total** |

---

## 4. QA generation recipe (Phase 3)

```
sample fresh chunks → teacher: "write N grounded, diverse QA; answer only from passage"
  → parse → grounding check → format check → decontaminate
  → dedup (exact + MinHash + embedding, GLOBAL) → task/domain balance → append chat JSONL
```

**Teacher prompt contract (grounding-first):** "Write diverse question–answer pairs whose
answers are stated **only** in the passage. If a question cannot be answered from it, do not
invent one." Task-typed variants for QA / summarize / extract / rewrite. RAFT variant also
produces some questions the passage does **not** answer → target "not stated in the context."

**Diversity levers:** task-type + difficulty balancing, varied system prompts, and a modest
**Evol-Instruct** pass (thinking on) evolving a subset into harder multi-step questions.

**Resumable + rate-limited generator:** paces under ~10 RPM; writes JSONL incrementally;
idempotent by `chunk_id`; **teacher-agnostic backend** (Groq/Llama-3.3-70B swaps in, no code
change).

**Chat JSONL schema** (one example per line):

```json
{
  "messages": [
    {"role": "system", "content": "<varied domain system prompt>"},
    {"role": "user", "content": "<question>  (+ passage prepended for RAFT)"},
    {"role": "assistant", "content": "<grounded answer>"}
  ],
  "meta": {
    "id": "…", "day": 1, "task": "qa|summarize|extract|rewrite",
    "mode": "closed_book|raft", "source": "sec|case-law|fineweb-edu",
    "chunk_id": "…", "chunk_sha256": "…",
    "teacher": "gemini-2.5-flash", "difficulty": "easy|medium|hard",
    "grounding": {"method": "overlap|nli|self_check", "score": 0.0}
  }
}
```

**Filtering (unique, grounded, well-formed, unseen by eval):** format → grounding
(overlap+NLI, batched self-check on borderline) → decontam (reuse `dedup.py` 13-grams vs
LexGLUE/CaseHOLD) → dedup (exact → MinHash → MiniLM cosine>0.9, **global**) → balance.

---

## 5. SFT training design (Phase 4)

The existing [`train_core.py`](train_core.py) is from-scratch-only (random init, rejects
`init_from_hf`, unmasked packed windows). SFT needs a **new sibling path** — canonical
pretraining files are not modified.

- **Init:** load `Ace-2504/slm-125m-base` weights (HF safetensors), fresh each round.
- **Chat template:** register a Jinja `chat_template` using the existing `<|system|>` /
  `<|user|>` / `<|assistant|>` tokens, terminated by `<|eos|>`.
- **Loss masking:** loss on **assistant tokens only** (system + user + padding → -100). The
  single most important SFT correctness detail.
- **Batching:** per-example, right-padded to batch max (not packed), `max_len = 1024`; skip
  examples over budget (RAFT passages capped ~500–600 tok).
- **Hyperparameters (fixed across all rounds):** epochs **3**, batch **16**, LR peak **3e-5**
  → cosine → **3e-6**, warmup ~5–10% of steps, AdamW (β 0.9/0.95), wd **0.0**, grad-clip
  **1.0**, bf16, seed **1337**.
- **Checkpointing:** atomic save; commit to Modal volume.

**Why full fine-tune (not LoRA / QLoRA):** at 125M, full FT needs only ~6–10 GB — fits any
GPU with capacity headroom LoRA can't match, and adds no rank hyperparameter to confound the
scaling curve. **LoRA** relieves memory pressure that doesn't exist here and caps learning.
**QLoRA** 4-bit-quantizes the base to fit large models on small GPUs — for a 125M model that
degrades quality for **zero** memory benefit. Full FT is correct at this scale.

**Compute reality:** day 1 <1M tokens → seconds of L4 compute; the run is **overhead-bound**
(cold start + model pull + imports ≈ 3–5 min), so wall-clock ≈ 4–7 min, cost ≈ $0.07.

---

## 6. Evaluation (fixed, comparable day-to-day)

- **Fixed eval set:** 100 held-out pairs (stratified), built day 1, leakage-checked, never trained on.
- **Quantitative:** held-out **val loss / perplexity**; per-task metrics (overlap/exact for
  extract, ROUGE-ish for summarize, grounded accuracy for QA).
- **Gemini-as-judge:** a fixed set of ~50 eval questions; each day the model's answers are
  scored **1–5** by Gemini on a rubric (helpfulness, grounding, format). Batched (~10/call).
- **Qualitative:** fixed prompt set, fixed sampling seed → **before (base) vs after** samples,
  logged every day so the base→instruct shift is visible across the curve.

### 6b. Retention / "data loss" (catastrophic-forgetting) monitoring

Fine-tuning can erode the base model's pretrained capability — "data loss." We measure it
directly, every run, and interpret it (not just record it).

- **Retention benchmark:** the model's **perplexity on the original pretraining validation
  set** (`data/tokens/val`, 20,119 raw-text windows). This is the same metric that produced
  the base model's **11.35**, so it is directly comparable.
- **Two perplexities, tracked separately (do not conflate):**
  1. **SFT-eval perplexity** — on the chat-formatted held-out set → should **improve** with SFT
     (task learning).
  2. **Retention perplexity** — on the raw pretraining val set → may **rise** (forgetting +
     chat-distribution shift). This is the "data loss" signal.
- **Reported every run** as: retention PPL, delta vs **base (11.35)**, and delta vs the
  **previous run's checkpoint**. A large, growing retention PPL = the model is trading
  pretrained knowledge for chat behavior.
- **A rise is partly expected** (the model now expects `<|user|>/<|assistant|>` framing); the
  research question is *how much* forgetting each data-scale/epoch setting costs. If it becomes
  severe, documented mitigations (not applied unless needed): lower LR, fewer epochs, mix a
  small fraction of raw pretraining windows into SFT (replay), or lighter-touch tuning.
- **Where it runs:** on the same Modal GPU run, right after training, against the pretraining
  val bins (already on the `slm-125m` volume from pretraining; re-upload if absent). Subsample
  (e.g. 100 batches) for a fast, stable estimate.

## 7. GPU / Modal setup

- **GPU:** single **L4 24 GB** (~$0.80/hr). At 125M the job is overhead-bound, so a faster GPU
  barely helps and costs more per idle minute:

  | GPU | ~$/hr | Compute (3 ep, 1k pairs) | Wall (incl. overhead) | Cost/run |
  |---|---|---|---|---|
  | **L4 24 GB** | ~$0.80 | ~45 s | ~4–7 min | **~$0.06–0.09** |
  | A100-40GB | ~$2.10 | ~15 s | ~3–6 min | ~$0.11–0.21 |
  | H100 80GB | ~$3.95 | ~5 s | ~3–6 min | ~$0.20–0.40 |

  H100 is the **worst value** here (paying top rate to watch a cold start). L4 wins.
- **App/volume:** reuse the authorized `slm-125m` Modal volume; new app `slm-125m-sft`.
- **Image:** pin `torch==2.4.1`, `transformers==4.46.3`, `tokenizers==0.20.3`, `numpy<2.0`,
  `huggingface_hub`.
- **Run detached** + resumable checkpoints, mirroring pretraining ops.

## 8. Output & deployment

- After the curve plateaus, export the best checkpoint to **`Ace-2504/fine-tuned-125m-slm`**
  (safetensors + tokenizer **with chat template** + `generation_config` + model card: recipe,
  teacher, dataset stats, scaling curve, eval).
- Update [`space/app.py`](space/app.py) + `web/` demo to **apply the chat template** (currently
  raw prompts) — likely a `/chat` path behind the existing shared-secret.

---

## 9. Research logging — capture EVERYTHING, per day (feeds the write-up)

Persist to `research_log.md` + `run_manifest.json` + `metrics.jsonl`, **one record per day**.

**Modal runtime (per run):** app + function name, GPU type/region, image digest + pinned
versions, **$/hr, billed seconds, total $**, **cold-start time**, wall-clock, CPU/RAM, **peak
GPU memory**, GPU util %, **tokens/sec**, est. **MFU %**, volume I/O, egress, checkpoint sizes,
exit status, retries/preemptions, Modal run URL/ID.

**Training (per day):** cumulative dataset size, full config, per-step `loss/lr/grad_norm/
tokens_seen/tokens_per_sec`, final val loss/perplexity + task metrics, **Gemini-judge score**,
before/after samples.

**Generation (per day):** teacher + version + params, chunks processed, raw pairs, **drop
counts per filter stage**, new pairs kept, cumulative total, per-source/task/mode/difficulty
counts, dedup stats, teacher tokens in/out, **requests used vs 500 RPD**, wall time, $ (=0).

**Scaling curve:** the assembled table of (day, #pairs, val loss, judge score) + plot.

**Reproducibility:** seeds, git commit, dataset hash, tokenizer hash, base-model revision,
package versions.

### 9b. Per-run report (REQUIRED after every training run)

After each run, `make_report.py` emits a self-contained report — `reports/run-<NN>.md` (human)
plus `reports/run-<NN>.json` (machine) — containing **everything** for that run:

1. **Run identity:** run number, date, day/dataset-scale, git commit, base-model revision,
   Modal run URL/ID.
2. **All parameters discussed so far:** model arch (12L/768d/12h, 125.8M, ctx 1024, tied emb);
   full SFT hyperparameters (epochs 3, batch 16, LR 3e-5→3e-6 cosine, warmup, AdamW β, wd 0.0,
   grad-clip, bf16, seed); fine-tune type (full FT); GPU + Modal image + pinned versions;
   chat-template + assistant-only masking; dataset composition (size, mode/task/domain/
   difficulty counts, teacher, per-filter drop counts, dedup stats).
3. **Data loss / forgetting:** retention perplexity on the pretraining val set, with **delta vs
   base (11.35)** and **delta vs previous run** — plus a plain-English verdict (e.g. "retention
   PPL 11.35 → 12.10, +6.6% — mild forgetting").
4. **Perplexity comparison:** this run's **SFT-eval perplexity** and **retention perplexity**
   vs the **previous checkpoint** (run N-1); for **run 1, vs the pretrained base model**. Shown
   as a small table with deltas and direction (↑ worse / ↓ better, per metric).
5. **Task quality:** SFT-eval val loss, per-task metrics, Gemini-judge score, before/after
   sample generations.
6. **Modal runtime:** $/hr, billed seconds, total $, cold-start, wall-clock, peak GPU mem,
   tokens/sec, MFU, exit status.
7. **Deltas vs the running scaling curve** so the report doubles as one point on the curve.

The per-run reports are the primary source material for the later observations write-up.

---

## 10. Teacher-limit resilience

- **RPM/TPM (per-minute):** auto exponential backoff + jitter (honor `Retry-After`).
- **RPD (daily wall):** persistent 429s → log progress, write resume marker, **exit 0** →
  resume next day from `chunk_id`. No data lost. (Also just means that day's +1k rolls over.)
- **Finish-now option:** one-flag switch to **Groq/Llama-3.3-70B** on remaining chunks (log
  `teacher` per record; keep whole task/domain slices single-teacher), or enable Gemini
  billing (~$0.50). Default = pause/resume; escalation is opt-in.

---

## 11. File manifest (to be created in Phases 3–4 — NOT NOW)

```
sft/
  sft_config.py        # mix ratios, sizes, hyperparams, chat template, day/scaling config
  gen_qa.py            # teacher-agnostic, resumable, rate-limited daily QA generator
  build_dataset.py     # filter → decontam → GLOBAL dedup → balance → append → cumulative JSONL
  sft_data.py          # loader: render template, tokenize, assistant-only masking, collate
  sft_train_core.py    # SFT engine: load HF base fresh, masked loss, 3 epochs, cosine LR, ckpt
  modal_sft.py         # Modal L4 app, detached, per-run research logging
  sft_eval.py          # SFT-eval + Gemini-judge + RETENTION ppl (pretrain val) + before/after
  make_report.py       # emit reports/run-<NN>.{md,json}: all params + data-loss + ppl vs prev
  export_sft_hf.py     # push Ace-2504/fine-tuned-125m-slm + chat template + card
  research_log.md      # human-readable per-day notes + scaling curve
  run_manifest.json    # machine-readable captured metrics
  reports/             # per-run detailed reports (run-01.md/json, run-02…) — tracked in git
data/sft/              # generated JSONL, cumulative (gitignored; regenerable)
  eval.jsonl           # fixed held-out eval set
```
Canonical pretraining files (`config.py`, `pipeline.py`, `cleaning.py`, `dedup.py`,
`train_core.py`) are **not modified**.

---

## 12. Risks & open items

- **Curve may plateau early** at 125M → that's a *result*, not a failure; stop and report it.
- **Shared 500 RPD** (Flash + Flash-Lite) → per day needs ~375; resume covers overruns.
- **1024 ctx** caps RAFT passage length → enforce token cap at generation time.
- **Teacher hallucination** → overlap+NLI+self-check gate; log drop rates.
- **Domain narrowness** → legal/financial by design; general small-talk out of scope for v1.
- **Gemini-judge bias** (same family as teacher) → note as a limitation; val loss is the
  neutral anchor metric.
- **Catastrophic forgetting / "data loss"** → retention PPL rise is partly expected (chat-
  distribution shift); monitored every run (§6b) and reported vs base + previous checkpoint
  (§9b). Mitigations documented, applied only if the rise is severe.

---

## 13. Prerequisites from the user (before Phase 3)

| # | Need | Status / action |
|---|---|---|
| 1 | **Gemini API key** (free tier) | Put it in `sft/.env` as `GEMINI_API_KEY=…` (gitignored) — **do not paste it into chat**. Used for generation + Gemini-judge. |
| 2 | **Gemini SDK** | Confirm OK to use the `google-genai` Python SDK, model id `gemini-2.5-flash`. |
| 3 | **Modal** authorized | You confirmed. I'll verify `modal token`/volume at Phase 4 start. |
| 4 | **Hugging Face token (write)** | Needed to pull base (if not public) and push `fine-tuned-125m-slm`. Confirm you're logged in locally (`huggingface-cli login`) — reuse the pretraining login. |
| 5 | **Base repo access** | Confirm `Ace-2504/slm-125m-base` is reachable (public or via your HF token). |
| 6 | **Local Python 3.12 env** | For generation + dedup: `google-genai`, `sentence-transformers`, `datasketch`, `transformers`, `numpy`, `python-dotenv`. I'll set this up in Phase 3. |
| 7 | **Groq key** (optional) | Only if you want the free fallback teacher ready. Not required. |

Nothing else is blocking. Corpus is already local; no data download needed.

---

## 14. Phase status

- [x] Phase 1 — Discussion
- [x] Phase 2 — Plan (this document, Plan A locked)
- [ ] Phase 3 — QnA generation (daily, cumulative)
- [ ] Phase 4 — Fine-tuning on Modal (daily, from base, scaling curve)
