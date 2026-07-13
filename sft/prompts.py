"""Teacher prompt builders + user-instruction templates for SFT QnA synthesis.

Design (validated during Phase 3 setup):
- QA is the only task with a closed-book / RAFT distinction:
    * closed_book -> training example is (question -> answer); teaches knowledge into weights.
    * raft        -> training example is (context + question -> answer|"not stated"); teaches
                     answer-from-context behavior. Some RAFT questions are deliberately
                     unanswerable from the passage (refusal targets).
- summarize / extract / rewrite inherently carry the source text in the USER turn (you cannot
  summarize text the model cannot see), so they are "context" mode by nature.

Every teacher call returns strict JSON (enforced by response_schema in teacher.py). These
builders only produce the prompt text.
"""

from __future__ import annotations

import random

NOT_STATED = "not stated in the context"

# --- QA (answerable, grounded) -------------------------------------------------------

def qa_answerable(passage: str, n: int) -> str:
    return (
        "You are creating supervised fine-tuning data for a legal and financial assistant.\n"
        f"Read the PASSAGE and write {n} diverse, high-quality question-answer pairs whose "
        "answers are stated ONLY in the passage.\n"
        "Rules:\n"
        "- Vary difficulty: mix easy factual lookups with harder multi-step or reasoning questions.\n"
        "- Each answer must be fully self-contained and MUST NOT reference 'the passage', "
        "'the text', 'the document', or 'above'.\n"
        "- Do NOT invent facts that are not supported by the passage.\n"
        "- Questions must be answerable without seeing the passage (they should carry their own "
        "context, e.g. name the company/case/topic).\n"
        "- No duplicate or near-duplicate questions.\n\n"
        f"PASSAGE:\n{passage}"
    )


def qa_unanswerable(passage: str, n: int) -> str:
    return (
        "You are creating RAFT-style training data that teaches a model to refuse when the "
        f"answer is absent. Read the PASSAGE and write {n} on-topic questions that are NOT "
        "answerable from the passage (the specific fact is genuinely absent).\n"
        "Rules:\n"
        "- Plausible and on-topic, but the passage does not contain the answer.\n"
        "- Do not write trivially unrelated questions.\n"
        "- The 'answer' field for every item must be exactly: "
        f"\"{NOT_STATED}\".\n\n"
        f"PASSAGE:\n{passage}"
    )


# --- Evol-Instruct: evolve a subset of QA into harder questions ----------------------

def qa_evolve(passage: str, base_question: str) -> str:
    return (
        "Evolve the QUESTION into a single harder version by adding a constraint, an edge case, "
        "or a multi-step reasoning requirement — while keeping it answerable ONLY from the "
        "PASSAGE. Return one JSON object with the harder 'question', its grounded 'answer', and "
        "\"difficulty\": \"hard\". The answer must be self-contained.\n\n"
        f"PASSAGE:\n{passage}\n\nQUESTION: {base_question}"
    )


# --- summarize / extract / rewrite (context in user turn) ----------------------------

def task_output(task: str, passage: str) -> str:
    """Teacher produces the grounded assistant OUTPUT for a context-bearing task."""
    if task == "summarize":
        return (
            "Summarize the following legal/financial text faithfully in 2-4 sentences. "
            "Include only information present in the text; add nothing. Return JSON with a "
            "single field 'answer' containing the summary.\n\nTEXT:\n" + passage
        )
    if task == "extract":
        return (
            "Extract the key structured facts from the following legal/financial text into a "
            "compact JSON object (e.g. parties, dates, amounts, entities, obligations — only "
            "fields actually present). Return JSON with a single field 'answer' whose value is "
            "the extracted JSON rendered as a string. Do not invent fields.\n\nTEXT:\n" + passage
        )
    if task == "rewrite":
        return (
            "Rewrite the following legal/financial text in clear, plain English for a "
            "non-expert, preserving all facts and meaning. Return JSON with a single field "
            "'answer' containing the rewrite.\n\nTEXT:\n" + passage
        )
    raise ValueError(f"unknown context task {task!r}")


# Varied user instructions paired with the passage for context-bearing tasks.
_INSTRUCTIONS = {
    "summarize": (
        "Summarize the following:",
        "Give a concise summary of this text:",
        "What are the key points below?",
        "Provide a brief summary of the following excerpt:",
    ),
    "extract": (
        "Extract the key facts from the following as JSON:",
        "Pull out the important structured details below as JSON:",
        "Identify the parties, dates, and amounts in this text as JSON:",
    ),
    "rewrite": (
        "Rewrite the following in plain English:",
        "Restate the text below in simple, clear language:",
        "Explain the following in everyday terms:",
    ),
}


def user_instruction(task: str, passage: str, rng: random.Random) -> str:
    """The USER-turn content for a context-bearing task: instruction + passage."""
    lead = rng.choice(_INSTRUCTIONS[task])
    return f"{lead}\n\n{passage}"


# --- Batched variants (amortize the 500 RPD budget: many passages per call) -----------

_TASK_VERB = {
    "summarize": ("Summarize each TEXT faithfully in 2-4 sentences, including only "
                  "information present in that text."),
    "extract": ("Extract the key structured facts from each TEXT into a compact JSON object "
                "(parties, dates, amounts, entities, obligations — only fields present) and "
                "render that JSON as a string."),
    "rewrite": ("Rewrite each TEXT in clear, plain English for a non-expert, preserving all "
                "facts and meaning."),
}


def task_output_batch(task: str, passages: list[str]) -> str:
    verb = _TASK_VERB[task]
    blocks = "\n\n".join(f"[TEXT {i}]\n{p}" for i, p in enumerate(passages))
    return (
        f"You are creating supervised fine-tuning data for a legal/financial assistant.\n{verb}\n"
        "Do NOT add facts not present in the corresponding text.\n"
        f"Return a JSON array of exactly {len(passages)} objects, each with 'index' (the TEXT "
        "number) and 'answer' (the result for that text).\n\n" + blocks
    )


def qa_unanswerable_batch(passages: list[str]) -> str:
    blocks = "\n\n".join(f"[TEXT {i}]\n{p}" for i, p in enumerate(passages))
    return (
        "You are creating RAFT refusal training data. For each TEXT, write ONE plausible, "
        "on-topic question whose answer is genuinely NOT contained in that text.\n"
        f"Return a JSON array of exactly {len(passages)} objects, each with 'index' (the TEXT "
        "number) and 'question'. Do not include an answer field.\n\n" + blocks
    )
