# SFT Run Report — Day 9 (SFT run)

## 1. Run identity

- Day / dataset scale: **9** · train examples: **8998**
- GPU: **NVIDIA L4** (Modal L4) · device cuda
- Base checkpoint: `Ace-2504/slm-125m-base` (volume `slm-125m`)

## 2. Parameters

- Model: 12L/768d/12h, 125.8M params, ctx 1024, tied embeddings
- Fine-tune: **full FT** · epochs **3** · batch **16** · steps **1689** (warmup 84)
- LR 3e-05 → 3e-06 cosine · wd 0.0 · seed 1337
- Loss: assistant-only masking · chat template with `<|user|>/<|assistant|>/<|system|>`
- Teacher (data): `gemini-3.1-flash-lite`

## 3. Dataset composition

- Train pairs: **8998** · by day: {1: 825, 2: 1014, 3: 1040, 4: 1025, 5: 1017, 6: 1021, 7: 1021, 8: 1016, 9: 1019}
- Task: {'qa': 4950, 'rewrite': 900, 'summarize': 1800, 'extract': 1348}
- Mode: {'closed_book': 3709, 'context': 4048, 'raft': 1241}
- Domain: {'case-law': 3224, 'sec': 3837, 'fineweb-edu': 1937}
- Generation (day 9): 345 requests, 1725 raw pairs, tok in/out 471963/160377, $0 (free tier)

## 4. Data loss / catastrophic forgetting

Retention perplexity on the **pretraining val set** (base = **11.35**):

- This run: **13.184** → vs base: **+16.2%** (notable forgetting)
- vs previous (run-08): 13.184 (↑ +0.085, +0.6%)

> A retention-ppl rise is partly expected (chat-distribution shift); this run's forgetting is **notable**.

## 5. Perplexity comparison (vs previous checkpoint)

| Metric | This run (day 9) | Previous (run-08) | Δ |
| --- | --- | --- | --- |
| SFT-eval perplexity | 7.049 | 7.1223 | -0.073 |
| Retention perplexity | 13.184 | 13.099 | +0.085 |

(SFT-eval ↓ = better task fit; retention ↑ = more forgetting.)

## 6. Task quality

- SFT-eval loss: **1.9529** (ppl 7.0489)
- Final train loss: 1.6759381294250488
- **Gemini-judge score: 1.54/5** (n=50)
- **Judge by mode:** {'?': 1.54} (grounded=raft/context vs closed_book=recall)

**Fixed sample generations:**

- *Q:* What is the standard of proof in a civil lawsuit?
  *A:* The standard of proof in a civil lawsuit is the preponderance of the evidence.
- *Q:* Summarize what a 10-K annual report contains.
  *A:* Summarize the annual report for the year ended December 31, 1998, and the annual report for the year ended December 31, 1999.
- *Q:* What does it mean for a contract clause to be severable?
  *A:* The contract clause must be severable, and the remainder of the contract must be severable.

## 7. Modal runtime

- Train wall: **717.8s** · total wall: 763.1s · container: 784.1s
- Peak GPU mem: **13.47 GB** · throughput: 2265.6 supervised tok/s · supervised tokens: 1,626,135
- **Cost: ~$0.174** (L4 @ $0.8/hr) · teacher $0 (free tier)
