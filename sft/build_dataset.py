"""Turn raw teacher output into the training-ready SFT dataset (Phase 3).

Pipeline:  raw.jsonl
  -> format filter (empty / too short / too long / unparseable)
  -> task-aware grounding gate (answer supported by its passage)
  -> global dedup (exact-hash + MiniLM embedding cosine > threshold)
  -> decontaminate vs LexGLUE / CaseHOLD (best-effort; corpus was already decontaminated)
  -> assemble chat messages + drop anything over the 1024-token context
  -> hold out a FIXED eval set + judge questions (once, on first build)
  -> light balance to the task mix
  -> write cumulative, day-ordered pairs.jsonl

Re-runnable: reads ALL of raw.jsonl each time, so after N days it yields the cumulative,
deduped set. eval.jsonl / judge_questions.jsonl are built once and then frozen and excluded.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

import sft_config as C
import prompts

_WORD = re.compile(r"[a-z0-9]{4,}")
NOT_STATED = prompts.NOT_STATED
_GROUND_MIN = {"qa": C.GROUNDING_OVERLAP_MIN, "extract": 0.45, "summarize": 0.30, "rewrite": 0.30}


def _content_words(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def _overlap(answer: str, passage: str) -> float:
    aw = _content_words(answer)
    if not aw:
        return 0.0
    pset = set(_content_words(passage))
    return sum(1 for w in aw if w in pset) / len(aw)


def _format_ok(r: dict) -> bool:
    a = r.get("answer", "").strip()
    if not (C.MIN_ANSWER_CHARS <= len(a) <= C.MAX_ANSWER_CHARS):
        return False
    if r["task"] == "qa" and len(r.get("question", "").strip()) < C.MIN_QUESTION_CHARS:
        return False
    if r["task"] == "extract" and a != NOT_STATED:
        # extract answers should look like JSON
        s = a.strip()
        if not (s.startswith("{") or s.startswith("[")):
            return False
    return True


def _grounded(r: dict) -> bool:
    if r.get("answer", "").strip() == NOT_STATED:
        return True                      # refusal target — grounding N/A
    thr = _GROUND_MIN.get(r["task"], 0.4)
    return _overlap(r["answer"], r["passage"]) >= thr


# ---- assembly into chat messages ----------------------------------------------------

def _assemble(r: dict, rng: random.Random) -> dict:
    task, mode = r["task"], r["mode"]
    passage, q, a = r["passage"], r.get("question", ""), r["answer"]
    if task == "qa" and mode == "closed_book":
        system = rng.choice(C.SYSTEM_PROMPTS)
        user = q
    elif task == "qa" and mode == "raft":
        system = C.RAFT_SYSTEM_PROMPT
        user = f"Context:\n{passage}\n\nQuestion: {q}"
    else:  # summarize / extract / rewrite (context)
        system = rng.choice(C.SYSTEM_PROMPTS)
        user = prompts.user_instruction(task, passage, rng)
    return {"messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user},
                         {"role": "assistant", "content": a}],
            "meta": {"task": task, "mode": mode, "source": r["source"],
                     "difficulty": r.get("difficulty", "medium"), "day": r.get("day", 1),
                     "chunk_id": r["chunk_id"], "teacher": r.get("teacher", C.TEACHER_MODEL)}}


def _fits_context(rec: dict, tokenizer) -> bool:
    ids = tokenizer.apply_chat_template(rec["messages"], tokenize=True,
                                        add_generation_prompt=False)
    return len(ids) <= C.MAX_SEQ_LEN


# ---- dedup --------------------------------------------------------------------------

def _dedup_key(r: dict) -> str:
    txt = (r.get("question", "") + " || " + r["answer"]).lower().strip()
    return hashlib.sha256(txt.encode("utf-8")).hexdigest()


def _embedding_dedup(recs: list[dict]) -> list[dict]:
    """Greedy drop of near-duplicate questions/answers within each task via MiniLM cosine."""
    from sentence_transformers import SentenceTransformer, util
    model = SentenceTransformer(C.EMBED_MODEL)
    kept: list[dict] = []
    by_task: dict[str, list[dict]] = defaultdict(list)
    for r in recs:
        by_task[r["task"]].append(r)
    for task, group in by_task.items():
        texts = [(g.get("question") or g["answer"]) for g in group]
        emb = model.encode(texts, convert_to_tensor=True, normalize_embeddings=True,
                           batch_size=128, show_progress_bar=False)
        keep_idx: list[int] = []
        for i in range(len(group)):
            if not keep_idx:
                keep_idx.append(i); continue
            sims = util.cos_sim(emb[i], emb[keep_idx])
            if float(sims.max()) < C.DEDUP_COSINE_THRESHOLD:
                keep_idx.append(i)
        kept.extend(group[i] for i in keep_idx)
    return kept


# ---- decontamination (best-effort) --------------------------------------------------

def _decontaminate(recs: list[dict]) -> list[dict]:
    ng_path = C.DATA_SFT_DIR / "eval_ngrams.json"
    grams: set[str] = set()
    if ng_path.exists():
        grams = set(json.load(open(ng_path, encoding="utf-8")))
    else:
        try:
            import sys
            sys.path.insert(0, str(C.REPO_ROOT))
            import pipeline  # reuse pretraining decontam machinery
            grams = pipeline._build_contamination_ngrams()
            json.dump(sorted(grams), open(ng_path, "w", encoding="utf-8"))
        except Exception as e:  # offline / unavailable -> skip, corpus already decontaminated
            print(f"  [decontam] skipped ({str(e)[:80]}); corpus was pre-decontaminated", flush=True)
            return recs
    if not grams:
        return recs
    import sys
    sys.path.insert(0, str(C.REPO_ROOT))
    from dedup import word_ngrams, words
    out = []
    dropped = 0
    for r in recs:
        text = f"{r.get('question','')} {r['answer']}"
        if word_ngrams(words(text), C.DECONTAM_NGRAM) & grams:
            dropped += 1
        else:
            out.append(r)
    print(f"  [decontam] dropped {dropped} contaminated pairs", flush=True)
    return out


# ---- balance ------------------------------------------------------------------------

def _balance(recs: list[dict], rng: random.Random) -> list[dict]:
    total = len(recs)
    target_total = ((max((r.get("day", 1) for r in recs), default=1)) * C.PAIRS_PER_DAY)
    target_total = min(total, target_total)
    by_task = defaultdict(list)
    for r in recs:
        by_task[r["task"]].append(r)
    out = []
    for task, frac in C.TASK_MIX.items():
        want = round(target_total * frac)
        group = by_task.get(task, [])
        rng.shuffle(group)
        out.extend(group[:want])
    rng.shuffle(out)
    out.sort(key=lambda r: r.get("day", 1))     # preserve day order for the scaling curve
    return out


# ---- main ---------------------------------------------------------------------------

def build() -> None:
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(str(C.TOKENIZER_DIR))
    tokenizer.chat_template = C.CHAT_TEMPLATE
    rng = random.Random(C.SEED)

    raw = [json.loads(l) for l in open(C.RAW_JSONL, encoding="utf-8")]
    print(f"raw pairs: {len(raw)}")

    # 1) format + grounding
    recs = [r for r in raw if _format_ok(r)]
    print(f"after format: {len(recs)}")
    recs = [r for r in recs if _grounded(r)]
    print(f"after grounding: {len(recs)}")

    # 2) exact-hash dedup
    seen, deduped = set(), []
    for r in recs:
        k = _dedup_key(r)
        if k not in seen:
            seen.add(k); deduped.append(r)
    print(f"after exact dedup: {len(deduped)}")

    # 3) embedding dedup
    deduped = _embedding_dedup(deduped)
    print(f"after embedding dedup: {len(deduped)}")

    # 4) decontaminate
    deduped = _decontaminate(deduped)
    print(f"after decontam: {len(deduped)}")

    # 5) fixed eval holdout at the CHUNK level (build once, then frozen) — BEFORE balancing,
    #    so quarantining eval chunks (anti-leakage) does not skew the train task mix.
    eval_chunks_path = C.DATA_SFT_DIR / "eval_chunks.json"
    if not C.EVAL_JSONL.exists():
        _build_eval(deduped, rng, tokenizer, eval_chunks_path)
    eval_chunks = set(json.load(open(eval_chunks_path, encoding="utf-8")))
    train_pool = [r for r in deduped if r["chunk_id"] not in eval_chunks]
    print(f"train pool after eval quarantine ({len(eval_chunks)} chunks): {len(train_pool)}")

    # 6) balance to task mix (cumulative target = days * 1000)
    balanced = _balance(train_pool, rng)
    print(f"after balance: {len(balanced)}")

    # 7) assemble chat + context-fit filter
    train = []
    for r in balanced:
        rec = _assemble(r, rng)
        if _fits_context(rec, tokenizer):
            train.append(rec)
    print(f"after context-fit: {len(train)}")

    with open(C.PAIRS_JSONL, "w", encoding="utf-8") as f:
        for rec in train:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"\nTRAIN pairs.jsonl: {len(train)}")
    print("  task:", dict(Counter(r["meta"]["task"] for r in train)))
    print("  mode:", dict(Counter(r["meta"]["mode"] for r in train)))
    print("  source:", dict(Counter(r["meta"]["source"] for r in train)))
    print("  by day:", dict(Counter(r["meta"]["day"] for r in train)))


def _build_eval(pool: list[dict], rng: random.Random, tokenizer, eval_chunks_path: Path) -> None:
    """Hold out a fixed, task-stratified eval set — at most ONE pair per chunk, and quarantine
    each selected chunk entirely so no sibling pair leaks into training."""
    day1 = [r for r in pool if r.get("day", 1) == 1] or pool
    rng.shuffle(day1)
    want = {t: round(C.EVAL_SIZE * f) for t, f in C.TASK_MIX.items()}
    picked: list[dict] = []
    used_chunks: set[str] = set()
    got = Counter()
    for r in day1:
        t = r["task"]
        if got[t] >= want.get(t, 0) or r["chunk_id"] in used_chunks:
            continue
        rec = _assemble(r, rng)
        if not _fits_context(rec, tokenizer):
            continue
        picked.append(rec)
        used_chunks.add(r["chunk_id"])
        got[t] += 1
        if len(picked) >= C.EVAL_SIZE:
            break
    with open(C.EVAL_JSONL, "w", encoding="utf-8") as f:
        for rec in picked:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    json.dump(sorted(used_chunks), open(eval_chunks_path, "w", encoding="utf-8"))
    judge = [r for r in picked if r["meta"]["task"] == "qa"
             and r["messages"][2]["content"] != NOT_STATED][:C.JUDGE_QUESTION_COUNT]
    with open(C.JUDGE_QUESTIONS_JSONL, "w", encoding="utf-8") as f:
        for rec in judge:
            f.write(json.dumps({"question": rec["messages"][1]["content"],
                                "reference": rec["messages"][2]["content"],
                                "system": rec["messages"][0]["content"],
                                "mode": rec["meta"]["mode"]}, ensure_ascii=False) + "\n")
    print(f"  built FIXED eval set: {len(picked)} pairs ({dict(got)}), {len(judge)} judge questions")


if __name__ == "__main__":
    build()
