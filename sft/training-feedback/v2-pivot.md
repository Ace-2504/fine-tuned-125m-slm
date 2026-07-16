# Decision — Switching to the v2 Pivot

**Date:** 2026-07-15 · **Trigger:** Day-3 plateau (see `day1.md`, `day2.md`, `../research_log.md`).

## Why

The v1 scaling study (Days 1–3, closed-book-heavy mix) reached a clean, honest conclusion:
the answer-quality judge **plateaus at ~1.5/5** while perplexity keeps inching down and
catastrophic forgetting keeps climbing (+6.1% → +9.5% → +11.0%, now "notable").

| Day | Pairs | SFT-eval ppl | Retention (Δ base) | Judge /5 |
| --- | --- | --- | --- | --- |
| 1 | 1,000 | 8.60 | +6.1% | 1.32 |
| 2 | 2,000 | 8.00 | +9.5% | 1.50 |
| 3 | 3,000 | 7.70 | +11.0% | 1.46 |

Root cause (from `day1.md`/`day2.md`): most training is **closed-book QA** — recall a document
fact from a single exposure, which a 125M model largely cannot do. More data buys distribution
fit and forgetting, not answer quality.

## What v2 changes

1. **Grounded-heavy mix** — flip QA to mostly **RAFT** (context in the prompt) and increase the
   share of context tasks (summarize / extract / rewrite). Closed-book QA is kept only for
   **general-knowledge** (fineweb-edu) passages. Target: ~90%+ of training on tasks the model can
   actually learn.
   - v1: mode {closed_book .80, raft .20}, task {qa .55, sum .20, ext .15, rew .10}
   - v2: mode {closed_book .15, raft .85}, task {qa .40, sum .25, ext .20, rew .15},
     closed-book sources = {fineweb-edu} only.
2. **Per-mode judge** — score grounded vs closed-book questions **separately**, so the metric
   reflects what the model can do instead of being dominated by the unlearnable recall task.
3. **Decoding fix** — `no_repeat_ngram_size=3` + `repetition_penalty=1.3` for eval/sample
   generations (removes greedy repetition loops). Applied to v2 only, to preserve v1's internal
   comparability.
4. **Replay (deferred):** mix a little raw pretraining data into SFT to bound forgetting — held in
   reserve; v2's grounded mix may forget less on its own. Add only if retention still climbs.

## How v1 stays intact (and Day-4 stays open)

v2 runs on a **separate track** via `SFT_TRACK=v2`, with its own namespaces — nothing v1 is
touched or overwritten:

| | v1 (default) | v2 (`SFT_TRACK=v2`) |
| --- | --- | --- |
| local data | `data/sft/` | `data/sft-v2/` |
| reports | `sft/reports/` | `sft/reports-v2/` |
| Modal app | `slm-125m-sft` | `slm-125m-sft-v2` |
| volume data | `/sft/` | `/sft-v2/` |
| checkpoints | `/checkpoints/sft/` | `/checkpoints/sft-v2/` |
| mix / decoding | original | grounded-heavy / rep-penalty |

**v1 Day 4 remains one command away** — a bare run (default track) continues v1 from its saved
state (`gen_state` last_day = 3 → Day 4) with the original mix and greedy decoding, fully
comparable to v1 Days 1–3. This option is preserved indefinitely.

## Status

- v1: **paused at Day 3** (plateau documented). Day-4 option kept open.
- v2: **starting fresh at Day 1** with the grounded-heavy design above.
