# SFT Run Report — Day 3 (SFT run)

## 1. Run identity

- Day / dataset scale: **3** · train examples: **3000**
- GPU: **NVIDIA L4** (Modal L4) · device cuda
- Base checkpoint: `Ace-2504/slm-125m-base` (volume `slm-125m`)

## 2. Parameters

- Model: 12L/768d/12h, 125.8M params, ctx 1024, tied embeddings
- Fine-tune: **full FT** · epochs **3** · batch **16** · steps **564** (warmup 28)
- LR 3e-05 → 3e-06 cosine · wd 0.0 · seed 1337
- Loss: assistant-only masking · chat template with `<|user|>/<|assistant|>/<|system|>`
- Teacher (data): `gemini-3.1-flash-lite`

## 3. Dataset composition

- Train pairs: **3000** · by day: {1: 859, 2: 1070, 3: 1071}
- Task: {'qa': 1650, 'rewrite': 300, 'extract': 450, 'summarize': 600}
- Mode: {'closed_book': 1253, 'raft': 397, 'context': 1350}
- Domain: {'sec': 1284, 'case-law': 1057, 'fineweb-edu': 659}
- Generation (day 3): 345 requests, 1725 raw pairs, tok in/out 468685/159846, $0 (free tier)

## 4. Data loss / catastrophic forgetting

Retention perplexity on the **pretraining val set** (base = **11.35**):

- This run: **12.601** → vs base: **+11.0%** (notable forgetting)
- vs previous (run-02): 12.601 (↑ +0.176, +1.4%)

> A retention-ppl rise is partly expected (chat-distribution shift); this run's forgetting is **notable**.

## 5. Perplexity comparison (vs previous checkpoint)

| Metric | This run (day 3) | Previous (run-02) | Δ |
| --- | --- | --- | --- |
| SFT-eval perplexity | 7.704 | 8.0018 | -0.298 |
| Retention perplexity | 12.601 | 12.425 | +0.176 |

(SFT-eval ↓ = better task fit; retention ↑ = more forgetting.)

## 6. Task quality

- SFT-eval loss: **2.0417** (ppl 7.7038)
- Final train loss: 2.127228260040283
- **Gemini-judge score: 1.46/5** (n=50)

**Fixed sample generations:**

- *Q:* What is the standard of proof in a civil lawsuit?
  *A:* The standard of proof in a civil lawsuit is the preponderance of the evidence standard.
- *Q:* Summarize what a 10-K annual report contains.
  *A:* Summarize the annual report for the year ended December 31, 1999.
- *Q:* What does it mean for a contract clause to be severable?
  *A:* The contract clause must be severable, and the parties must be bound by the terms of the contract.

## 7. Modal runtime

- Train wall: **241.3s** · total wall: 278.2s · container: 289.1s
- Peak GPU mem: **12.94 GB** · throughput: 2253.4 supervised tok/s · supervised tokens: 543,828
- **Cost: ~$0.064** (L4 @ $0.8/hr) · teacher $0 (free tier)
