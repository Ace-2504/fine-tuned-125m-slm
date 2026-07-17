---
title: SLM-125M — SFT Scaling Study (2k vs 10k)
emoji: ⚖️
colorFrom: blue
colorTo: gray
sdk: gradio
sdk_version: 4.44.1
app_file: app.py
pinned: false
license: mit
short_description: Ask two fine-tunes of a 125M model — did 5x more data help?
models:
  - Ace-2504/fine-tuned-125m-slm
  - Ace-2504/slm-125m-base
---

# SLM-125M — did 5× more fine-tuning data help?

Side-by-side demo of two supervised fine-tunes of
[Ace-2504/slm-125m-base](https://huggingface.co/Ace-2504/slm-125m-base), taken from a ten-round
data-scaling study:

| | Training data | Judge /5 | Forgetting vs base |
| --- | --- | --- | --- |
| **Left** | 2,000 QnA pairs (day 2) | **1.50** | **+9.5%** |
| **Right** | 10,000 QnA pairs (day 10) | 1.54 | +16.3% |

Ask both the same question and see whether **5× the data** bought anything.

**The study's answer: no.** The judge score was flat (1.50 → 1.54 — inside the measured ±0.07 noise
band) while catastrophic forgetting nearly **tripled**. The smaller model strictly dominates.

📊 **Full write-up:** https://ace-2504.github.io/fine-tuned-125m-slm/
· 💻 **Code:** https://github.com/Ace-2504/fine-tuned-125m-slm

⚠️ **Research artifact, not a usable assistant.** Both models score ~1.5/5 on answer quality —
expect fluent, confident, frequently wrong answers. Not for legal or financial advice.
