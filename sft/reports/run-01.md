# SFT Run Report — Day 1 (SFT run)

## 1. Run identity

- Day / dataset scale: **1** · train examples: **1000**
- GPU: **NVIDIA L4** (Modal L4) · device cuda
- Base checkpoint: `Ace-2504/slm-125m-base` (volume `slm-125m`)

## 2. Parameters

- Model: 12L/768d/12h, 125.8M params, ctx 1024, tied embeddings
- Fine-tune: **full FT** · epochs **3** · batch **16** · steps **189** (warmup 9)
- LR 3e-05 → 3e-06 cosine · wd 0.0 · seed 1337
- Loss: assistant-only masking · chat template with `<|user|>/<|assistant|>/<|system|>`
- Teacher (data): `gemini-3.1-flash-lite`

## 3. Dataset composition

- Train pairs: **1000** · by day: {1: 1000}
- Task: {'qa': 550, 'summarize': 200, 'extract': 150, 'rewrite': 100}
- Mode: {'raft': 133, 'closed_book': 417, 'context': 450}
- Domain: {'sec': 420, 'case-law': 352, 'fineweb-edu': 228}
- Generation (day 1): 345 requests, 1721 raw pairs, tok in/out 468035/158404, $0 (free tier)

## 4. Data loss / catastrophic forgetting

Retention perplexity on the **pretraining val set** (base = **11.35**):

- This run: **12.045** → vs base: **+6.1%** (mild forgetting)
- vs previous (run-00): 12.045 (↑ +0.691, +6.1%)

> A retention-ppl rise is partly expected (chat-distribution shift); this run's forgetting is **mild**.

## 5. Perplexity comparison (vs previous checkpoint)

| Metric | This run (day 1) | Previous (run-00) | Δ |
| --- | --- | --- | --- |
| SFT-eval perplexity | 8.595 | 24.4367 | -15.841 |
| Retention perplexity | 12.045 | 11.355 | +0.691 |

(SFT-eval ↓ = better task fit; retention ↑ = more forgetting.)

## 6. Task quality

- SFT-eval loss: **2.1512** (ppl 8.5955)
- Final train loss: 1.8386907577514648
- **Gemini-judge score: 1.32/5** (n=50)

**Fixed sample generations:**

- *Q:* What is the standard of proof in a civil lawsuit?
  *A:* The standard of proof in a civil lawsuit is the standard of proof in a civil lawsuit.
- *Q:* Summarize what a 10-K annual report contains.
  *A:* Summarize what a 10-K annual report contains.
- *Q:* What does it mean for a contract clause to be severable?
  *A:* The contract clause is not severable, and the parties are bound by the terms of the contract.

## 7. Modal runtime

- Train wall: **79.2s** · total wall: 121.5s · container: 130.4s
- Peak GPU mem: **11.52 GB** · throughput: 2254.3 supervised tok/s · supervised tokens: 178,635
- **Cost: ~$0.029** (L4 @ $0.8/hr) · teacher $0 (free tier)
