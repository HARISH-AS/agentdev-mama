"""
Approval Agent.

The one hard rule in the whole system: nothing reaches the PR Agent
without an explicit human "yes" here. Prints a summary of what the
Developer Agent built and what the Tester Agent confirmed, then asks.
"""
from __future__ import annotations

from config.logging_config import get_logger
from src.state import PipelineState, log_transition

logger = get_logger(__name__)

_NODE_NAME = "approval_agent"


def approval_agent_node(state: PipelineState) -> dict:
    logger.info("Approval Agent starting")

    print("\n" + "=" * 60)
    print("APPROVAL REQUIRED")
    print("=" * 60)
    print(f"Target files : {', '.join(state['target_files'])}")
    print(f"Spec         : {state['refined_prompt']}")
    print(f"Explanation  : {state.get('explanation', '')}")
    print(f"Test output  :\n{state.get('test_results', {}).get('output', '')}")
    print("-" * 60)
    for path, code in state.get("patch_code", {}).items():
        print(f"--- {path} ---")
        print(code)
        print()
    print("=" * 60)
    print(
        "NOTE: frontend file(s) above have NO automated test in this MVP — "
        "review them by eye before approving."
    )

    answer = input("Approve this change and open a PR? [y/N]: ").strip().lower()
    approved = answer in ("y", "yes")

    note = "human approved" if approved else "human declined"
    return {
        "approved": approved,
        "chain_of_thought": log_transition(state, _NODE_NAME, note),
    }