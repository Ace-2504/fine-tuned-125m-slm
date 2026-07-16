"""SFT training engine for the SLM-125M scaling study (device-agnostic).

Loads the pretrained base weights, fine-tunes on a chat JSONL with assistant-only loss
masking (see sft_data.py), then evaluates:
  - SFT-eval loss/perplexity on the fixed held-out chat set (task learning), and
  - RETENTION perplexity on the original pretraining val bins (catastrophic forgetting /
    "data loss"), directly comparable to the base model's 11.35.
Also generates deterministic answers for the judge questions + fixed sample prompts so the
base->instruct shift and Gemini-judge scoring can be logged.

Reuses the pretraining `train_core` for the model builder and the packed-bin val loader.
"""

from __future__ import annotations

import json
import math
import random
import sys
import time
from pathlib import Path

import numpy as np

import sft_config as C
import sft_data

# pretraining engine (model builder + retention val loader) lives at REPO_ROOT
sys.path.insert(0, str(C.REPO_ROOT))
import train_core  # noqa: E402

FIXED_SAMPLE_PROMPTS = (
    "What is the standard of proof in a civil lawsuit?",
    "Summarize what a 10-K annual report contains.",
    "What does it mean for a contract clause to be severable?",
)


def _lr_at(step: int, total: int, warmup: int) -> float:
    if step < warmup:
        return C.LR * (step + 1) / max(1, warmup)
    prog = (step - warmup) / max(1, total - warmup)
    return C.MIN_LR + 0.5 * (1 + math.cos(math.pi * min(1.0, prog))) * (C.LR - C.MIN_LR)


def _load_base(model, base_ckpt: str, device: str) -> None:
    import torch
    ckpt = torch.load(base_ckpt, map_location=device)
    state = ckpt["model"] if "model" in ckpt else ckpt
    model.load_state_dict(state)


def _eval_sft_loss(model, dataset, pad_id: int, device: str) -> float:
    import torch
    model.eval()
    losses, i = [], 0
    with torch.no_grad():
        while i < len(dataset):
            batch = [dataset[j] for j in range(i, min(len(dataset), i + C.BATCH_SIZE))]
            input_ids, labels, attn = sft_data.collate(batch, pad_id)
            input_ids, labels, attn = input_ids.to(device), labels.to(device), attn.to(device)
            with torch.autocast(device_type=device, dtype=torch.bfloat16, enabled=device == "cuda"):
                loss = model(input_ids=input_ids, attention_mask=attn, labels=labels).loss
            losses.append(float(loss.detach().cpu()))
            i += C.BATCH_SIZE
    model.train()
    return float(np.mean(losses))


def _generate(model, tokenizer, prompts_msgs, device, max_new_tokens=120) -> list[str]:
    import torch
    model.eval()
    outs = []
    with torch.no_grad():
        for msgs in prompts_msgs:
            ids = tokenizer.apply_chat_template(msgs, add_generation_prompt=True,
                                                tokenize=True, return_tensors="pt").to(device)
            out = model.generate(ids, max_new_tokens=max_new_tokens, do_sample=False,
                                 no_repeat_ngram_size=C.GEN_NO_REPEAT_NGRAM or 0,
                                 repetition_penalty=C.GEN_REPETITION_PENALTY,
                                 pad_token_id=tokenizer.pad_token_id,
                                 eos_token_id=tokenizer.eos_token_id)
            outs.append(tokenizer.decode(out[0][ids.shape[1]:], skip_special_tokens=True).strip())
    model.train()
    return outs


def run_sft(*, base_ckpt: str, pairs_path: str, eval_path: str, judge_path: str,
            out_dir: str, tokenizer_dir: str, data_root: str, day: int,
            epochs: int | None = None) -> dict:
    import torch

    epochs = C.EPOCHS if epochs is None else epochs
    baseline = epochs == 0                       # day-0 "before" run: eval base, no training
    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(C.SEED); np.random.seed(C.SEED); random.seed(C.SEED)
    if device == "cuda":
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.cuda.reset_peak_memory_stats()

    tokenizer = sft_data.load_tokenizer(tokenizer_dir)
    pad_id = tokenizer.pad_token_id

    model = train_core._build_model(device, attn_implementation="sdpa")
    _load_base(model, base_ckpt, device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=C.LR, betas=(C.BETA1, C.BETA2),
                                  weight_decay=C.WEIGHT_DECAY, fused=(device == "cuda"))

    train_ds = sft_data.SFTDataset(pairs_path, tokenizer)
    steps_per_epoch = math.ceil(len(train_ds) / C.BATCH_SIZE)
    total_steps = steps_per_epoch * epochs
    warmup = max(1, int(total_steps * C.WARMUP_RATIO))
    print(f"day {day}{' (BASELINE)' if baseline else ''}: {len(train_ds)} train ex | "
          f"{epochs} epochs x {steps_per_epoch} steps = {total_steps} steps | "
          f"warmup {warmup} | device {device}", flush=True)

    metrics_steps = []
    started = time.time()
    supervised_tokens = 0
    model.train()
    step = 0
    for epoch in range(epochs):
        order = list(range(len(train_ds)))
        random.Random(C.SEED + epoch).shuffle(order)
        for s in range(steps_per_epoch):
            idx = order[s * C.BATCH_SIZE:(s + 1) * C.BATCH_SIZE]
            batch = [train_ds[j] for j in idx]
            input_ids, labels, attn = sft_data.collate(batch, pad_id)
            input_ids, labels, attn = input_ids.to(device), labels.to(device), attn.to(device)
            supervised_tokens += int((labels != sft_data.IGNORE).sum())

            lr = _lr_at(step, total_steps, warmup)
            for g in optimizer.param_groups:
                g["lr"] = lr
            with torch.autocast(device_type=device, dtype=torch.bfloat16, enabled=device == "cuda"):
                loss = model(input_ids=input_ids, attention_mask=attn, labels=labels).loss
            loss.backward()
            gnorm = torch.nn.utils.clip_grad_norm_(model.parameters(), C.GRAD_CLIP)
            optimizer.step()
            optimizer.zero_grad(set_to_none=True)
            step += 1
            if step % 10 == 0 or step == 1 or step == total_steps:
                row = {"step": step, "epoch": epoch, "lr": lr,
                       "train_loss": float(loss.detach().cpu()), "grad_norm": float(gnorm)}
                metrics_steps.append(row)
                print(json.dumps(row), flush=True)

    train_wall = time.time() - started

    # --- save checkpoint ---
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    torch.save({"model": model.state_dict(), "day": day, "sft": True,
                "train_examples": len(train_ds)}, out / "ckpt.pt")

    # --- eval: SFT loss/ppl + retention ppl ---
    eval_ds = sft_data.SFTDataset(eval_path, tokenizer)
    sft_loss = _eval_sft_loss(model, eval_ds, pad_id, device)
    val_data = train_core.BinWindowDataset(data_root, "val", C.MAX_SEQ_LEN)
    retention_loss = train_core.evaluate_loss(model, val_data, C.BATCH_SIZE, device,
                                              max_batches=C.RETENTION_EVAL_BATCHES)

    # --- generations: judge questions + fixed samples (deterministic/greedy) ---
    judge = [json.loads(l) for l in open(judge_path, encoding="utf-8")]
    judge_msgs = [[{"role": "system", "content": j["system"]},
                   {"role": "user", "content": j["question"]}] for j in judge]
    judge_answers = _generate(model, tokenizer, judge_msgs, device)
    sample_msgs = [[{"role": "system", "content": C.SYSTEM_PROMPTS[0]},
                    {"role": "user", "content": p}] for p in FIXED_SAMPLE_PROMPTS]
    sample_answers = _generate(model, tokenizer, sample_msgs, device)

    peak_mem_gb = (torch.cuda.max_memory_allocated() / 1e9) if device == "cuda" else 0.0
    total_wall = time.time() - started

    return {
        "day": day, "device": device,
        "gpu": (torch.cuda.get_device_name(0) if device == "cuda" else "cpu"),
        "train_examples": len(train_ds), "epochs": epochs, "baseline": baseline,
        "batch_size": C.BATCH_SIZE,
        "total_steps": total_steps, "warmup_steps": warmup,
        "lr_peak": C.LR, "lr_min": C.MIN_LR, "weight_decay": C.WEIGHT_DECAY, "seed": C.SEED,
        "supervised_tokens": supervised_tokens,
        "train_wall_s": round(train_wall, 1), "total_wall_s": round(total_wall, 1),
        "tokens_per_sec": round(supervised_tokens / max(1e-6, train_wall), 1),
        "peak_gpu_mem_gb": round(peak_mem_gb, 2),
        "final_train_loss": metrics_steps[-1]["train_loss"] if metrics_steps else None,
        "sft_eval_loss": round(sft_loss, 4),
        "sft_eval_perplexity": round(math.exp(min(20.0, sft_loss)), 4),
        "retention_loss": round(retention_loss, 4),
        "retention_perplexity": round(math.exp(min(20.0, retention_loss)), 4),
        "base_retention_perplexity": C.BASE_VAL_PERPLEXITY,
        "metrics_steps": metrics_steps,
        "judge": [{"question": j["question"], "reference": j["reference"], "answer": a,
                   "mode": j.get("mode", "")}
                  for j, a in zip(judge, judge_answers)],
        "samples": [{"prompt": p, "answer": a}
                    for p, a in zip(FIXED_SAMPLE_PROMPTS, sample_answers)],
    }
