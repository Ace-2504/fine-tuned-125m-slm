"""Modal entrypoint for SLM-125M SFT (Phase 4) — one training run per study "day".

Reads everything from the authorized `slm-125m` volume:
  /data/checkpoints/base/ckpt.pt   base weights (init each run)
  /data/sft/{pairs,eval,judge_questions}.jsonl   uploaded before the run
  /data/tokens/val/*.bin           pretraining val bins (retention / "data loss" eval)
  /data/tokenizer                  tokenizer (chat_template applied at runtime)
Writes the SFT checkpoint to /data/checkpoints/sft/day-<N>/ and returns the full metrics
dict to the local entrypoint, which saves it for make_report.py.

Run:
    modal run modal_sft.py --day 1
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import modal

import sft_config as C   # also puts REPO_ROOT on sys.path so config/train_core resolve

app = modal.App(C.MODAL_APP)
volume = modal.Volume.from_name(C.MODAL_VOLUME)

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("torch==2.4.1", "transformers==4.46.3", "tokenizers==0.20.3", "numpy>=1.26,<2.0")
    .add_local_python_source("config", "train_core", "sft_config", "sft_data",
                             "sft_train_core", "prompts")
)


@app.function(image=image, gpu=C.MODAL_GPU, volumes={"/data": volume}, timeout=C.MODAL_TIMEOUT_S)
def train(day: int, epochs: int) -> dict:
    import sft_train_core

    t0 = time.time()
    volume.reload()
    r = sft_train_core.run_sft(
        base_ckpt="/data/checkpoints/base/ckpt.pt",
        pairs_path="/data/sft/pairs.jsonl",
        eval_path="/data/sft/eval.jsonl",
        judge_path="/data/sft/judge_questions.jsonl",
        out_dir=f"/data/checkpoints/sft/day-{day}",
        tokenizer_dir="/data/tokenizer",
        data_root="/data",
        day=day,
        epochs=epochs,
    )
    volume.commit()
    r["container_wall_s"] = round(time.time() - t0, 1)
    r["modal_gpu"] = C.MODAL_GPU
    return r


@app.local_entrypoint()
def main(day: int = 1, epochs: int = -1):
    # epochs=-1 -> use config default (C.EPOCHS); day 0 is the base "before" baseline (epochs 0)
    ep = C.EPOCHS if epochs < 0 else epochs
    if day == 0:
        ep = 0
    r = train.remote(day, ep)
    C.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = C.REPORTS_DIR / f"run-{day:02d}.metrics.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(r, f, indent=2)
    print(f"\nsaved metrics -> {out}")
    print(f"  device {r['device']} ({r.get('gpu')}) | {r['train_examples']} ex | "
          f"{r['total_steps']} steps | train_wall {r['train_wall_s']}s")
    print(f"  SFT-eval ppl {r['sft_eval_perplexity']} | retention ppl "
          f"{r['retention_perplexity']} (base {r['base_retention_perplexity']})")
    print("Next: python make_report.py --day", day)
