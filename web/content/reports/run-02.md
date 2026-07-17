# SFT Run Report — Day 2 (SFT run)

## 1. Run identity

- Day / dataset scale: **2** · train examples: **2000**
- GPU: **NVIDIA L4** (Modal L4) · device cuda
- Base checkpoint: `Ace-2504/slm-125m-base` (volume `slm-125m`)

## 2. Parameters

- Model: 12L/768d/12h, 125.8M params, ctx 1024, tied embeddings
- Fine-tune: **full FT** · epochs **3** · batch **16** · steps **375** (warmup 18)
- LR 3e-05 → 3e-06 cosine · wd 0.0 · seed 1337
- Loss: assistant-only masking · chat template with `<|user|>/<|assistant|>/<|system|>`
- Teacher (data): `gemini-3.1-flash-lite`

## 3. Dataset composition

- Train pairs: **2000** · by day: {1: 913, 2: 1087}
- Task: {'qa': 1100, 'extract': 300, 'rewrite': 200, 'summarize': 400}
- Mode: {'closed_book': 847, 'context': 900, 'raft': 253}
- Domain: {'sec': 834, 'case-law': 717, 'fineweb-edu': 449}
- Generation (day 2): 209 requests, 1037 raw pairs, tok in/out 394103/102715, $0 (free tier)

## 4. Data loss / catastrophic forgetting

Retention perplexity on the **pretraining val set** (base = **11.35**):

- This run: **12.425** → vs base: **+9.5%** (mild forgetting)
- vs previous (run-01): 12.425 (↑ +0.380, +3.2%)

> A retention-ppl rise is partly expected (chat-distribution shift); this run's forgetting is **mild**.

## 5. Perplexity comparison (vs previous checkpoint)

| Metric | This run (day 2) | Previous (run-01) | Δ |
| --- | --- | --- | --- |
| SFT-eval perplexity | 8.002 | 8.5955 | -0.594 |
| Retention perplexity | 12.425 | 12.045 | +0.380 |

(SFT-eval ↓ = better task fit; retention ↑ = more forgetting.)

## 6. Task quality

- SFT-eval loss: **2.0797** (ppl 8.0018)
- Final train loss: 2.0033435821533203
- **Gemini-judge score: 1.5/5** (n=50)

**Fixed sample generations:**

- *Q:* What is the standard of proof in a civil lawsuit?
  *A:* The standard of proof in a civil lawsuit is not a standard of proof, but is a standard of proof that is applied to a case.
- *Q:* Summarize what a 10-K annual report contains.
  *A:* Summarize the report to include a 10-K annual report.
- *Q:* What does it mean for a contract clause to be severable?
  *A:* The contract clause is severable from the other provisions of the contract.

## 7. Modal runtime

- Train wall: **164.0s** · total wall: 207.0s · container: 220.4s
- Peak GPU mem: **12.14 GB** · throughput: 2201.4 supervised tok/s · supervised tokens: 361,065
- **Cost: ~$0.049** (L4 @ $0.8/hr) · teacher $0 (free tier)
