"""Run the SFT inference server (2k + 10k checkpoints) locally.

Mirrors the repo's `serve_local.py` pattern, but serves BOTH SFT revisions of
Ace-2504/fine-tuned-125m-slm with the chat template applied (see sft_server.py).

    ./.venv/Scripts/python.exe sft/serve_sft_local.py

Then expose it publicly through your Cloudflare tunnel:

    cloudflared tunnel --url http://localhost:8000

Both models are ~503 MB each and load into RAM (~1 GB total) on first run; they are cached in
~/.cache/huggingface after the first download.

Env overrides:
    SFT_PORT        port (default 8000)
    SFT_HOST        bind address (default 127.0.0.1; use 0.0.0.0 to accept LAN/tunnel traffic
                    directly — not needed for `cloudflared tunnel --url`, which connects to localhost)
    API_SECRET      if set, requires `Authorization: Bearer <secret>` (default: open, like the
                    reference deployment)
    SFT_MODEL_REPO  model repo (default Ace-2504/fine-tuned-125m-slm)
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("SFT_HOST", "127.0.0.1")
    port = int(os.environ.get("SFT_PORT", "8000"))
    print(f"serving SFT models on http://{host}:{port}  (docs: /docs, health: /health)")
    print("tunnel with:  cloudflared tunnel --url http://localhost:%d" % port)
    uvicorn.run("sft_server:app", host=host, port=port, log_level="info")
