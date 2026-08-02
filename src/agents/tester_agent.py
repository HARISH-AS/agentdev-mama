"""
Tester Agent (multi-file).

Assembles the full set of files the sandbox needs: every file the
Developer Agent patched (backend + frontend), plus the existing test
files and pytest.ini from workspace/sample_project/ that WEREN'T
touched by the Developer Agent (it never edits tests). Only backend
files are actually exercised by pytest — frontend files are written
into the sandbox for completeness but nothing runs against them here;
they're human-reviewed at the Approval Agent step instead.
"""
from __future__ import annotations

from pathlib import Path

from config.logging_config import get_logger
from src.state import PipelineState, STATUS_FAILED, STATUS_PASSED, log_transition
from src.tools.docker_sandbox import run_in_sandbox

logger = get_logger(__name__)

_NODE_NAME = "tester_agent"

# MVP assumption: project root is workspace/sample_project/, tests live
# under tests/, and pytest.ini there sets pythonpath so tests can import
# from backend/. Adjust here if your repo layout differs — this is the
# one place that assumption lives.
_PROJECT_ROOT = Path("workspace/sample_project")
_TEST_DIR = _PROJECT_ROOT / "tests"
_PYTEST_INI = _PROJECT_ROOT / "pytest.ini"


def _collect_existing_test_files(patched_files: set[str]) -> dict[str, str]:
    """
    Read every test_*.py under tests/, plus pytest.ini if present, and
    key them by the SAME relative-path convention as patch_code (e.g.
    'tests/test_app.py', 'pytest.ini') so they land in the right spot
    inside the sandbox next to the patched backend/ files.
    """
    collected: dict[str, str] = {}

    if _TEST_DIR.exists():
        for test_file in _TEST_DIR.glob("test_*.py"):
            rel_path = f"tests/{test_file.name}"
            if rel_path in patched_files:
                continue  # Developer Agent shouldn't touch tests, but don't clobber if it did
            collected[rel_path] = test_file.read_text(encoding="utf-8")

    if _PYTEST_INI.exists():
        collected["pytest.ini"] = _PYTEST_INI.read_text(encoding="utf-8")

    return collected


def tester_agent_node(state: PipelineState) -> dict:
    iteration = state.get("iteration_count", 0)
    logger.info("Tester Agent starting (iteration %d)", iteration)

    patch_code = state.get("patch_code", {})
    if not patch_code:
        msg = "No patch_code produced by Developer Agent; cannot test"
        logger.error(msg)
        return {
            "test_results": {"passed": False, "output": msg},
            "status": STATUS_FAILED,
            "iteration_count": iteration + 1,
            "chain_of_thought": log_transition(state, _NODE_NAME, msg),
        }

    existing_tests = _collect_existing_test_files(set(patch_code.keys()))

    # A test file counts whether it already existed on disk (existing_tests)
    # OR the Developer Agent generated a new one this iteration (patch_code).
    # Previously this only checked existing_tests, so a freshly-generated
    # tests/test_*.py in patch_code was invisible to this guard and the
    # run was wrongly rejected as "no tests found" even though a real
    # test file was sitting right there in the patch.
    has_existing_test = any(k.startswith("tests/") for k in existing_tests)
    has_patched_test = any(
        k.startswith("tests/") and Path(k).name.startswith("test_")
        for k in patch_code
    )

    if not (has_existing_test or has_patched_test):
        msg = f"No test_*.py files found under {_TEST_DIR}; cannot verify patch"
        logger.error(msg)
        return {
            "test_results": {"passed": False, "output": msg},
            "status": STATUS_FAILED,
            "iteration_count": iteration + 1,
            "chain_of_thought": log_transition(state, _NODE_NAME, msg),
        }

    all_files = {**patch_code, **existing_tests}
    logger.debug("Sandbox file set: %s", list(all_files.keys()))

    result = run_in_sandbox(all_files)

    status = STATUS_PASSED if result["passed"] else STATUS_FAILED
    note = f"tests {'passed' if result['passed'] else 'failed'} (iteration {iteration})"

    return {
        "test_results": result,
        "status": status,
        "iteration_count": iteration + 1,
        "chain_of_thought": log_transition(state, _NODE_NAME, note),
    }