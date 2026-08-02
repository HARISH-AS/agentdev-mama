"""
AgentDEV-MAMA entry point.

Usage:
    python main.py
"""
from __future__ import annotations

from config.logging_config import get_logger
from config.settings import settings
from src.graph import build_graph
from src.state import new_initial_state

logger = get_logger(__name__)


def main() -> None:
    raw_prompt = input(
        "Describe the change you want (e.g. 'add a download button that exports the table as CSV'): "
    ).strip()
    target_files_raw = input(
        "Target files, comma-separated, relative to workspace/sample_project/ "
        "(e.g. backend/app.py, frontend/index.html): "
    ).strip()
    target_files = [f.strip() for f in target_files_raw.split(",") if f.strip()]

    state = new_initial_state(
        raw_prompt=raw_prompt,
        target_files=target_files,
        max_iterations=settings.MAX_ITERATIONS,
    )

    graph = build_graph()
    logger.info("Invoking pipeline")
    final_state = graph.invoke(state)

    print("\n" + "=" * 60)
    print("PIPELINE FINISHED")
    print("=" * 60)
    print(f"Status : {final_state.get('status')}")
    print(f"PR URL : {final_state.get('pr_url')}")

    test_results = final_state.get("test_results")
    if test_results:
        print("\nLast test output:")
        print(test_results.get("output", "(no output captured)"))

    print("\nChain of thought:")
    for line in final_state.get("chain_of_thought", []):
        print(f"  - {line}")


if __name__ == "__main__":
    main()