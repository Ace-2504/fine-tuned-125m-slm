"""Export an SFT checkpoint from the Modal volume to a Hugging Face model repo.

Converts /data/checkpoints/sft/day-<N>/ckpt.pt into HF format (safetensors + tokenizer WITH the
chat template + a generation_config that includes the decoding fix) and pushes it to a branch.

Both study checkpoints are published to one repo as revisions:
    main    -> day 2  (the best model: same judge as day 10, half the forgetting)
    day-10  -> day 10 (the study endpoint, for comparison — demonstrably degraded)

    modal run export_sft_hf.py --day 2  --revision main
    modal run export_sft_hf.py --day 10 --revision day-10

The HF token is read from the local login and passed over Modal's encrypted channel; it is never
stored as a named secret or printed.
"""

from __future__ import annotations

import modal

import sft_config as C

app = modal.App("slm-125m-sft-export")
volume = modal.Volume.from_name(C.MODAL_VOLUME)

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("torch==2.4.1", "transformers==4.46.3", "tokenizers==0.20.3",
                 "numpy>=1.26,<2.0", "huggingface_hub>=0.24")
    .env({"SFT_TRACK": C.TRACK})
    .add_local_python_source("config", "train_core", "sft_config", "sft_data", "prompts")
)

CARD = """---
license: mit
library_name: transformers
pipeline_tag: text-generation
base_model: Ace-2504/slm-125m-base
tags:
  - llama
  - legal
  - sft
  - small-language-model
  - research
---

# SLM-125M — SFT data-scaling study

Supervised fine-tunes of [Ace-2504/slm-125m-base](https://huggingface.co/Ace-2504/slm-125m-base)
(125.8M params, 1024 ctx, pretrained from scratch on 2.04B tokens of US case law, SEC filings and
educational web text).

**This repo is a research artifact, not a useful assistant.** It is the output of a ten-round
data-scaling study whose headline result is a **negative** one: scaling SFT data 10× did **not**
improve answer quality (judge flat at ~1.5/5) and **tripled catastrophic forgetting**.

📊 **Full write-up:** https://ace-2504.github.io/fine-tuned-125m-slm/
· 💻 **Code:** https://github.com/Ace-2504/fine-tuned-125m-slm

## Two revisions — pick deliberately

| Revision | Data | Judge /5 | Forgetting vs base | Notes |
| --- | --- | --- | --- | --- |
| **`main`** | 2,000 pairs | **1.50** | **+9.5%** | **The better model.** Recommended. |
| `day-10` | 10,000 pairs | 1.54 | +16.3% | Study endpoint. 5× the data, **no quality gain**, ~2× the forgetting, and a *regressed* probe answer. |

The two judge scores are **identical within the measured ±0.07 noise band**, so `main` (day 2)
strictly dominates: same quality, half the damage, one-fifth the data.

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

# the better model (day 2)
tok = AutoTokenizer.from_pretrained("Ace-2504/fine-tuned-125m-slm")
model = AutoModelForCausalLM.from_pretrained("Ace-2504/fine-tuned-125m-slm")

# the 10k endpoint, for comparison
tok10 = AutoTokenizer.from_pretrained("Ace-2504/fine-tuned-125m-slm", revision="day-10")
model10 = AutoModelForCausalLM.from_pretrained("Ace-2504/fine-tuned-125m-slm", revision="day-10")

msgs = [
    {"role": "system", "content": "You are a precise legal and financial assistant."},
    {"role": "user", "content": "What is the standard of proof in a civil lawsuit?"},
]
ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt")
print(tok.decode(model.generate(ids, max_new_tokens=120)[0][ids.shape[1]:], skip_special_tokens=True))
```

## Honest limitations

- **Answer quality is poor (~1.5/5).** It learned the *shape* of an assistant turn, not reliable
  answers. Expect repetition, prompt echoing, and confident wrong answers.
- **It forgot part of its pretraining.** Perplexity on the original pretraining validation set rose
  from 11.35 → 12.42 (`main`) / 13.20 (`day-10`).
- **Root cause:** ~40% of training was *closed-book* QA — recalling a document fact from a single
  exposure, which a 125M model cannot do. Common facts land; long-tail specifics never do.
- Do not use for legal or financial advice. It is a study artifact.

## Training

Full fine-tune (no LoRA), 3 epochs, batch 16, LR 3e-5→3e-6 cosine, AdamW, bf16, **assistant-only loss
masking**, seed 1337, on a single Modal L4. Data: QnA written by `gemini-3.1-flash-lite`, grounded in
passages from the same corpus the base was pretrained on, then filtered, deduplicated (exact +
embedding), decontaminated and balanced. Chat template uses `<|system|>` / `<|user|>` / `<|assistant|>`.

`generation_config` ships with `repetition_penalty=1.3` and `no_repeat_ngram_size=3` — without them
greedy decoding falls into repetition loops.
"""


@app.function(image=image, volumes={"/data": volume}, timeout=60 * 30)
def export(hf_token: str, repo_id: str, day: int, revision: str) -> str:
    import torch
    from transformers import AutoTokenizer, GenerationConfig
    from huggingface_hub import create_branch, create_repo, upload_folder

    import sft_config as C
    import train_core

    volume.reload()
    out_dir = f"/tmp/export_day{day}"

    model = train_core._build_model("cpu", attn_implementation="sdpa")
    ckpt = torch.load(f"/data/checkpoints/sft/day-{day}/ckpt.pt", map_location="cpu")
    model.load_state_dict(ckpt["model"])
    model = model.to(torch.float32)
    model.eval()

    # Decoding fix baked in — greedy without these loops badly on this model.
    model.generation_config = GenerationConfig(
        do_sample=True, temperature=0.7, top_p=0.9, top_k=50, max_new_tokens=160,
        repetition_penalty=1.3, no_repeat_ngram_size=3,
        bos_token_id=0, eos_token_id=1, pad_token_id=2,
    )
    model.save_pretrained(out_dir, safe_serialization=True)

    tok = AutoTokenizer.from_pretrained("/data/tokenizer")
    tok.chat_template = C.CHAT_TEMPLATE
    tok.save_pretrained(out_dir)

    with open(f"{out_dir}/README.md", "w", encoding="utf-8") as f:
        f.write(CARD)

    create_repo(repo_id, token=hf_token, repo_type="model", exist_ok=True)
    if revision != "main":
        create_branch(repo_id, branch=revision, token=hf_token, exist_ok=True)
    upload_folder(folder_path=out_dir, repo_id=repo_id, revision=revision, token=hf_token,
                  commit_message=f"SFT day-{day} ({ckpt.get('train_examples','?')} pairs)")
    return (f"pushed day-{day} -> {repo_id}@{revision} "
            f"({ckpt.get('train_examples','?')} train pairs)")


@app.local_entrypoint()
def main(day: int = 2, revision: str = "main", repo_id: str = C.OUTPUT_HF_REPO):
    from huggingface_hub import HfFolder
    token = HfFolder.get_token()
    if not token:
        raise SystemExit("No local HF token — run `huggingface-cli login` first.")
    print(export.remote(token, repo_id, day, revision))
