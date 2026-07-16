"""Per-run report generator (Phase 4, required after every training run).

Reads reports/run-<NN>.metrics.json (returned by modal_sft), scores the judge answers with
Gemini, computes the data-loss / catastrophic-forgetting analysis and the perplexity
comparison vs the previous checkpoint (vs the base model for the first run), and writes a
self-contained reports/run-<NN>.md (human) + reports/run-<NN>.json (machine).

    python make_report.py --day 1
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import sft_config as C

L4_USD_PER_HR = 0.80


def _load(path: Path):
    return json.load(open(path, encoding="utf-8")) if path.exists() else None


def _judge_scores(items: list[dict]) -> dict:
    """Score each model answer 1-5 with Gemini vs the reference. Batched. Best-effort."""
    if not items:
        return {}
    try:
        from teacher import TeacherClient
        from google.genai import types
        tc = TeacherClient()
        schema = types.Schema(type=types.Type.ARRAY, items=types.Schema(
            type=types.Type.OBJECT,
            properties={"index": types.Schema(type=types.Type.INTEGER),
                        "score": types.Schema(type=types.Type.INTEGER),
                        "reason": types.Schema(type=types.Type.STRING)},
            required=["index", "score"]))
        scores, reasons = [], []
        for start in range(0, len(items), 10):
            batch = items[start:start + 10]
            blocks = "\n\n".join(
                f"[{i}] QUESTION: {b['question']}\nREFERENCE: {b['reference']}\nANSWER: {b['answer']}"
                for i, b in enumerate(batch))
            prompt = ("Score each ANSWER to its QUESTION on a 1-5 scale for correctness and "
                      "helpfulness given the REFERENCE (5=fully correct & helpful, 1=wrong/empty). "
                      f"Return a JSON array of {len(batch)} objects with 'index', 'score', 'reason'.\n\n"
                      + blocks)
            out = tc.generate_json(prompt, schema, temperature=0.0)
            by_i = {int(o["index"]): o for o in out}
            for i in range(len(batch)):
                o = by_i.get(i, {})
                scores.append(int(o.get("score", 0)))
                reasons.append(o.get("reason", ""))
        valid = [s for s in scores if s > 0]
        by_mode: dict[str, list[int]] = {}
        for it, s in zip(items, scores):
            if s > 0:
                by_mode.setdefault(it.get("mode") or "?", []).append(s)
        by_mode = {m: round(sum(v) / len(v), 2) for m, v in by_mode.items()}
        return {"mean": round(sum(valid) / len(valid), 2) if valid else None,
                "n": len(valid), "by_mode": by_mode, "scores": scores, "reasons": reasons}
    except Exception as e:  # offline / RPD — report can still be produced
        return {"error": str(e)[:120]}


def _dataset_stats() -> dict:
    if not C.PAIRS_JSONL.exists():
        return {}
    metas = [json.loads(l)["meta"] for l in open(C.PAIRS_JSONL, encoding="utf-8")]
    return {"total": len(metas),
            "task": dict(Counter(m["task"] for m in metas)),
            "mode": dict(Counter(m["mode"] for m in metas)),
            "source": dict(Counter(m["source"] for m in metas)),
            "by_day": dict(Counter(m["day"] for m in metas))}


def _delta(cur: float, ref: float) -> str:
    d = cur - ref
    pct = 100 * d / ref if ref else 0.0
    arrow = "↑" if d > 0 else ("↓" if d < 0 else "→")
    return f"{cur:.3f} ({arrow} {d:+.3f}, {pct:+.1f}%)"


def build(day: int) -> None:
    m = _load(C.REPORTS_DIR / f"run-{day:02d}.metrics.json")
    if m is None:
        raise SystemExit(f"metrics not found: run-{day:02d}.metrics.json — run modal_sft first")
    prev = _load(C.REPORTS_DIR / f"run-{day-1:02d}.json")
    ds = _dataset_stats()
    gen = _load(C.GEN_STATE_PATH) or {}
    gen_day = (gen.get("days", {}) or {}).get(str(day), {})

    judge = _judge_scores(m.get("judge", []))
    base_ret = C.BASE_VAL_PERPLEXITY
    ret_ppl = m["retention_perplexity"]
    sft_ppl = m["sft_eval_perplexity"]
    prev_ret = prev.get("retention_perplexity") if prev else base_ret
    prev_sft = prev.get("sft_eval_perplexity") if prev else None
    prev_label = f"run-{day-1:02d}" if prev else "base model"

    cost = round(m.get("container_wall_s", m.get("total_wall_s", 0)) / 3600 * L4_USD_PER_HR, 3)
    forget_pct = 100 * (ret_ppl - base_ret) / base_ret
    verdict = ("negligible" if abs(forget_pct) < 3 else
               "mild" if forget_pct < 10 else "notable" if forget_pct < 25 else "severe")

    machine = {
        "day": day, "baseline": m.get("baseline", False),
        "sft_eval_perplexity": sft_ppl, "retention_perplexity": ret_ppl,
        "base_retention_perplexity": base_ret,
        "forgetting_pct_vs_base": round(forget_pct, 2), "forgetting_verdict": verdict,
        "judge_mean": judge.get("mean"), "judge_by_mode": judge.get("by_mode"),
        "cost_usd": cost, "metrics": m, "dataset": ds,
    }
    with open(C.REPORTS_DIR / f"run-{day:02d}.json", "w", encoding="utf-8") as f:
        json.dump(machine, f, indent=2)

    md = _render_md(day, m, ds, gen_day, judge, base_ret, ret_ppl, sft_ppl,
                    prev_ret, prev_sft, prev_label, cost, forget_pct, verdict)
    (C.REPORTS_DIR / f"run-{day:02d}.md").write_text(md, encoding="utf-8")
    print(f"wrote reports/run-{day:02d}.md and run-{day:02d}.json")
    print(f"  SFT-eval ppl {sft_ppl} | retention ppl {ret_ppl} vs base {base_ret} "
          f"({forget_pct:+.1f}% forgetting: {verdict}) | judge {judge.get('mean')} | ${cost}")


def _render_md(day, m, ds, gen_day, judge, base_ret, ret_ppl, sft_ppl,
               prev_ret, prev_sft, prev_label, cost, forget_pct, verdict) -> str:
    kind = "BASELINE (base model, no training)" if m.get("baseline") else "SFT run"
    lines = [f"# SFT Run Report — Day {day} ({kind})", ""]

    lines += ["## 1. Run identity", "",
              f"- Day / dataset scale: **{day}** · train examples: **{m['train_examples']}**",
              f"- GPU: **{m.get('gpu')}** (Modal {m.get('modal_gpu','?')}) · device {m['device']}",
              f"- Base checkpoint: `Ace-2504/slm-125m-base` (volume `slm-125m`)", ""]

    lines += ["## 2. Parameters", "",
              f"- Model: 12L/768d/12h, 125.8M params, ctx {C.MAX_SEQ_LEN}, tied embeddings",
              f"- Fine-tune: **full FT** · epochs **{m['epochs']}** · batch **{m['batch_size']}** · "
              f"steps **{m['total_steps']}** (warmup {m['warmup_steps']})",
              f"- LR {m['lr_peak']:g} → {m['lr_min']:g} cosine · wd {m['weight_decay']} · seed {m['seed']}",
              f"- Loss: assistant-only masking · chat template with `<|user|>/<|assistant|>/<|system|>`",
              f"- Teacher (data): `{C.TEACHER_MODEL}`", ""]

    if ds:
        lines += ["## 3. Dataset composition", "",
                  f"- Train pairs: **{ds['total']}** · by day: {ds['by_day']}",
                  f"- Task: {ds['task']}", f"- Mode: {ds['mode']}", f"- Domain: {ds['source']}"]
        if gen_day:
            lines += [f"- Generation (day {day}): {gen_day.get('requests','?')} requests, "
                      f"{gen_day.get('raw_total','?')} raw pairs, "
                      f"tok in/out {gen_day.get('in_tokens','?')}/{gen_day.get('out_tokens','?')}, $0 (free tier)"]
        lines += [""]

    lines += ["## 4. Data loss / catastrophic forgetting", "",
              f"Retention perplexity on the **pretraining val set** (base = **{base_ret}**):", "",
              f"- This run: **{ret_ppl:.3f}** → vs base: **{forget_pct:+.1f}%** ({verdict} forgetting)",
              f"- vs previous ({prev_label}): {_delta(ret_ppl, prev_ret)}",
              "", f"> A retention-ppl rise is partly expected (chat-distribution shift); "
              f"this run's forgetting is **{verdict}**.", ""]

    lines += ["## 5. Perplexity comparison (vs previous checkpoint)", "",
              f"| Metric | This run (day {day}) | Previous ({prev_label}) | Δ |",
              "| --- | --- | --- | --- |",
              f"| SFT-eval perplexity | {sft_ppl:.3f} | "
              f"{prev_sft if prev_sft is not None else '—'} | "
              f"{('%.3f' % (sft_ppl - prev_sft)) if prev_sft is not None else 'first run'} |",
              f"| Retention perplexity | {ret_ppl:.3f} | {prev_ret:.3f} | {ret_ppl - prev_ret:+.3f} |",
              "", "(SFT-eval ↓ = better task fit; retention ↑ = more forgetting.)", ""]

    jm = judge.get("mean")
    lines += ["## 6. Task quality", "",
              f"- SFT-eval loss: **{m['sft_eval_loss']}** (ppl {sft_ppl})",
              f"- Final train loss: {m.get('final_train_loss')}",
              f"- **Gemini-judge score: {jm if jm is not None else judge.get('error','n/a')}/5** "
              f"(n={judge.get('n','?')})",
              f"- **Judge by mode:** {judge.get('by_mode') or 'n/a'} "
              f"(grounded=raft/context vs closed_book=recall)",
              "", "**Fixed sample generations:**", ""]
    for s in m.get("samples", []):
        lines += [f"- *Q:* {s['prompt']}", f"  *A:* {s['answer'][:300]}"]
    lines += [""]

    lines += ["## 7. Modal runtime", "",
              f"- Train wall: **{m['train_wall_s']}s** · total wall: {m['total_wall_s']}s · "
              f"container: {m.get('container_wall_s','?')}s",
              f"- Peak GPU mem: **{m['peak_gpu_mem_gb']} GB** · throughput: {m['tokens_per_sec']} "
              f"supervised tok/s · supervised tokens: {m['supervised_tokens']:,}",
              f"- **Cost: ~${cost}** (L4 @ ${L4_USD_PER_HR}/hr) · teacher $0 (free tier)", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", type=int, required=True)
    args = ap.parse_args()
    build(args.day)
