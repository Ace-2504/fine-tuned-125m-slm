# SFT Run Report — Day 5 (SFT run)

## 1. Run identity

- Day / dataset scale: **5** · train examples: **4999**
- GPU: **NVIDIA L4** (Modal L4) · device cuda
- Base checkpoint: `Ace-2504/slm-125m-base` (volume `slm-125m`)

## 2. Parameters

- Model: 12L/768d/12h, 125.8M params, ctx 1024, tied embeddings
- Fine-tune: **full FT** · epochs **3** · batch **16** · steps **939** (warmup 46)
- LR 3e-05 → 3e-06 cosine · wd 0.0 · seed 1337
- Loss: assistant-only masking · chat template with `<|user|>/<|assistant|>/<|system|>`
- Teacher (data): `gemini-3.1-flash-lite`

## 3. Dataset composition

- Train pairs: **4999** · by day: {1: 852, 2: 1015, 3: 1030, 4: 1060, 5: 1042}
- Task: {'qa': 2750, 'summarize': 1000, 'extract': 749, 'rewrite': 500}
- Mode: {'closed_book': 2075, 'context': 2249, 'raft': 675}
- Domain: {'fineweb-edu': 1104, 'sec': 2108, 'case-law': 1787}
- Generation (day 5): 345 requests, 1721 raw pairs, tok in/out 472542/158355, $0 (free tier)

## 4. Data loss / catastrophic forgetting

Retention perplexity on the **pretraining val set** (base = **11.35**):

- This run: **12.897** → vs base: **+13.6%** (notable forgetting)
- vs previous (run-04): 12.897 (↑ +0.160, +1.3%)

> A retention-ppl rise is partly expected (chat-distribution shift); this run's forgetting is **notable**.

## 5. Perplexity comparison (vs previous checkpoint)

| Metric | This run (day 5) | Previous (run-04) | Δ |
| --- | --- | --- | --- |
| SFT-eval perplexity | 7.366 | 7.5055 | -0.139 |
| Retention perplexity | 12.897 | 12.737 | +0.160 |

(SFT-eval ↓ = better task fit; retention ↑ = more forgetting.)

## 6. Task quality

- SFT-eval loss: **1.9969** (ppl 7.3661)
- Final train loss: 1.7835110425949097
- **Gemini-judge score: 1.52/5** (n=50)
- **Judge by mode:** {'?': 1.52} (grounded=raft/context vs closed_book=recall)

**Fixed sample generations:**

- *Q:* What is the standard of proof in a civil lawsuit?
  *A:* The standard of proof in a civil lawsuit is the preponderance of the evidence standard.
- *Q:* Summarize what a 10-K annual report contains.
  *A:* Summarize the annual report for the year ended December 31, 1998, and the annual report for the year ended December 31, 1999.
- *Q:* What does it mean for a contract clause to be severable?
  *A:* The contract clause must be severable, and the parties must be bound by the terms of the contract.

## 7. Modal runtime

- Train wall: **399.5s** · total wall: 442.4s · container: 458.5s
- Peak GPU mem: **13.96 GB** · throughput: 2264.1 supervised tok/s · supervised tokens: 904,596
- **Cost: ~$0.102** (L4 @ $0.8/hr) · teacher $0 (free tier)
