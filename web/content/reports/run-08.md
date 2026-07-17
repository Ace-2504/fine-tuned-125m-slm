# SFT Run Report — Day 8 (SFT run)

## 1. Run identity

- Day / dataset scale: **8** · train examples: **8000**
- GPU: **NVIDIA L4** (Modal L4) · device cuda
- Base checkpoint: `Ace-2504/slm-125m-base` (volume `slm-125m`)

## 2. Parameters

- Model: 12L/768d/12h, 125.8M params, ctx 1024, tied embeddings
- Fine-tune: **full FT** · epochs **3** · batch **16** · steps **1500** (warmup 75)
- LR 3e-05 → 3e-06 cosine · wd 0.0 · seed 1337
- Loss: assistant-only masking · chat template with `<|user|>/<|assistant|>/<|system|>`
- Teacher (data): `gemini-3.1-flash-lite`

## 3. Dataset composition

- Train pairs: **8000** · by day: {1: 821, 2: 1042, 3: 1030, 4: 1052, 5: 1017, 6: 1005, 7: 1005, 8: 1028}
- Task: {'summarize': 1600, 'extract': 1200, 'qa': 4400, 'rewrite': 800}
- Mode: {'context': 3600, 'closed_book': 3306, 'raft': 1094}
- Domain: {'sec': 3413, 'fineweb-edu': 1746, 'case-law': 2841}
- Generation (day 8): 345 requests, 1725 raw pairs, tok in/out 467502/156812, $0 (free tier)

## 4. Data loss / catastrophic forgetting

Retention perplexity on the **pretraining val set** (base = **11.35**):

- This run: **13.099** → vs base: **+15.4%** (notable forgetting)
- vs previous (run-07): 13.099 (↑ +0.095, +0.7%)

> A retention-ppl rise is partly expected (chat-distribution shift); this run's forgetting is **notable**.

## 5. Perplexity comparison (vs previous checkpoint)

| Metric | This run (day 8) | Previous (run-07) | Δ |
| --- | --- | --- | --- |
| SFT-eval perplexity | 7.122 | 7.1994 | -0.077 |
| Retention perplexity | 13.099 | 13.004 | +0.095 |

(SFT-eval ↓ = better task fit; retention ↑ = more forgetting.)

## 6. Task quality

- SFT-eval loss: **1.9632** (ppl 7.1223)
- Final train loss: 1.8434715270996094
- **Gemini-judge score: 1.6/5** (n=50)
- **Judge by mode:** {'?': 1.6} (grounded=raft/context vs closed_book=recall)

**Fixed sample generations:**

- *Q:* What is the standard of proof in a civil lawsuit?
  *A:* The standard of proof in a civil lawsuit is the preponderance of the evidence.
- *Q:* Summarize what a 10-K annual report contains.
  *A:* Summarize a 10-K annual report for the year ended December 31, 1998.
- *Q:* What does it mean for a contract clause to be severable?
  *A:* The contract clause must be severable, and the remainder of the contract must be severable.

## 7. Modal runtime

- Train wall: **652.8s** · total wall: 691.1s · container: 710.7s
- Peak GPU mem: **13.72 GB** · throughput: 2209.5 supervised tok/s · supervised tokens: 1,442,301
- **Cost: ~$0.158** (L4 @ $0.8/hr) · teacher $0 (free tier)
