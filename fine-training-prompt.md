# Fine-Tuning Prompt — SLM-125M Supervised Fine-Tuning

> This file captures the founding instructions for the SFT project on top of
> `Ace-2504/slm-125m-base`. It is the source-of-truth brief; the plan, dataset,
> and training phases all descend from it.

## Instructions

1. **No implementation, only discussion** (during the current phase).
2. Save this text as a file into the repository as `fine-training-prompt.md`.
3. Claude acts as the **best AI fine-tuning engineer and researcher**.
4. This will be implemented in **4 phases**:
   1. **Discussion** (current phase)
   2. **Plan**
   3. **Make the QnA pairs**
   4. **Actually fine-tuning** (last phase)
5. This model will be trained via **supervised fine-tuning (SFT)** using the
   **Gemini 2.5 Flash** model as its **teacher** — it will generate the QnA pairs.
6. The dataset used to generate the QnA pairs should be **the same dataset as in
   this repository** (the pretraining corpus: US case law, SEC filings,
   educational web text).
7. The QnA dataset must be **high quality, high diversity, and free of duplicate
   QnA pairs** (follow the approach at https://slm-finetuning-data.vercel.app/).
   The **size** of the QnA set depends on the **cost** to fine-tune on Modal —
   Claude should suggest the **optimal number of QnA pairs and the associated
   cost**.
8. Training will be done on **Modal** (already set up), **not** the local machine.
9. For fine-tuning on Modal, Claude will suggest the **optimal GPU cluster** —
   it is **not** mandatory to match the pre-training setup.
10. This fine-tuning is to be treated as a **research project**. Claude will note
    **every single detail** from the Modal interface (e.g. the referenced Modal
    run artifact) and any other relevant information used to conduct the
    experiment. An **observations write-up** (like
    https://ace-2504.github.io/slm-125m-observations/) will be produced **later**
    — not now, but noted as upcoming.
11. Claude will **ask every single question** it has regarding this prompt.

## Reference material

- QnA data-quality methodology: https://slm-finetuning-data.vercel.app/
- Prior pre-training observations (style reference for the later write-up):
  https://ace-2504.github.io/slm-125m-observations/
- Modal run interface artifact (research logging reference): captured per run.

## Phase tracker

- [x] Phase 1 — Discussion
- [x] Phase 2 — Plan (see `fine-tuning-plan.md`)
- [x] Phase 3 — QnA pair generation (`sft/gen_qa.py`, `build_dataset.py`; 10,000 pairs generated)
- [x] Phase 4 — Fine-tuning on Modal (11 runs, `sft/reports/run-00…10`)

**All four phases complete.** The v1 study ran 10 rounds (0 → 10,000 pairs) and closed as a clean
negative result: scaling SFT data 10× did not improve answer quality (judge flat at ~1.5/5) and
tripled catastrophic forgetting (+6.1% → +16.3%). See `sft/research_log.md`,
`sft/training-feedback/day10.md`, and the published write-up:
https://ace-2504.github.io/fine-tuned-125m-slm/

Follow-on (not part of the original 4 phases): **v2** grounded-heavy pivot — shipped and parked
(`sft/training-feedback/v2-pivot.md`).
