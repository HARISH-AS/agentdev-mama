"""
PipelineState: the shared state dict passed between every node in the
LangGraph state machine (Refiner -> Developer -> Tester -> Approval -> PR).

Keeping this in one typed dict, rather than scattering ad-hoc dicts
across agents, is what lets each agent be replaced independently
(e.g. swapping the Developer Agent's local Ollama call for a Claude Code
invocation later) without touching the graph wiring or any other agent.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict

from config.logging_config import get_logger

logger = get_logger(__name__)

# Allowed values for PipelineState.status
STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_PASSED = "PASSED"
STATUS_FAILED = "FAILED"

VALID_STATUSES = {STATUS_IN_PROGRESS, STATUS_PASSED, STATUS_FAILED}


class PipelineState(TypedDict):
    # --- Input ---
    raw_prompt: str

    # --- Refiner Agent output ---
    clarifying_questions: List[str]
    clarifying_answers: List[str]
    refined_prompt: str

    # --- Developer Agent output ---
    target_files: List[str]           # relative paths, e.g. ["backend/app.py", "frontend/index.html"]
    patch_code: Dict[str, str]        # target_file -> full new file content
    explanation: str

    # --- Tester Agent output ---
    test_results: Optional[Dict[str, Any]]
    status: str  # one of VALID_STATUSES
    iteration_count: int
    max_iterations: int

    # --- Approval Agent output ---
    approved: Optional[bool]

    # --- PR Agent output ---
    pr_url: Optional[str]

    # --- Cross-cutting ---
    chain_of_thought: List[str]


def new_initial_state(
    raw_prompt: str,
    target_files: List[str],
    max_iterations: int = 3,
) -> PipelineState:
    """
    Build a fresh, fully-populated PipelineState for main.py to hand to
    graph.invoke(). Centralizing this avoids partially-initialized state
    dicts (missing keys cause KeyError deep inside a node, which is a
    painful thing to debug at 11pm).
    """
    logger.debug(
        "Creating initial state: target_files=%s max_iterations=%d",
        target_files,
        max_iterations,
    )
    return PipelineState(
        raw_prompt=raw_prompt,
        clarifying_questions=[],
        clarifying_answers=[],
        refined_prompt="",
        target_files=target_files,
        patch_code={},
        explanation="",
        test_results=None,
        status=STATUS_IN_PROGRESS,
        iteration_count=0,
        max_iterations=max_iterations,
        approved=None,
        pr_url=None,
        chain_of_thought=[],
    )


def log_transition(state: PipelineState, node_name: str, note: str) -> List[str]:
    """
    Append a chain_of_thought entry and mirror it to the logger, so the
    same trace shows up both in the printed run summary (chain_of_thought)
    and in structured logs (for later Phase-2 telemetry / DuckDB queries).
    Every agent should call this instead of building the log list by hand.
    """
    logger.info("[%s] %s", node_name, note)
    return state.get("chain_of_thought", []) + [f"{node_name}: {note}"]