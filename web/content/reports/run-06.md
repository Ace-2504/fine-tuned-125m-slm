# SFT Run Report — Day 6 (SFT run)

## 1. Run identity

- Day / dataset scale: **6** · train examples: **5999**
- GPU: **NVIDIA L4** (Modal L4) · device cuda
- Base checkpoint: `Ace-2504/slm-125m-base` (volume `slm-125m`)

## 2. Parameters

- Model: 12L/768d/12h, 125.8M params, ctx 1024, tied embeddings
- Fine-tune: **full FT** · epochs **3** · batch **16** · steps **1125** (warmup 56)
- LR 3e-05 → 3e-06 cosine · wd 0.0 · seed 1337
- Loss: assistant-only masking · chat template with `<|user|>/<|assistant|>/<|system|>`
- Teacher (data): `gemini-3.1-flash-lite`

## 3. Dataset composition

- Train pairs: **5999** · by day: {1: 853, 2: 1039, 3: 1031, 4: 1025, 5: 1039, 6: 1012}
- Task: {'extract': 899, 'summarize': 1200, 'qa': 3300, 'rewrite': 600}
- Mode: {'context': 2699, 'closed_book': 2448, 'raft': 852}
- Domain: {'sec': 2604, 'fineweb-edu': 1313, 'case-law': 2082}
- Generation (day 6): 345 requests, 1725 raw pairs, tok in/out 474475/162612, $0 (free tier)

## 4. Data loss / catastrophic forgetting

Retention perplexity on the **pretraining val set** (base = **11.35**):

- This run: **12.954** → vs base: **+14.1%** (notable forgetting)
- vs previous (run-05): 12.954 (↑ +0.057, +0.4%)

> A retention-ppl rise is partly expected (chat-distribution shift); this run's forgetting is **notable**.

## 5. Perplexity comparison (vs previous checkpoint)

| Metric | This run (day 6) | Previous (run-05) | Δ |
| --- | --- | --- | --- |
| SFT-eval perplexity | 7.279 | 7.3661 | -0.087 |
| Retention perplexity | 12.954 | 12.897 | +0.057 |

(SFT-eval ↓ = better task fit; retention ↑ = more forgetting.)

## 6. Task quality

- SFT-eval loss: **1.985** (ppl 7.2792)
- Final train loss: 1.7076669931411743
- **Gemini-judge score: 1.54/5** (n=50)
- **Judge by mode:** {'?': 1.54} (grounded=raft/context vs closed_book=recall)

**Fixed sample generations:**

- *Q:* What is the standard of proof in a civil lawsuit?
  *A:* The standard of proof in a civil lawsuit is the preponderance of the evidence standard.
- *Q:* Summarize what a 10-K annual report contains.
  *A:* Summarize the report to include a 10-K annual report.
- *Q:* What does it mean for a contract clause to be severable?
  *A:* The contract clause must be construed as a whole, and if it is not severable, it must be construed as a whole.

## 7. Modal runtime

- Train wall: **495.9s** · total wall: 534.4s · container: 549.0s
- Peak GPU mem: **13.78 GB** · throughput: 2196.5 supervised tok/s · supervised tokens: 1,089,366
- **Cost: ~$0.122** (L4 @ $0.8/hr) · teacher $0 (free tier)
