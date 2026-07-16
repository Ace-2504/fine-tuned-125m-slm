"""Daily QnA generator for the SLM-125M SFT scaling study (Phase 3).

Each run generates ~1,000-pairs-worth of RAW teacher output for one "day" of the study and
appends it to data/sft/raw.jsonl. Filtering/dedup/balancing happens later in build_dataset.py.

Design:
- QA task: 1 call per chunk -> 5 grounded QA pairs; each pair assembled as closed_book (Q->A)
  or, for ~20%, raft (context+Q->A). Teaches knowledge into weights + answer-from-context.
- summarize / extract / rewrite: BATCHED (5 passages per call) to fit the 500 RPD budget;
  passage lives in the user turn (context mode).
- refusal: batched on-topic-but-unanswerable questions -> answer "not stated in the context".

Resilience: paced under RPM, backoff on blips, clean exit + resume on the daily wall (RPD).
Idempotent by content-hash chunk_id (persisted), so chunks are never reused across days.

Usage:
    python gen_qa.py                 # next day (auto-increment)
    python gen_qa.py --day 1
    python gen_qa.py --smoke 3       # tiny validation run (does not advance the day counter)
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path

import sft_config as C
import prompts
from chunker import Chunk, domain_targets, load_tokenizer, sample_chunks
from teacher import RPDExhausted, TeacherClient

GEN_BATCH = 5                      # passages per aux/refusal call
NOT_STATED = prompts.NOT_STATED


# ---- persisted state ----------------------------------------------------------------

def _load_json(path: Path, default):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def _save_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    tmp.replace(path)


# ---- teacher schemas ----------------------------------------------------------------

def _schemas():
    from google.genai import types
    qa = types.Schema(type=types.Type.ARRAY, items=types.Schema(
        type=types.Type.OBJECT,
        properties={"question": types.Schema(type=types.Type.STRING),
                    "answer": types.Schema(type=types.Type.STRING),
                    "difficulty": types.Schema(type=types.Type.STRING,
                                               enum=["easy", "medium", "hard"])},
        required=["question", "answer", "difficulty"]))
    batch_ans = types.Schema(type=types.Type.ARRAY, items=types.Schema(
        type=types.Type.OBJECT,
        properties={"index": types.Schema(type=types.Type.INTEGER),
                    "answer": types.Schema(type=types.Type.STRING)},
        required=["index", "answer"]))
    batch_q = types.Schema(type=types.Type.ARRAY, items=types.Schema(
        type=types.Type.OBJECT,
        properties={"index": types.Schema(type=types.Type.INTEGER),
                    "question": types.Schema(type=types.Type.STRING)},
        required=["index", "question"]))
    return qa, batch_ans, batch_q


# ---- per-day plan (derived from config composition) ---------------------------------

def plan(smoke: int | None) -> dict:
    if smoke:
        return {"qa": smoke, "summarize": 1, "extract": 1, "rewrite": 1, "refusal": 1}
    raw = C.PAIRS_PER_DAY / C.ASSUMED_KEEP_RATE
    return {
        "qa": math.ceil(raw * C.TASK_MIX["qa"] / C.QA_PER_CHUNK),
        "summarize": math.ceil(raw * C.TASK_MIX["summarize"] / GEN_BATCH),
        "extract": math.ceil(raw * C.TASK_MIX["extract"] / GEN_BATCH),
        "rewrite": math.ceil(raw * C.TASK_MIX["rewrite"] / GEN_BATCH),
        "refusal": 10,
    }


def _append_raw(fh, rec: dict) -> None:
    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    fh.flush()


def _existing_call_counts(day: int) -> dict:
    """Calls already completed for `day` (from raw.jsonl) -> lets a resumed run top up only
    the remainder instead of re-generating a full day after an RPD wall."""
    done = {"qa": 0, "summarize": 0, "extract": 0, "rewrite": 0, "refusal": 0}
    if not C.RAW_JSONL.exists():
        return done
    pairs = {k: 0 for k in done}
    with open(C.RAW_JSONL, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("day") != day:
                continue
            cat = ("refusal" if (r["task"] == "qa" and r["answer"] == NOT_STATED)
                   else r["task"])
            pairs[cat] = pairs.get(cat, 0) + 1
    # every call yields ~5 pairs (QA_PER_CHUNK for qa; GEN_BATCH passages for aux/refusal)
    for k in done:
        done[k] = pairs[k] // 5
    return done


def run(day: int, smoke: int | None) -> None:
    rng = random.Random(C.SEED + day)
    tokenizer = load_tokenizer()
    teacher = TeacherClient()
    qa_schema, batch_ans_schema, batch_q_schema = _schemas()

    full = plan(smoke)
    if smoke:
        calls = full
    else:
        done = _existing_call_counts(day)
        calls = {k: max(0, full[k] - done.get(k, 0)) for k in full}
        if any(done.values()):
            print(f"resuming day {day}: already done {done} calls; remaining {calls}", flush=True)
    # chunks needed: qa(1 each) + aux/refusal (GEN_BATCH each)
    n_chunks = calls["qa"] + GEN_BATCH * (calls["summarize"] + calls["extract"]
                                          + calls["rewrite"] + calls["refusal"])
    print(f"day {day}: calls={calls} (~{sum(calls.values())} requests), "
          f"sampling {n_chunks} chunks", flush=True)

    used = set(_load_json(C.CHUNKS_USED_PATH, []))
    pool = sample_chunks(domain_targets(n_chunks), used, rng, tokenizer)
    _save_json(C.CHUNKS_USED_PATH, sorted(used))
    if len(pool) < n_chunks:
        print(f"  note: sampled {len(pool)}/{n_chunks} chunks", flush=True)

    # partition the shuffled pool into task groups
    it = iter(pool)
    def take(k): return [c for _, c in zip(range(k), it)]
    qa_chunks = take(calls["qa"])
    sum_chunks = take(GEN_BATCH * calls["summarize"])
    ext_chunks = take(GEN_BATCH * calls["extract"])
    rew_chunks = take(GEN_BATCH * calls["rewrite"])
    ref_chunks = take(GEN_BATCH * calls["refusal"])

    C.DATA_SFT_DIR.mkdir(parents=True, exist_ok=True)
    kept = {"qa": 0, "summarize": 0, "extract": 0, "rewrite": 0, "refusal": 0}
    started = time.time()
    hit_wall = False

    with open(C.RAW_JSONL, "a", encoding="utf-8") as fh:
        try:
            # --- QA (1 call/chunk -> 5 pairs) ---
            for qi, ch in enumerate(qa_chunks):
                if qi and qi % 25 == 0:
                    print(f"  qa {qi}/{len(qa_chunks)} | {teacher.usage.requests} reqs | "
                          f"{int(time.time()-started)}s", flush=True)
                pairs = teacher.generate_json(prompts.qa_answerable(ch.text, C.QA_PER_CHUNK),
                                              qa_schema)
                for p in pairs or []:
                    mode = "raft" if rng.random() < C.MODE_MIX["raft"] else "closed_book"
                    if mode == "closed_book" and ch.source not in C.CLOSED_BOOK_SOURCES:
                        mode = "raft"      # closed-book only allowed from general-knowledge sources
                    _append_raw(fh, _rec(ch, "qa", mode, p.get("question", ""),
                                         p.get("answer", ""), p.get("difficulty", "medium"), day))
                    kept["qa"] += 1

            # --- batched context tasks ---
            for task, chunks in (("summarize", sum_chunks), ("extract", ext_chunks),
                                 ("rewrite", rew_chunks)):
                print(f"  {task}: {len(chunks)} passages | {teacher.usage.requests} reqs | "
                      f"{int(time.time()-started)}s", flush=True)
                for batch in _batches(chunks, GEN_BATCH):
                    outs = teacher.generate_json(
                        prompts.task_output_batch(task, [c.text for c in batch]),
                        batch_ans_schema)
                    for o in outs or []:
                        i = int(o.get("index", -1))
                        if 0 <= i < len(batch):
                            _append_raw(fh, _rec(batch[i], task, "context", "",
                                                 o.get("answer", ""), "medium", day))
                            kept[task] += 1

            # --- batched refusals ---
            for batch in _batches(ref_chunks, GEN_BATCH):
                outs = teacher.generate_json(
                    prompts.qa_unanswerable_batch([c.text for c in batch]), batch_q_schema)
                for o in outs or []:
                    i = int(o.get("index", -1))
                    if 0 <= i < len(batch):
                        _append_raw(fh, _rec(batch[i], "qa", "raft", o.get("question", ""),
                                             NOT_STATED, "hard", day))
                        kept["refusal"] += 1
        except RPDExhausted as e:
            hit_wall = True
            print(f"  RPD wall hit: {e} — saving progress, resume tomorrow.", flush=True)
        except KeyboardInterrupt:
            print("  interrupted — progress saved.", flush=True)

    stats = {
        "day": day, "smoke": bool(smoke), "teacher": teacher.model,
        "planned_calls": calls, "raw_pairs": kept, "raw_total": sum(kept.values()),
        "requests": teacher.usage.requests, "retries": teacher.usage.retries,
        "in_tokens": teacher.usage.in_tokens, "out_tokens": teacher.usage.out_tokens,
        "wall_s": round(time.time() - started, 1), "rpd_wall": hit_wall,
    }
    gen_state = _load_json(C.GEN_STATE_PATH, {"last_day": 0, "days": {}})
    if not smoke:
        gen_state["last_day"] = max(gen_state.get("last_day", 0), day)
    gen_state.setdefault("days", {})[str(day) if not smoke else "smoke"] = stats
    _save_json(C.GEN_STATE_PATH, gen_state)

    print(f"\nday {day} done: {stats['raw_total']} raw pairs {kept} | "
          f"{stats['requests']} requests, {stats['retries']} retries | "
          f"tok in/out {stats['in_tokens']}/{stats['out_tokens']} | {stats['wall_s']}s"
          f"{' | RPD WALL' if hit_wall else ''}", flush=True)


def _rec(ch: Chunk, task: str, mode: str, q: str, a: str, difficulty: str, day: int) -> dict:
    return {"chunk_id": ch.chunk_id, "source": ch.source, "task": task, "mode": mode,
            "difficulty": difficulty, "question": (q or "").strip(), "answer": (a or "").strip(),
            "passage": ch.text, "passage_tokens": ch.token_len, "day": day, "teacher": C.TEACHER_MODEL}


def _batches(seq, n):
    for i in range(0, len(seq), n):
        b = seq[i:i + n]
        if b:
            yield b


def main() -> None:
    ap = argparse.ArgumentParser(description="Daily QnA generator (SFT scaling study)")
    ap.add_argument("--day", type=int, default=None, help="day index; default = last+1")
    ap.add_argument("--smoke", type=int, default=None, help="tiny run: N qa calls, 1 of each aux")
    args = ap.parse_args()
    gen_state = _load_json(C.GEN_STATE_PATH, {"last_day": 0, "days": {}})
    day = args.day if args.day is not None else (0 if args.smoke else gen_state.get("last_day", 0) + 1)
    run(day, args.smoke)


if __name__ == "__main__":
    main()
