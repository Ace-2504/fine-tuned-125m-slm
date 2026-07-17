"""Gradio Space — SLM-125M SFT study: compare the 2k and 10k checkpoints side by side.

Loads both revisions of Ace-2504/fine-tuned-125m-slm (main = day 2, day-10 = day 10) and answers
the same prompt with each, so the study's central finding is visible directly: 5× more training
data bought no quality — and measurably more forgetting.

Runs on ZeroGPU when available; falls back cleanly to CPU (a 125M model is fast enough either way).
"""

import os

import gradio as gr
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

REPO = os.environ.get("MODEL_REPO", "Ace-2504/fine-tuned-125m-slm")
MAX_NEW_TOKENS_CAP = 256

# ZeroGPU decorator when on a ZeroGPU Space; no-op otherwise (CPU Space / local).
try:
    import spaces

    def gpu(fn):
        return spaces.GPU(duration=60)(fn)
except Exception:  # noqa: BLE001 — `spaces` only exists on HF Spaces
    def gpu(fn):
        return fn

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32

VARIANTS = [
    ("day-2", "main", "Day 2 · 2,000 pairs", "judge 1.50 · forgetting +9.5%"),
    ("day-10", "day-10", "Day 10 · 10,000 pairs", "judge 1.54 · forgetting +16.3%"),
]

_tok, _model = {}, {}
for key, rev, _, _ in VARIANTS:
    _tok[key] = AutoTokenizer.from_pretrained(REPO, revision=rev)
    m = AutoModelForCausalLM.from_pretrained(REPO, revision=rev, torch_dtype=DTYPE)
    m.eval()
    _model[key] = m.to(DEVICE)


def _answer(key: str, system: str, question: str, temperature: float, max_new_tokens: int) -> str:
    tok, model = _tok[key], _model[key]
    msgs = [{"role": "system", "content": system.strip() or "You are a helpful assistant."},
            {"role": "user", "content": question.strip()}]
    ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt").to(DEVICE)
    do_sample = temperature and temperature > 0
    with torch.inference_mode():
        out = model.generate(
            ids,
            max_new_tokens=int(min(MAX_NEW_TOKENS_CAP, max_new_tokens)),
            do_sample=bool(do_sample),
            temperature=float(temperature) if do_sample else None,
            top_p=0.9 if do_sample else None,
            repetition_penalty=1.3,
            no_repeat_ngram_size=3,
            pad_token_id=tok.pad_token_id,
            eos_token_id=tok.eos_token_id,
        )
    text = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True).strip()
    return text or "(empty)"


@gpu
def compare(question: str, system: str, temperature: float, max_new_tokens: int):
    if not (question or "").strip():
        return "Enter a question.", "Enter a question."
    return (_answer("day-2", system, question, temperature, max_new_tokens),
            _answer("day-10", system, question, temperature, max_new_tokens))


DEFAULT_SYSTEM = "You are a precise legal and financial assistant."
EXAMPLES = [
    ["What is the standard of proof in a civil lawsuit?", DEFAULT_SYSTEM, 0.0, 120],
    ["What does it mean for a contract clause to be severable?", DEFAULT_SYSTEM, 0.0, 120],
    ["Summarize what a 10-K annual report contains.", DEFAULT_SYSTEM, 0.0, 120],
    ["What is a preponderance of the evidence?", DEFAULT_SYSTEM, 0.7, 120],
]

with gr.Blocks(title="SLM-125M · SFT scaling study", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        "# SLM-125M — did 5× more fine-tuning data help?\n"
        "Two supervised fine-tunes of the same 125.8M-parameter "
        "[base model](https://huggingface.co/Ace-2504/slm-125m-base), from a ten-round data-scaling "
        "study. **Left: trained on 2,000 QnA pairs. Right: trained on 10,000.** Ask both the same "
        "question and see whether 5× the data bought anything.\n\n"
        "**The study's answer: no.** Judge score was flat (1.50 → 1.54, inside the ±0.07 noise band) "
        "while catastrophic forgetting nearly tripled (+9.5% → +16.3%). "
        "📊 [Full write-up](https://ace-2504.github.io/fine-tuned-125m-slm/) · "
        "💻 [Code](https://github.com/Ace-2504/fine-tuned-125m-slm)"
    )
    gr.Markdown(
        "> ⚠️ **This is a research artifact, not a usable assistant.** Both models score ~1.5/5 on "
        "answer quality. Expect confident, fluent, frequently **wrong** answers. ~40% of their "
        "training asked them to recall document facts from a single exposure — something a 125M "
        "model simply cannot do. Not for legal or financial advice."
    )

    with gr.Row():
        with gr.Column(scale=3):
            question = gr.Textbox(label="Question", lines=3,
                                  value="What is the standard of proof in a civil lawsuit?")
            system = gr.Textbox(label="System prompt", lines=2, value=DEFAULT_SYSTEM)
            run = gr.Button("Ask both models", variant="primary")
        with gr.Column(scale=2):
            temperature = gr.Slider(0.0, 1.5, value=0.0, step=0.05,
                                    label="Temperature (0 = deterministic)")
            max_new_tokens = gr.Slider(20, MAX_NEW_TOKENS_CAP, value=120, step=10,
                                       label="Max new tokens")

    with gr.Row():
        out_a = gr.Textbox(label="◀ Day 2 — 2,000 pairs  ·  judge 1.50 · forgetting +9.5%  (the better model)",
                           lines=9)
        out_b = gr.Textbox(label="Day 10 — 10,000 pairs  ·  judge 1.54 · forgetting +16.3%  (5× the data) ▶",
                           lines=9)

    gr.Markdown(
        "*Both use `repetition_penalty=1.3` + `no_repeat_ngram_size=3`. Without them this model "
        "collapses into greedy repetition loops — a decoding artifact the study documents separately.*"
    )

    run.click(compare, inputs=[question, system, temperature, max_new_tokens],
              outputs=[out_a, out_b])
    gr.Examples(EXAMPLES, inputs=[question, system, temperature, max_new_tokens])

if __name__ == "__main__":
    demo.launch()
