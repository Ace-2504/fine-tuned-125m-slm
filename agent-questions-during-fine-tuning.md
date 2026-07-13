# Agent Questions During Fine-Tuning (Discussion Phase)

Record of the questions Claude (acting as fine-tuning engineer/researcher) asked
during the **discussion phase**, each with the recommended default and the
decision the user made. This is a research log artifact.

Legend: **Q** = question · **Default** = Claude's recommendation · **Decision** = user's answer.

---

## A. Target behavior & example design

**A1 — Closed-book vs open-book (the pivotal fork)**
Q: Teach domain knowledge into the weights (closed-book, Q→A, no passage at
train/infer time), or teach "answer from provided context" (open-book / RAFT,
passage in the prompt)? The 1024-token context is the hard ceiling.
Default: ~80% closed-book (domain assistant) + ~20% RAFT-style "answer from
context / say 'not stated'".
**Decision: default (80/20 closed-book / RAFT).**

**A2 — Persona**
Q: A legal + financial domain assistant, or a more general helpful assistant?
Default: domain assistant (honest to the base, cleaner research story).
**Decision: domain assistant.**

**A3 — Task-type mix**
Q: Proportions across QA / summarize / extract-to-JSON / rewrite?
Default: 55% QA, 20% summarize, 15% extract, 10% rewrite.
**Decision: default.**

**A4 — Domain mix of the pairs**
Q: Mirror pretraining (SEC 42% / case-law 35% / edu 23%) or rebalance?
Default: mirror pretraining so SFT reinforces what the base knows.
**Decision: mirror pretraining.**

**A5 — Single-turn vs multi-turn**
Q: Single-turn only, or some multi-turn?
Default: single-turn for v1 (1024 ctx makes multi-turn cramped).
**Decision: single-turn.**

**A6 — System prompt**
Q: Fixed, varied, or none?
Default: a small set of varied domain system prompts.
**Decision: default (varied domain system prompts).**

## B. Teacher generation

**B7 — Teacher model / access / where it runs**
Q: Gemini API available? Run generation locally or on Modal? NOTE: user has a
**free-tier** Gemini key and asked whether that suffices or if a different free
teacher is better.
Default: run locally (API calls, no GPU).
**Decision: user has a free-tier Gemini API key.**
Claude's confirmation: free tier is sufficient at this scale (~3.3k requests)
IF the generator is resumable + rate-limited; RPD is the bottleneck (spread over
days). Free-tier data may be used by Google to improve products. Options:
(a) free-tier Gemini 2.5 Flash [chosen primary], (b) enable billing (~$5–12,
removes limits, ~1 h), (c) free fallback: Groq-hosted Llama 3.3 70B. Generator
will be built teacher-agnostic.

**B8 — "Thinking" mode on Flash**
Q: On (better pairs, ~2× output cost) or off (cheaper)?
Default: off for bulk QA, on only for the harder Evol-Instruct slice.
**Decision: default.**

**B9 — QA per chunk / chunk size**
Q: How many QA per chunk and what chunk size?
Default: ~500-token chunks, ~5 QA each.
**Decision: default.**

**B10 — Augmentation**
Q: Grounded-QA only for v1, or also Self-Instruct / Evol-Instruct?
Default: grounded-QA core + a modest Evol-Instruct slice for hard multi-step.
**Decision: default.**

## C. Quality, dedup, eval

**C11 — Semantic dedup config**
Q: Embedding model + cosine threshold?
Default: local `all-MiniLM-L6-v2`, drop cosine > 0.9, plus exact-hash dedup.
**Decision: "whatever you find best."**
Claude's choice: dedup on the question (and question+answer) using local
`all-MiniLM-L6-v2` embeddings, drop near-duplicates at cosine > 0.9, plus
exact-hash + MinHash near-exact dedup (reusing the pretraining `dedup.py`
machinery). Fully local, no API cost, no data egress.

**C12 — Grounding verification method**
Q: String-overlap, NLI, or teacher self-check?
Default: string-overlap gate + a Flash self-check on borderline cases.
**Decision: default.**

**C13 — Held-out eval + decontamination**
Q: Build a small held-out SFT eval set + harness, and decontaminate the SFT set
against LexGLUE / CaseHOLD like pretraining did?
Default: yes to both.
**Decision: default.**

## D. Training & output

**D14 — Hyperparameters / epochs**
Q: Settle hyperparameters in the plan phase (full FT, LR ~2e-5 cosine, short
warmup, assistant-only loss masking, max len 1024, bf16)?
Default: proposed above.
**Decision: proceed — but do exactly 1 EPOCH of fine-tuning.**

**D15 — Output repo + demo update**
Q: Push SFT model to a new HF repo and update the Space/web demo to apply the
chat template?
Default: yes, `Ace-2504/slm-125m-instruct`.
**Decision: yes — name the repo `fine-tuned-125m-slm`.**

## E. Modal & research logging

**E16 — Base weights for init**
Q: Init SFT from `ckpt.pt` on the Modal volume, or from the HF repo
`Ace-2504/slm-125m-base`?
Default: from the HF repo (self-contained, reproducible).
**Decision: default (init from HF base repo).**

**E17 — Modal state / authorization**
Q: Reuse the existing `slm-125m` app/volume/token, or a fresh volume? Is the CLI
token still authorized?
**Decision: everything is authorized (per user's knowledge).**

**E18 — Research logging scope**
Q: The referenced Modal artifact link is private (Claude can't open it). Paste
its fields, or shall Claude propose a full research-log schema?
Default: propose a schema in the plan phase.
**Decision: capture everything possible — the more the better.**
(Realized as the "Research logging" section of `fine-tuning-plan.md`.)
