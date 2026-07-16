# SFT Run Report — Day 7 (SFT run)

## 1. Run identity

- Day / dataset scale: **7** · train examples: **6999**
- GPU: **NVIDIA L4** (Modal L4) · device cuda
- Base checkpoint: `Ace-2504/slm-125m-base` (volume `slm-125m`)

## 2. Parameters

- Model: 12L/768d/12h, 125.8M params, ctx 1024, tied embeddings
- Fine-tune: **full FT** · epochs **3** · batch **16** · steps **1314** (warmup 65)
- LR 3e-05 → 3e-06 cosine · wd 0.0 · seed 1337
- Loss: assistant-only masking · chat template with `<|user|>/<|assistant|>/<|system|>`
- Teacher (data): `gemini-3.1-flash-lite`

## 3. Dataset composition

- Train pairs: **6999** · by day: {1: 844, 2: 1017, 3: 1055, 4: 1041, 5: 1010, 6: 1003, 7: 1029}
- Task: {'summarize': 1400, 'qa': 3850, 'extract': 1049, 'rewrite': 700}
- Mode: {'context': 3149, 'closed_book': 2900, 'raft': 950}
- Domain: {'sec': 3038, 'fineweb-edu': 1532, 'case-law': 2429}
- Generation (day 7): 345 requests, 1725 raw pairs, tok in/out 471213/159553, $0 (free tier)

## 4. Data loss / catastrophic forgetting

Retention perplexity on the **pretraining val set** (base = **11.35**):

- This run: **13.004** → vs base: **+14.6%** (notable forgetting)
- vs previous (run-06): 13.004 (↑ +0.050, +0.4%)

> A retention-ppl rise is partly expected (chat-distribution shift); this run's forgetting is **notable**.

## 5. Perplexity comparison (vs previous checkpoint)

| Metric | This run (day 7) | Previous (run-06) | Δ |
| --- | --- | --- | --- |
| SFT-eval perplexity | 7.199 | 7.2792 | -0.080 |
| Retention perplexity | 13.004 | 12.954 | +0.050 |

(SFT-eval ↓ = better task fit; retention ↑ = more forgetting.)

## 6. Task quality

- SFT-eval loss: **1.974** (ppl 7.1994)
- Final train loss: 2.4048001766204834
- **Gemini-judge score: 1.6/5** (n=50)
- **Judge by mode:** {'?': 1.6} (grounded=raft/context vs closed_book=recall)

**Fixed sample generations:**

- *Q:* What is the standard of proof in a civil lawsuit?
  *A:* The standard of proof in a civil lawsuit is the preponderance of the evidence.
- *Q:* Summarize what a 10-K annual report contains.
  *A:* Summarize a 10-K annual report for the year.
- *Q:* What does it mean for a contract clause to be severable?
  *A:* The clause is severable from the other provisions of the contract, and the remainder of the contract is severable.

## 7. Modal runtime

- Train wall: **565.2s** · total wall: 607.7s · container: 626.7s
- Peak GPU mem: **13.74 GB** · throughput: 2242.4 supervised tok/s · supervised tokens: 1,267,506
- **Cost: ~$0.139** (L4 @ $0.8/hr) · teacher $0 (free tier)
