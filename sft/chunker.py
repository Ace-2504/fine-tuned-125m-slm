"""Corpus chunker + stratified sampler for QnA synthesis.

Samples fresh passages from the cleaned pretraining corpus (one doc per line, ~13 GB)
without a full scan, using random byte-offset seeks. Each chunk gets a content-hash id so
the same passage is never reused across days (idempotency), and identical text collides to
the same id naturally.
"""

from __future__ import annotations

import hashlib
import os
import random
from dataclasses import dataclass
from pathlib import Path

import sft_config as C

_CHARS_PER_TOKEN = 4.0
CHUNK_CHARS = int(C.CHUNK_TOKENS * _CHARS_PER_TOKEN)   # ~2000
MIN_CHUNK_CHARS = 600
_MAX_TRIES_PER_CHUNK = 40


@dataclass
class Chunk:
    chunk_id: str
    source: str
    text: str
    token_len: int


def _shard_paths(source: str) -> list[Path]:
    d = C.CORPUS_DIR / source
    paths = sorted(d.glob("*.txt"))
    if not paths:
        raise FileNotFoundError(f"no corpus shards in {d}")
    return paths


def _random_doc(paths: list[Path], rng: random.Random) -> str:
    """Uniformly-ish random document via a random byte offset + next full line."""
    path = rng.choice(paths)
    size = path.stat().st_size
    with open(path, "rb") as f:
        f.seek(rng.randint(0, max(0, size - 2)))
        f.readline()                      # discard the partial line we landed in
        line = f.readline()               # the candidate doc
        if not line:                      # landed at EOF; wrap to start
            f.seek(0)
            line = f.readline()
    return line.decode("utf-8", errors="ignore").strip()


def _chunk_from_doc(doc: str, rng: random.Random) -> str | None:
    """A ~CHUNK_CHARS window from the doc, aligned to word boundaries."""
    if len(doc) < MIN_CHUNK_CHARS:
        return None
    if len(doc) <= CHUNK_CHARS:
        return doc
    start = rng.randint(0, len(doc) - CHUNK_CHARS)
    window = doc[start:start + CHUNK_CHARS]
    # trim to whole words at both ends
    if start > 0 and " " in window:
        window = window[window.index(" ") + 1:]
    if " " in window:
        window = window[:window.rindex(" ")]
    return window.strip() or None


def _chunk_id(source: str, text: str) -> str:
    return hashlib.sha256(f"{source}:{text}".encode("utf-8")).hexdigest()[:16]


def sample_chunks(targets: dict[str, int], used_ids: set[str],
                  rng: random.Random, tokenizer) -> list[Chunk]:
    """Return fresh chunks per-domain per `targets`, skipping any already-used chunk_id."""
    out: list[Chunk] = []
    for source, n in targets.items():
        if n <= 0:
            continue
        paths = _shard_paths(source)
        got = 0
        tries = 0
        while got < n and tries < n * _MAX_TRIES_PER_CHUNK:
            tries += 1
            text = _chunk_from_doc(_random_doc(paths, rng), rng)
            if not text:
                continue
            cid = _chunk_id(source, text)
            if cid in used_ids:
                continue
            token_len = len(tokenizer.encode(text, add_special_tokens=False))
            used_ids.add(cid)
            out.append(Chunk(cid, source, text, token_len))
            got += 1
        if got < n:
            print(f"  [chunker] WARNING: only {got}/{n} chunks for {source}", flush=True)
    rng.shuffle(out)
    return out


def domain_targets(total: int) -> dict[str, int]:
    """Split a chunk count across domains by DOMAIN_MIX (largest-remainder rounding)."""
    raw = {s: total * w for s, w in C.DOMAIN_MIX.items()}
    floors = {s: int(v) for s, v in raw.items()}
    rem = total - sum(floors.values())
    for s in sorted(raw, key=lambda k: raw[k] - floors[k], reverse=True)[:rem]:
        floors[s] += 1
    return floors


def load_tokenizer():
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(str(C.TOKENIZER_DIR))
