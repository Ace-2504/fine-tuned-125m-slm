"""SFT dataset loader with assistant-only loss masking.

Masking construction (robust to BPE boundary issues):
  prompt_ids = apply_chat_template(messages[:-1], add_generation_prompt=True)  # ends "<|assistant|>\n"
  target_ids = encode(assistant_content) + [eos]
  input_ids  = prompt_ids + target_ids
  labels     = [-100]*len(prompt_ids) + target_ids

This mirrors inference exactly (at generation time the same prompt is built with
add_generation_prompt=True and the model generates the target fresh), so there is no
train/inference tokenization mismatch at the assistant boundary. Loss is computed ONLY on the
assistant answer + its terminating <|eos|>.
"""

from __future__ import annotations

import json
from pathlib import Path

import sft_config as C

IGNORE = -100


def load_tokenizer(tokenizer_dir=None):
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(str(tokenizer_dir or C.TOKENIZER_DIR))
    tok.chat_template = C.CHAT_TEMPLATE
    return tok


def encode_example(messages: list[dict], tokenizer, max_len: int = C.MAX_SEQ_LEN):
    eos_id = tokenizer.convert_tokens_to_ids(C.SPECIAL_TOKENS["eos_token"])
    prompt_ids = tokenizer.apply_chat_template(
        messages[:-1], add_generation_prompt=True, tokenize=True)
    target_ids = tokenizer.encode(messages[-1]["content"], add_special_tokens=False) + [eos_id]
    input_ids = prompt_ids + target_ids
    labels = [IGNORE] * len(prompt_ids) + list(target_ids)
    if len(input_ids) > max_len:
        input_ids = input_ids[:max_len]
        labels = labels[:max_len]
    return input_ids, labels


class SFTDataset:
    """Pre-tokenized (input_ids, labels) pairs from a chat JSONL."""

    def __init__(self, path: str | Path, tokenizer, max_len: int = C.MAX_SEQ_LEN):
        self.examples: list[tuple[list[int], list[int]]] = []
        skipped = 0
        with open(path, encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                ids, labels = encode_example(rec["messages"], tokenizer, max_len)
                if any(l != IGNORE for l in labels):     # must have >=1 supervised token
                    self.examples.append((ids, labels))
                else:
                    skipped += 1
        self.skipped = skipped

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, i):
        return self.examples[i]


def collate(batch, pad_id: int):
    import torch
    max_len = max(len(ids) for ids, _ in batch)
    input_ids, labels, attn = [], [], []
    for ids, labs in batch:
        pad = max_len - len(ids)
        input_ids.append(ids + [pad_id] * pad)
        labels.append(labs + [IGNORE] * pad)
        attn.append([1] * len(ids) + [0] * pad)
    return (torch.tensor(input_ids, dtype=torch.long),
            torch.tensor(labels, dtype=torch.long),
            torch.tensor(attn, dtype=torch.long))
