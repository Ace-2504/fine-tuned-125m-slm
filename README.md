# SLM-125M — SFT data-scaling study

**We scaled supervised fine-tuning data 10× and answer quality didn't move — but catastrophic
forgetting tripled.**

A ten-round, controlled data-scaling study fine-tuning a 125.8M-parameter base model
([Ace-2504/slm-125m-base](https://huggingface.co/Ace-2504/slm-125m-base), pretrained from scratch on
2.04B tokens). Each round added 1,000 teacher-generated QnA pairs, re-fine-tuned **from the base**, and
scored against a frozen eval set. Method frozen throughout, so the curve isolates the effect of data alone.

📊 **Full write-up:** https://ace-2504.github.io/fine-tuned-125m-slm/
· 🔍 **Per-round feedback:** https://ace-2504.github.io/fine-tuned-125m-slm/feedback.html

---

## Result

| Round | Pairs | SFT-eval ppl | Retention ppl | Forgetting | Judge /5 |
| --- | --- | --- | --- | --- | --- |
| 0 (base) | 0 | 24.44 | 11.35 | — | 1.00 |
| 1 | 1,000 | 8.60 | 12.05 | +6.1% | 1.32 |
| **2** | 2,000 | 8.00 | 12.42 | +9.5% | **1.50** ← gain ends here |
| 3–9 | 3k–9k | 7.70 → 7.05 | 12.60 → 13.18 | +11.0% → +16.2% | 1.46 · 1.50 · 1.52 · 1.54 · 1.60 · 1.60 · 1.54 |
| **10** | **10,000** | **7.01** | **13.20** | **+16.3%** | **1.54** |

**Findings**

- **The plateau.** All gain arrived by round 2. From 2k → 10k — a **5× data increase** — the judge moved
  **+0.04**, inside the measured **±0.07 noise band**. Rounds 7–8 spiked to 1.60 and round 9 collapsed
  back, testing and rejecting the "late climb" hypothesis.
- **Forgetting was the only thing data bought.** Retention perplexity rose **monotonically in all ten
  rounds**, 11.35 → 13.20, nearly tripling — while quality stood still.
- **Quality regressed at scale.** The probe *"What is the standard of proof in a civil lawsuit?"* was
  correct for **seven straight rounds (3–9)** — "preponderance of the evidence" — then broke at round 10.
- **Perplexity is not quality.** SFT-eval ppl improved in *every* round (8.60 → 7.01) against a flat
  judge and a regressing sample. Reporting it as the headline would have told the opposite story.
- **Best checkpoint is round 2, not round 10** — same judge, **half the forgetting**, 1/5 the data.

**Why:** ~40% of training was **closed-book QA** — recall a document fact from a single exposure. A 125M
model can't store long-tail facts that way, so no amount of supervision installs them. Common facts do
land ("preponderance of the evidence" by round 3); one-off document specifics never do.

**Cost:** ~$4.60 total (~$1.14 Modal GPU + ~$3.50 teacher) for 11 training runs and 10,000 pairs.

## Method

- **Base:** LlamaForCausalLM, 12L / 768d / 12h, 125.8M params, vocab 16,384, ctx 1,024, tied embeddings.
- **Teacher:** `gemini-3.1-flash-lite` writes QnA grounded in passages from the *same corpus the base was
  pretrained on* (US case law, SEC filings, educational web) — answers must be stated in the passage.
- **Data:** format + grounding gates → exact/embedding dedup → decontamination → balanced to a fixed
  task/domain mix → chat JSONL. Eval set frozen at round 1 and chunk-quarantined (zero leakage).
- **Training:** full fine-tune (no LoRA/QLoRA — unnecessary at 125M), 3 epochs, batch 16, LR 3e-5→3e-6
  cosine, bf16, **assistant-only loss masking**, seed 1337. Single **Modal L4** (~$0.10/run).
- **Eval:** SFT-eval perplexity · **retention perplexity** on the original pretraining val bins
  (catastrophic forgetting, directly comparable to the base's 11.35) · Gemini-as-judge 1–5 · fixed
  greedy sample generations.

## Layout

| Path | What it is |
| --- | --- |
| `sft/sft_config.py` | Single source of truth (mix, hyperparameters, chat template, tracks) |
| `sft/gen_qa.py` | Daily QnA generator — rate-limited, resumable, teacher-agnostic |
| `sft/build_dataset.py` | Filter → dedup → decontaminate → balance → split → chat JSONL |
| `sft/sft_data.py` | Loader with assistant-only loss masking |
| `sft/sft_train_core.py` | SFT engine + baseline mode + retention/judge eval |
| `sft/modal_sft.py` | Modal L4 training app |
| `sft/make_report.py` | Per-run report (params + data-loss + ppl vs previous checkpoint) |
| `sft/chain_days.sh` | Runs N rounds end-to-end (gen → build → upload → train → report) |
| `sft/reports/` | All 11 per-run reports (`run-00…10`) |
| `sft/training-feedback/` | Per-round feedback (`day1…day10`) + the v2 pivot decision |
| `sft/research_log.md` | Full chronological log |
| `docs/` | The published GitHub Pages write-up |

Root `*.py` files are the inherited **pretraining** pipeline for the base model (stream → clean → dedup
→ tokenize → pretrain); see `TRAINING_PLAN_*.md`. Large artifacts (`data/`, checkpoints) are gitignored
and regenerated.

## Running it

```bash
pip install -r requirements.txt          # + google-genai, sentence-transformers
cp sft/.env.example sft/.env             # add GEMINI_API_KEY (gitignored)
cd sft
python gen_qa.py --day 1                 # generate ~1,000 pairs
python build_dataset.py                  # filter/dedup/balance -> data/sft/pairs.jsonl
modal volume put slm-125m ../data/sft/pairs.jsonl /sft/pairs.jsonl --force
modal run modal_sft.py --day 1           # train on Modal L4 (--day 0 = base baseline)
python make_report.py --day 1            # report + judge
./chain_days.sh 2 10                     # or run many rounds end-to-end
```

## Status & what's next

**v1 is closed** as a clean negative result — the data-volume question is answered.

**v2 (parked, shipped):** the one untested lever is the **mix**. v2 flips training to *open-book* —
the passage stays in the prompt (`context + question → answer`), ~92% grounded, closed-book restricted
to general knowledge — plus a decoding fix and a per-mode judge. It runs on a separate track
(`SFT_TRACK=v2`) so v1 stays intact. See `sft/training-feedback/v2-pivot.md`.

---

Built by **Harman Sandhu** ([@Ace-2504](https://github.com/Ace-2504)).
Base model write-up: [slm-125m-observations](https://ace-2504.github.io/slm-125m-observations/).
