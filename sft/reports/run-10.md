# SFT Run Report — Day 10 (SFT run)

## 1. Run identity

- Day / dataset scale: **10** · train examples: **9999**
- GPU: **NVIDIA L4** (Modal L4) · device cuda
- Base checkpoint: `Ace-2504/slm-125m-base` (volume `slm-125m`)

## 2. Parameters

- Model: 12L/768d/12h, 125.8M params, ctx 1024, tied embeddings
- Fine-tune: **full FT** · epochs **3** · batch **16** · steps **1875** (warmup 93)
- LR 3e-05 → 3e-06 cosine · wd 0.0 · seed 1337
- Loss: assistant-only masking · chat template with `<|user|>/<|assistant|>/<|system|>`
- Teacher (data): `gemini-3.1-flash-lite`

## 3. Dataset composition

- Train pairs: **9999** · by day: {1: 804, 2: 1008, 3: 1038, 4: 1013, 5: 1022, 6: 1027, 7: 1026, 8: 1029, 9: 1024, 10: 1008}
- Task: {'qa': 5500, 'summarize': 2000, 'extract': 1499, 'rewrite': 1000}
- Mode: {'raft': 1334, 'context': 4499, 'closed_book': 4166}
- Domain: {'fineweb-edu': 2239, 'case-law': 3528, 'sec': 4232}
- Generation (day 10): 345 requests, 1721 raw pairs, tok in/out 472376/158198, $0 (free tier)

## 4. Data loss / catastrophic forgetting

Retention perplexity on the **pretraining val set** (base = **11.35**):

- This run: **13.200** → vs base: **+16.3%** (notable forgetting)
- vs previous (run-09): 13.200 (↑ +0.016, +0.1%)

> A retention-ppl rise is partly expected (chat-distribution shift); this run's forgetting is **notable**.

## 5. Perplexity comparison (vs previous checkpoint)

| Metric | This run (day 10) | Previous (run-09) | Δ |
| --- | --- | --- | --- |
| SFT-eval perplexity | 7.007 | 7.0489 | -0.042 |
| Retention perplexity | 13.200 | 13.184 | +0.016 |

(SFT-eval ↓ = better task fit; retention ↑ = more forgetting.)

## 6. Task quality

- SFT-eval loss: **1.9469** (ppl 7.0067)
- Final train loss: 1.896994709968567
- **Gemini-judge score: 1.54/5** (n=50)
- **Judge by mode:** {'?': 1.54} (grounded=raft/context vs closed_book=recall)

**Fixed sample generations:**

- *Q:* What is the standard of proof in a civil lawsuit?
  *A:* A civil action is a civil action for the recovery of money, which is generally a civil action for the recovery of money.
- *Q:* Summarize what a 10-K annual report contains.
  *A:* Summarize a 10-K annual report for the year ended December 31, 1998.
- *Q:* What does it mean for a contract clause to be severable?
  *A:* The contract clause must be severable, and the remainder of the contract must be severable.

## 7. Modal runtime

- Train wall: **798.4s** · total wall: 835.0s · container: 854.3s
- Peak GPU mem: **13.99 GB** · throughput: 2266.1 supervised tok/s · supervised tokens: 1,809,369
- **Cost: ~$0.19** (L4 @ $0.8/hr) · teacher $0 (free tier)
