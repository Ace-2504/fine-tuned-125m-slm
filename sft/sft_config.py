"""Single source of truth for the SLM-125M supervised fine-tuning (SFT) project.

Plan A — cumulative data-scaling study: each day +1,000 fresh QnA pairs, re-fine-tune
from the base model on the cumulative set, evaluate on a fixed held-out set, and track
the scaling curve + catastrophic-forgetting ("data loss").

Paths default to the sibling pretraining repo (which holds the cleaned corpus, tokenizer,
and pretraining val bins) and are overridable via env vars. Nothing here has import-time
side effects beyond reading env.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# --- Locate this repo and the sibling pretraining repo -------------------------------
SFT_DIR = Path(__file__).resolve().parent                 # .../125M-model-base/sft
REPO_ROOT = SFT_DIR.parent                                # .../125M-model-base
SLM_COURSE = REPO_ROOT.parent.parent                      # .../SLM-course
PRETRAIN_REPO = SLM_COURSE / "Replicate-the-125M-SLM-Data-Pipeline"

# Import the base model/tokenizer config from the pretraining repo layout (config.py
# lives at REPO_ROOT). Used for special tokens, model arch, seq len.
sys.path.insert(0, str(REPO_ROOT))
import config as base_config  # noqa: E402

# --- Data sources (already on disk; no re-streaming) ---------------------------------
CORPUS_DIR = Path(os.environ.get("SLM_CORPUS_DIR", PRETRAIN_REPO / "data" / "corpus"))
TOKENIZER_DIR = Path(os.environ.get("SLM_TOKENIZER_DIR", PRETRAIN_REPO / "data" / "tokenizer"))
# Original pretraining validation bins — the retention / "data loss" benchmark.
PRETRAIN_VAL_DIR = Path(os.environ.get("SLM_PRETRAIN_VAL_DIR", PRETRAIN_REPO / "data" / "tokens" / "val"))

# --- Track (v1 = original mix; v2 = grounded-heavy pivot) ----------------------------
# v2 runs on its own namespaces so v1 stays intact + Day-4-resumable. Set SFT_TRACK=v2.
TRACK = os.environ.get("SFT_TRACK", "v1")
_TSFX = "" if TRACK == "v1" else f"-{TRACK}"

# --- SFT working outputs -------------------------------------------------------------
DATA_SFT_DIR = Path(os.environ.get("SLM_SFT_DATA_DIR", REPO_ROOT / "data" / f"sft{_TSFX}"))  # gitignored
PAIRS_JSONL = DATA_SFT_DIR / "pairs.jsonl"            # cumulative, all kept pairs (all days)
RAW_JSONL = DATA_SFT_DIR / "raw.jsonl"               # raw teacher output before filtering
EVAL_JSONL = DATA_SFT_DIR / "eval.jsonl"             # fixed held-out eval set (built once)
JUDGE_QUESTIONS_JSONL = DATA_SFT_DIR / "judge_questions.jsonl"
CHUNKS_USED_PATH = DATA_SFT_DIR / "chunks_used.json"  # chunk_ids consumed (cross-day idempotency)
GEN_STATE_PATH = DATA_SFT_DIR / "gen_state.json"     # resume marker for the generator
REPORTS_DIR = SFT_DIR / f"reports{_TSFX}"            # per-run reports (tracked in git)
ENV_PATH = SFT_DIR / ".env"

# --- Model identity ------------------------------------------------------------------
BASE_HF_REPO = "Ace-2504/slm-125m-base"
OUTPUT_HF_REPO = "Ace-2504/fine-tuned-125m-slm"
BASE_VAL_PERPLEXITY = 11.35   # base model's pretraining-val PPL — retention baseline

# Model arch + tokens come straight from the base config (do not diverge).
MODEL = base_config.MODEL
SPECIAL_TOKENS = base_config.SPECIAL_TOKENS
EXTRA_CHAT_TOKENS = base_config.EXTRA_CHAT_TOKENS
MAX_SEQ_LEN = base_config.SEQ_LEN     # 1024 — hard context ceiling

# --- Teacher (Gemini) ----------------------------------------------------------------
# NOTE: gemini-2.5-flash (originally planned) is BLOCKED for new-user generation on this
# key (404 "no longer available to new users"), as is the whole 2.5 family. The stable
# full-flash aliases (gemini-flash-latest, gemini-3.5-flash) return persistent 503 on
# free tier. Reliable on this key (tested): gemini-3-flash-preview (full flash, 4/4) and
# gemini-3.1-flash-lite. Chose the released flash-LITE for RPD headroom + a stable,
# reproducible teacher across the scaling study; grounded QA needs no more capability.
TEACHER_MODEL = "gemini-3.1-flash-lite"
TEACHER_MODEL_HIGHQ = "gemini-3-flash-preview"   # stronger alt if RPD allows / for hard slice
TEACHER_THINKING_BULK = False         # off for bulk QA; on only for the Evol-Instruct slice
FREE_TIER_RPM = 10                    # requests/min (paces the generator) — verify empirically
FREE_TIER_RPD = 500                   # requests/day (shared across flash/flash-lite)
REQUEST_MIN_INTERVAL_S = 6.5          # ~60/RPM with margin
MAX_RETRIES = 6                       # exponential backoff on 429/5xx
FALLBACK_TEACHER = "groq/llama-3.3-70b-versatile"   # only if backend is switched

# --- Generation granularity ----------------------------------------------------------
CHUNK_TOKENS = 500                    # target passage size (project tokenizer)
RAFT_PASSAGE_MAX_TOKENS = 550         # cap so a RAFT example still fits in 1024 ctx
QA_PER_CHUNK = 5
PAIRS_PER_DAY = 1000                  # final kept pairs added each day
ASSUMED_KEEP_RATE = 0.60             # after all filters (reference: 20–50% dropped)
RAW_TARGET_PER_DAY = int(PAIRS_PER_DAY / ASSUMED_KEEP_RATE)          # ~1667 raw
CHUNKS_PER_DAY = -(-RAW_TARGET_PER_DAY // QA_PER_CHUNK)              # ceil ~334

# --- Composition (mirror pretraining; enforced by the balancer) ----------------------
if TRACK == "v2":
    # grounded-heavy pivot: mostly context/RAFT (learnable); closed-book only for general knowledge
    MODE_MIX = {"closed_book": 0.15, "raft": 0.85}
    TASK_MIX = {"qa": 0.40, "summarize": 0.25, "extract": 0.20, "rewrite": 0.15}
    CLOSED_BOOK_SOURCES = {"fineweb-edu"}          # closed-book QA only from general-knowledge web
    GEN_NO_REPEAT_NGRAM = 3                          # decoding fix (kills greedy repetition loops)
    GEN_REPETITION_PENALTY = 1.3
else:
    MODE_MIX = {"closed_book": 0.80, "raft": 0.20}
    TASK_MIX = {"qa": 0.55, "summarize": 0.20, "extract": 0.15, "rewrite": 0.10}
    CLOSED_BOOK_SOURCES = {"sec", "case-law", "fineweb-edu"}   # v1: any source
    GEN_NO_REPEAT_NGRAM = 0                          # v1: greedy (preserve internal comparability)
    GEN_REPETITION_PENALTY = 1.0
DOMAIN_MIX = {"sec": 0.42, "case-law": 0.35, "fineweb-edu": 0.23}
DIFFICULTY_MIX = {"easy": 0.4, "medium": 0.4, "hard": 0.2}          # hard ≈ Evol-Instruct slice

# --- Varied domain system prompts (legal + financial assistant) ----------------------
SYSTEM_PROMPTS: tuple[str, ...] = (
    "You are a precise legal and financial assistant. Answer clearly and only from what you know; if unsure, say so.",
    "You are an expert assistant for US case law and SEC filings. Give accurate, concise answers.",
    "You are a helpful domain assistant specializing in law and corporate finance. Be factual and to the point.",
    "You are a knowledgeable legal/financial analyst. Provide grounded, well-structured answers.",
    "You assist with legal and financial questions. Answer faithfully; do not invent facts.",
    "You are a careful assistant for legal documents and financial disclosures. Prefer accuracy over length.",
)
# RAFT examples use a context-grounded system prompt.
RAFT_SYSTEM_PROMPT = (
    "You are a grounded assistant. Answer the question using ONLY the provided context. "
    "If the answer is not in the context, reply exactly: not stated in the context."
)

# --- Chat template (Jinja) — uses the tokenizer's existing chat tokens ----------------
# Renders: <|bos|><|system|>\n{sys}<|eos|>\n<|user|>\n{q}<|eos|>\n<|assistant|>\n{a}<|eos|>\n
CHAT_TEMPLATE = (
    "{{ bos_token }}"
    "{% for message in messages %}"
    "{{ '<|' + message['role'] + '|>\n' + message['content'] + eos_token + '\n' }}"
    "{% endfor %}"
    "{% if add_generation_prompt %}{{ '<|assistant|>\n' }}{% endif %}"
)

# --- Filtering / dedup / grounding ---------------------------------------------------
MIN_ANSWER_CHARS = 8
MAX_ANSWER_CHARS = 1200
MIN_QUESTION_CHARS = 8
GROUNDING_OVERLAP_MIN = 0.55          # frac of answer content-words present in passage
GROUNDING_BORDERLINE = (0.40, 0.55)  # range that triggers a batched Flash self-check
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEDUP_COSINE_THRESHOLD = 0.90         # drop near-duplicate questions above this
MINHASH_PERM = 32
MINHASH_THRESHOLD = 0.80
DECONTAM_NGRAM = 13                   # reuse pretraining machinery vs LexGLUE / CaseHOLD
EVAL_HOLDOUT_SOURCES = base_config.EVAL_HOLDOUT   # ("coastalcph/lex_glue", "casehold/casehold")

# --- Evaluation ----------------------------------------------------------------------
EVAL_SIZE = 100                       # fixed held-out SFT pairs (built once, never trained on)
JUDGE_QUESTION_COUNT = 50             # fixed question set scored 1–5 by Gemini each run
RETENTION_EVAL_BATCHES = 100          # subsample of pretraining val for a fast, stable PPL

# --- SFT training hyperparameters (fixed across ALL scaling rounds) -------------------
EPOCHS = 3
BATCH_SIZE = 16
LR = 3e-4 * 0.1                        # 3e-5 peak
MIN_LR = 3e-6
WARMUP_RATIO = 0.05
WEIGHT_DECAY = 0.0
GRAD_CLIP = 1.0
BETA1, BETA2 = 0.9, 0.95
SEED = 1337

# --- Modal ---------------------------------------------------------------------------
MODAL_APP = f"slm-125m-sft{_TSFX}"
MODAL_VOLUME = "slm-125m"             # reuse the authorized pretraining volume
MODAL_GPU = "L4"                      # best value; job is overhead-bound (see plan §7)
MODAL_TIMEOUT_S = 60 * 60             # 1 h ceiling (runs take minutes)
MODAL_SFT_REMOTE = f"/sft{_TSFX}"                  # uploaded dataset on the volume
MODAL_CKPT_REMOTE = f"/checkpoints/sft{_TSFX}"     # SFT checkpoints on the volume


def summary() -> str:
    return (
        f"SFT config for {BASE_HF_REPO} -> {OUTPUT_HF_REPO}\n"
        f"  corpus:     {CORPUS_DIR}\n"
        f"  tokenizer:  {TOKENIZER_DIR}\n"
        f"  pretrain val (retention): {PRETRAIN_VAL_DIR}\n"
        f"  teacher:    {TEACHER_MODEL} (free tier {FREE_TIER_RPD} RPD / {FREE_TIER_RPM} RPM)\n"
        f"  per day:    {PAIRS_PER_DAY} pairs  (~{CHUNKS_PER_DAY} chunks x {QA_PER_CHUNK} QA, keep~{ASSUMED_KEEP_RATE:.0%})\n"
        f"  mode:       {MODE_MIX}\n"
        f"  task:       {TASK_MIX}\n"
        f"  domain:     {DOMAIN_MIX}\n"
        f"  train:      full FT, {EPOCHS} epochs, batch {BATCH_SIZE}, lr {LR:g}->{MIN_LR:g}, seed {SEED}\n"
        f"  GPU:        Modal {MODAL_GPU} (app {MODAL_APP}, volume {MODAL_VOLUME})\n"
        f"  ctx:        {MAX_SEQ_LEN} tokens (hard ceiling)\n"
    )


if __name__ == "__main__":
    print(summary())
    print("paths exist:")
    for label, p in [("corpus", CORPUS_DIR), ("tokenizer", TOKENIZER_DIR),
                     ("pretrain_val", PRETRAIN_VAL_DIR), ("env", ENV_PATH)]:
        print(f"  {label:14} {'OK ' if Path(p).exists() else 'MISSING'} {p}")
