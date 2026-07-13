"""Teacher backend for QnA synthesis — Gemini via google-genai, rate-limited + resilient.

Teacher-agnostic surface: the generator only calls `TeacherClient.generate_json(prompt, ...)`.
Swapping to another backend (e.g. Groq/Llama-3.3-70B) means adding one class with the same
method, no change to the generator.

Handles:
- proactive pacing under the free-tier RPM,
- exponential backoff + jitter on 429 / 5xx (RPM/TPM blips),
- a distinct RPDExhausted signal on a persistent daily wall (generator exits cleanly, resumes),
- strict-JSON output via response_schema.
"""

from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

import sft_config as C


class RPDExhausted(Exception):
    """Raised when the daily request wall is hit and backoff cannot clear it."""


@dataclass
class Usage:
    requests: int = 0
    in_tokens: int = 0
    out_tokens: int = 0
    retries: int = 0

    def add(self, in_t: int, out_t: int) -> None:
        self.requests += 1
        self.in_tokens += in_t or 0
        self.out_tokens += out_t or 0


@dataclass
class TeacherClient:
    model: str = C.TEACHER_MODEL
    min_interval_s: float = C.REQUEST_MIN_INTERVAL_S
    max_retries: int = C.MAX_RETRIES
    usage: Usage = field(default_factory=Usage)
    _last_call: float = 0.0

    def __post_init__(self) -> None:
        load_dotenv(C.ENV_PATH)
        key = os.environ.get("GEMINI_API_KEY", "")
        if not key:
            raise SystemExit(f"GEMINI_API_KEY not found in {C.ENV_PATH}")
        from google import genai
        self._genai = genai
        self._client = genai.Client(api_key=key)

    def _pace(self) -> None:
        wait = self.min_interval_s - (time.time() - self._last_call)
        if wait > 0:
            time.sleep(wait)

    def generate_json(self, prompt: str, schema, *, temperature: float = 0.9,
                      thinking: bool = False):
        """Return parsed JSON (list/dict) from the teacher, or raise RPDExhausted."""
        import json as _json
        from google.genai import types

        cfg_kwargs = dict(
            response_mime_type="application/json",
            response_schema=schema,
            temperature=temperature,
        )
        if not thinking:
            # disable "thinking" for cheap bulk calls where the SDK/model supports it
            try:
                cfg_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
            except Exception:
                pass
        config = types.GenerateContentConfig(**cfg_kwargs)

        delay = 2.0
        for attempt in range(self.max_retries + 1):
            self._pace()
            try:
                r = self._client.models.generate_content(
                    model=self.model, contents=prompt, config=config)
                self._last_call = time.time()
                um = getattr(r, "usage_metadata", None)
                self.usage.add(getattr(um, "prompt_token_count", 0) if um else 0,
                               getattr(um, "candidates_token_count", 0) if um else 0)
                return _json.loads(r.text)
            except Exception as e:  # noqa: BLE001 — classify by message/status
                self._last_call = time.time()
                status = _status_of(e)
                transient = status in (429, 500, 502, 503, 504)
                if not transient or attempt == self.max_retries:
                    if status == 429:
                        # backoff already exhausted -> treat as daily wall
                        raise RPDExhausted(str(e)[:200]) from e
                    raise
                self.usage.retries += 1
                time.sleep(delay + random.uniform(0, delay))
                delay = min(delay * 2, 60.0)
        raise RPDExhausted("retries exhausted")


def _status_of(exc: Exception) -> int | None:
    for attr in ("code", "status_code"):
        v = getattr(exc, attr, None)
        if isinstance(v, int):
            return v
    s = str(exc)
    for code in (429, 500, 502, 503, 504, 404, 401, 403):
        if str(code) in s:
            return code
    return None
