"""
Refiner Agent.

Takes the human's raw_prompt (and, on loop-back, any clarifying_answers
already collected) and either:
  (a) emits clarifying_questions if the spec is too vague to code against, or
  (b) emits a refined_prompt precise enough for the Developer Agent to act on.

This node is deliberately conservative: it only asks for clarification
once (checked via refined_prompt / clarifying_answers state), so the
refiner<->ask_human loop in graph.py can't spin forever on a chatty model.
"""
from __future__ import annotations

from langchain_ollama import ChatOllama

from config.logging_config import get_logger
from config.settings import settings
from src.state import PipelineState, log_transition

logger = get_logger(__name__)

_NODE_NAME = "refiner_agent"

_SYSTEM_PROMPT = """You are the Refiner Agent in an autonomous coding pipeline.
Your only job is to turn a human's raw feature request into a precise,
unambiguous engineering spec for a single file edit.

Rules:
- If the request is missing information you truly cannot proceed without
  (e.g. which file, what the exact behavior should be), output up to 2
  short clarifying questions, one per line, each starting with "Q: ".
- If the request is already clear enough to implement, do NOT ask
  questions. Instead output a single refined spec starting with "FINAL: "
  followed by a precise, implementation-ready description.
- Never do both. Output either questions or a FINAL line, nothing else.
"""


def _build_human_turn(state: PipelineState) -> str:
    parts = [f"Raw request: {state['raw_prompt']}"]
    if state.get("clarifying_questions") and state.get("clarifying_answers"):
        qa_pairs = zip(state["clarifying_questions"], state["clarifying_answers"])
        parts.append("Previous clarifications:")
        for q, a in qa_pairs:
            parts.append(f"  Q: {q}\n  A: {a}")
    return "\n".join(parts)


def refiner_agent_node(state: PipelineState) -> dict:
    logger.info("Refiner Agent starting")

    # If we already collected answers, don't ask again — force finalization.
    already_asked = bool(state.get("clarifying_answers"))

    llm = ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0.0,
    )

    human_turn = _build_human_turn(state)
    if already_asked:
        human_turn += "\n\nYou already asked clarifying questions and got answers above. You MUST output a FINAL: line now, no more questions."

    response = llm.invoke(
        [
            ("system", _SYSTEM_PROMPT),
            ("human", human_turn),
        ]
    )
    text = response.content.strip()
    logger.debug("Refiner raw output: %s", text)

    questions = [
        line[3:].strip()
        for line in text.splitlines()
        if line.strip().upper().startswith("Q:")
    ]

    if questions and not already_asked:
        note = f"asked {len(questions)} clarifying question(s)"
        return {
            "clarifying_questions": questions,
            "chain_of_thought": log_transition(state, _NODE_NAME, note),
        }

    final_line = next(
        (line for line in text.splitlines() if line.strip().upper().startswith("FINAL:")),
        None,
    )
    refined_prompt = final_line[6:].strip() if final_line else text

    if not refined_prompt:
        # Defensive fallback: never hand an empty spec to the Developer Agent.
        refined_prompt = state["raw_prompt"]
        logger.warning("Refiner produced no usable output; falling back to raw_prompt")

    return {
        "clarifying_questions": [],
        "refined_prompt": refined_prompt,
        "chain_of_thought": log_transition(state, _NODE_NAME, "spec refined, ready for developer"),
    }