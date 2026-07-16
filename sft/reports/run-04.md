# SFT Run Report — Day 4 (SFT run)

## 1. Run identity

- Day / dataset scale: **4** · train examples: **4000**
- GPU: **NVIDIA L4** (Modal L4) · device cuda
- Base checkpoint: `Ace-2504/slm-125m-base` (volume `slm-125m`)

## 2. Parameters

- Model: 12L/768d/12h, 125.8M params, ctx 1024, tied embeddings
- Fine-tune: **full FT** · epochs **3** · batch **16** · steps **750** (warmup 37)
- LR 3e-05 → 3e-06 cosine · wd 0.0 · seed 1337
- Loss: assistant-only masking · chat template with `<|user|>/<|assistant|>/<|system|>`
- Teacher (data): `gemini-3.1-flash-lite`

## 3. Dataset composition

- Train pairs: **4000** · by day: {1: 870, 2: 1038, 3: 1056, 4: 1036}
- Task: {'summarize': 800, 'qa': 2200, 'extract': 600, 'rewrite': 400}
- Mode: {'context': 1800, 'raft': 536, 'closed_book': 1664}
- Domain: {'sec': 1691, 'fineweb-edu': 901, 'case-law': 1408}
- Generation (day 4): 345 requests, 1721 raw pairs, tok in/out 471710/159743, $0 (free tier)

## 4. Data loss / catastrophic forgetting

Retention perplexity on the **pretraining val set** (base = **11.35**):

- This run: **12.737** → vs base: **+12.2%** (notable forgetting)
- vs previous (run-03): 12.737 (↑ +0.136, +1.1%)

> A retention-ppl rise is partly expected (chat-distribution shift); this run's forgetting is **notable**.

## 5. Perplexity comparison (vs previous checkpoint)

| Metric | This run (day 4) | Previous (run-03) | Δ |
| --- | --- | --- | --- |
| SFT-eval perplexity | 7.505 | 7.7038 | -0.198 |
| Retention perplexity | 12.737 | 12.601 | +0.136 |

(SFT-eval ↓ = better task fit; retention ↑ = more forgetting.)

## 6. Task quality

- SFT-eval loss: **2.0156** (ppl 7.5055)
- Final train loss: 1.7417744398117065
- **Gemini-judge score: 1.5/5** (n=50)
- **Judge by mode:** {'?': 1.5} (grounded=raft/context vs closed_book=recall)

**Fixed sample generations:**

- *Q:* What is the standard of proof in a civil lawsuit?
  *A:* The standard of proof in a civil lawsuit is the preponderance of the evidence standard.
- *Q:* Summarize what a 10-K annual report contains.
  *A:* Summarize the report to include a 10-K annual report.
- *Q:* What does it mean for a contract clause to be severable?
  *A:* The contract clause must be severable, and the remainder of the contract must be severable.

## 7. Modal runtime

- Train wall: **331.1s** · total wall: 369.6s · container: 381.9s
- Peak GPU mem: **13.97 GB** · throughput: 2189.0 supervised tok/s · supervised tokens: 724,758
- **Cost: ~$0.085** (L4 @ $0.8/hr) · teacher $0 (free tier)
