# SFT Run Report — Day 0 (BASELINE (base model, no training))

## 1. Run identity

- Day / dataset scale: **0** · train examples: **1000**
- GPU: **NVIDIA L4** (Modal L4) · device cuda
- Base checkpoint: `Ace-2504/slm-125m-base` (volume `slm-125m`)

## 2. Parameters

- Model: 12L/768d/12h, 125.8M params, ctx 1024, tied embeddings
- Fine-tune: **full FT** · epochs **0** · batch **16** · steps **0** (warmup 1)
- LR 3e-05 → 3e-06 cosine · wd 0.0 · seed 1337
- Loss: assistant-only masking · chat template with `<|user|>/<|assistant|>/<|system|>`
- Teacher (data): `gemini-3.1-flash-lite`

## 3. Dataset composition

- Train pairs: **1000** · by day: {1: 1000}
- Task: {'qa': 550, 'summarize': 200, 'extract': 150, 'rewrite': 100}
- Mode: {'raft': 133, 'closed_book': 417, 'context': 450}
- Domain: {'sec': 420, 'case-law': 352, 'fineweb-edu': 228}

## 4. Data loss / catastrophic forgetting

Retention perplexity on the **pretraining val set** (base = **11.35**):

- This run: **11.355** → vs base: **+0.0%** (negligible forgetting)
- vs previous (base model): 11.355 (↑ +0.005, +0.0%)

> A retention-ppl rise is partly expected (chat-distribution shift); this run's forgetting is **negligible**.

## 5. Perplexity comparison (vs previous checkpoint)

| Metric | This run (day 0) | Previous (base model) | Δ |
| --- | --- | --- | --- |
| SFT-eval perplexity | 24.437 | — | first run |
| Retention perplexity | 11.355 | 11.350 | +0.005 |

(SFT-eval ↓ = better task fit; retention ↑ = more forgetting.)

## 6. Task quality

- SFT-eval loss: **3.1961** (ppl 24.4367)
- Final train loss: None
- **Gemini-judge score: 1.0/5** (n=50)

**Fixed sample generations:**

- *Q:* What is the standard of proof in a civil lawsuit?
  *A:* missibleit is a term used to describe a process of determining the probability of a particular outcome. It is a term used to describe a process of determining the probability of a particular outcome. It is a term used to describe a process of determining the probability of a particular outcome. It i
- *Q:* Summarize what a 10-K annual report contains.
  *A:* missibleit is a term used to describe a process of producing a sample of a sample of a sample of a sample of a sample of a sample of a sample of a sample of a sample of a sample of a sample of a sample of a sample of a sample of a sample of a sample of a sample of a sample of a sample of a sample of
- *Q:* What does it mean for a contract clause to be severable?
  *A:* missibleit is a term used to describe a contract clause that is a term used to describe a contract clause that is a term used to describe a contract clause that is a term used to describe a contract clause that is a term used to describe a contract clause that is a term used to describe a contract c

## 7. Modal runtime

- Train wall: **0.0s** · total wall: 114.0s · container: 127.5s
- Peak GPU mem: **4.67 GB** · throughput: 0.0 supervised tok/s · supervised tokens: 0
- **Cost: ~$0.028** (L4 @ $0.8/hr) · teacher $0 (free tier)
