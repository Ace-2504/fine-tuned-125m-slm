"""Local FastAPI inference server for the two SFT checkpoints (2k and 10k).

Serves BOTH revisions of Ace-2504/fine-tuned-125m-slm side by side so a frontend can ask the
same question of each and show the study's finding directly:

    main    -> "day-2"   2,000 pairs  (judge 1.50 · forgetting +9.5%)  — the better model
    day-10  -> "day-10"  10,000 pairs (judge 1.54 · forgetting +16.3%) — the endpoint

Routes (mirrors the contract used by the reference deployment, so a frontend can target either):
    GET  /health    -> {"ok":true,"models":[...],"device":"cpu"}
    POST /generate  -> {"generated": "..."}          body: {model, question, system?, ...}
    POST /compare   -> {"day-2": "...", "day-10": "..."}   body: {question, system?, ...}

CORS is open (`*`) so a browser (or a Cloudflare-tunnelled origin) can call it directly — same as
the reference endpoint. Auth is OFF by default; set API_SECRET to require a Bearer token.

Run via `serve_sft_local.py` (see that file), then expose with:
    cloudflared tunnel --url http://localhost:8000
"""

from __future__ import annotations

import os
import threading
import time

import torch
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer

REPO = os.environ.get("SFT_MODEL_REPO", "Ace-2504/fine-tuned-125m-slm")
API_SECRET = os.environ.get("API_SECRET", "")          # empty => open (like the reference)
MAX_NEW_TOKENS_CAP = 256
MAX_QUESTION_CHARS = 2000

# label -> (revision, human description)
VARIANTS = {
    "day-2": ("main", "2,000 pairs · judge 1.50 · forgetting +9.5% (the better model)"),
    "day-10": ("day-10", "10,000 pairs · judge 1.54 · forgetting +16.3% (study endpoint)"),
}
DEFAULT_SYSTEM = "You are a precise legal and financial assistant."

app = FastAPI(title="slm-125m-sft", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

_lock = threading.Lock()
_tok: dict = {}
_model: dict = {}
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

torch.set_num_threads(max(1, os.cpu_count() or 1))
for label, (rev, _) in VARIANTS.items():
    print(f"loading {REPO}@{rev} as '{label}' …", flush=True)
    _tok[label] = AutoTokenizer.from_pretrained(REPO, revision=rev)
    m = AutoModelForCausalLM.from_pretrained(REPO, revision=rev, torch_dtype=torch.float32)
    m.eval()
    _model[label] = m.to(DEVICE)
print(f"ready on {DEVICE}: {list(VARIANTS)}", flush=True)


class GenerateRequest(BaseModel):
    question: str = ""
    prompt: str = ""                 # alias for `question`
    model: str = "day-2"
    system: str = DEFAULT_SYSTEM
    max_new_tokens: int = 120
    temperature: float = 0.7


def _auth(authorization: str) -> None:
    if API_SECRET and authorization != f"Bearer {API_SECRET}":
        raise HTTPException(status_code=401, detail="unauthorized")


def _run(label: str, question: str, system: str, max_new_tokens: int, temperature: float) -> str:
    tok, model = _tok[label], _model[label]
    msgs = [{"role": "system", "content": (system or DEFAULT_SYSTEM).strip()},
            {"role": "user", "content": question.strip()}]
    ids = tok.apply_chat_template(msgs, add_generation_prompt=True,
                                  return_tensors="pt").to(DEVICE)
    do_sample = temperature is not None and temperature > 0
    with _lock, torch.inference_mode():
        out = model.generate(
            ids,
            max_new_tokens=int(max(1, min(MAX_NEW_TOKENS_CAP, max_new_tokens))),
            do_sample=do_sample,
            temperature=float(temperature) if do_sample else None,
            top_p=0.9 if do_sample else None,
            repetition_penalty=1.3,      # without this the model loops (see training-feedback/day1.md)
            no_repeat_ngram_size=3,
            pad_token_id=tok.pad_token_id,
            eos_token_id=tok.eos_token_id,
        )
    return tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True).strip()


@app.get("/health")
def health():
    return {
        "ok": True,
        "repo": REPO,
        "device": DEVICE,
        "auth": bool(API_SECRET),
        "models": [{"id": k, "revision": v[0], "about": v[1]} for k, v in VARIANTS.items()],
        "study": "https://ace-2504.github.io/fine-tuned-125m-slm/",
    }


@app.get("/")
def root():
    return health()


@app.post("/generate")
def generate(req: GenerateRequest, authorization: str = Header(default="")):
    _auth(authorization)
    question = (req.question or req.prompt or "").strip()[:MAX_QUESTION_CHARS]
    if not question:
        raise HTTPException(status_code=400, detail="empty question")
    if req.model not in VARIANTS:
        raise HTTPException(status_code=400, detail=f"model must be one of {list(VARIANTS)}")
    t = time.time()
    text = _run(req.model, question, req.system, req.max_new_tokens, req.temperature)
    return {"generated": text, "model": req.model, "seconds": round(time.time() - t, 2)}


@app.post("/compare")
def compare(req: GenerateRequest, authorization: str = Header(default="")):
    """Ask BOTH checkpoints the same question — the comparison the study is about."""
    _auth(authorization)
    question = (req.question or req.prompt or "").strip()[:MAX_QUESTION_CHARS]
    if not question:
        raise HTTPException(status_code=400, detail="empty question")
    t = time.time()
    out = {label: _run(label, question, req.system, req.max_new_tokens, req.temperature)
           for label in VARIANTS}
    out["seconds"] = round(time.time() - t, 2)
    return out
