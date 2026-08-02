"""
Graph construction for the AgentDEV-MAMA pipeline.

Flow:
    refiner --(needs clarification)--> ask_human --> refiner (loop)
    refiner --(spec is clear)-------> developer --> tester
    tester  --(failed, retries left)-> developer
    tester  --(failed, out of retries)-> END
    tester  --(passed)----------------> approval
    approval --(human said yes)-------> pr_agent --> END
    approval --(human said no)--------> END

This module only handles routing/wiring. Agent logic lives in
src/agents/*.py so each agent can be developed, tested, and swapped
independently (per the project's modularity principle).
"""
from __future__ import annotations

from typing import Literal

from langgraph.graph import END, StateGraph

from config.logging_config import get_logger
from src.state import PipelineState, STATUS_PASSED

logger = get_logger(__name__)

# NOTE: these imports will start resolving once the corresponding agent
# files are implemented. Left as-is (matching the approved MVP spec)
# rather than stubbed, so nothing silently diverges from the plan.
from src.agents.refiner_agent import refiner_agent_node
from src.agents.developer_agent import developer_agent_node
from src.agents.tester_agent import tester_agent_node
from src.agents.approval_agent import approval_agent_node
from src.agents.pr_agent import pr_agent_node


def refiner_router(state: PipelineState) -> Literal["ask_human", "developer"]:
    """After the Refiner Agent runs: if it produced clarifying questions,
    go collect answers from the human; otherwise the spec is precise
    enough to hand to the Developer Agent."""
    if state.get("clarifying_questions"):
        logger.info(
            "Refiner router -> ask_human (%d question(s) pending)",
            len(state["clarifying_questions"]),
        )
        return "ask_human"
    logger.info("Refiner router -> developer (spec is clear)")
    return "developer"


def tester_router(state: PipelineState) -> Literal["developer", "approval", "END"]:
    """After the Tester Agent runs: route to approval on pass, back to
    the Developer Agent on failure (up to max_iterations), or bail out
    once retries are exhausted."""
    status = state.get("status")
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 3)

    if status == STATUS_PASSED:
        logger.info("Tester router -> approval (tests passed)")
        return "approval"

    if iteration_count >= max_iterations:
        logger.warning(
            "Tester router -> END (max_iterations=%d reached, giving up)",
            max_iterations,
        )
        return "END"

    logger.info(
        "Tester router -> developer (retry %d/%d)",
        iteration_count + 1,
        max_iterations,
    )
    return "developer"


def approval_router(state: PipelineState) -> Literal["pr_agent", "END"]:
    """After the human Approval Agent runs: only proceed to the PR Agent
    on explicit approval. This is the one hard rule in the whole system —
    no path to pr_agent skips this check."""
    if state.get("approved"):
        logger.info("Approval router -> pr_agent (human approved)")
        return "pr_agent"
    logger.info("Approval router -> END (human declined)")
    return "END"


def ask_human_node(state: PipelineState) -> dict:
    """Collect answers to the Refiner Agent's clarifying questions
    directly from the terminal, then loop back to the refiner so it can
    fold the answers into a refined_prompt."""
    answers = []
    for q in state["clarifying_questions"]:
        a = input(f"[Refiner Agent] {q}\n> ")
        answers.append(a)
    logger.debug("Collected %d clarifying answer(s) from human", len(answers))
    return {"clarifying_answers": state.get("clarifying_answers", []) + answers}


def build_graph():
    """Assemble and compile the LangGraph state machine described in the
    module docstring. Call this once per run from main.py."""
    logger.info("Building pipeline graph")
    g = StateGraph(PipelineState)

    g.add_node("refiner", refiner_agent_node)
    g.add_node("ask_human", ask_human_node)
    g.add_node("developer", developer_agent_node)
    g.add_node("tester", tester_agent_node)
    g.add_node("approval", approval_agent_node)
    g.add_node("pr_agent", pr_agent_node)

    g.set_entry_point("refiner")

    g.add_conditional_edges(
        "refiner",
        refiner_router,
        {"ask_human": "ask_human", "developer": "developer"},
    )
    g.add_edge("ask_human", "refiner")  # loop back with answers until FINAL:
    g.add_edge("developer", "tester")
    g.add_conditional_edges(
        "tester",
        tester_router,
        {"developer": "developer", "approval": "approval", "END": END},
    )
    g.add_conditional_edges(
        "approval",
        approval_router,
        {"pr_agent": "pr_agent", "END": END},
    )
    g.add_edge("pr_agent", END)

    compiled = g.compile()
    logger.info("Pipeline graph compiled successfully")
    return compiled