"""
Developer Agent (multi-file).

Reads the refined_prompt and target_files list, and produces patch_code
as a {file_path: full_content} dict — one entry per target file. This
lets a single feature request (e.g. "add a download button") span both
a backend route and a frontend change in one coordinated pass, so the
model can see all target files' context together and keep things like
route URLs consistent between them.

No automated test exists for frontend changes in this MVP — only
backend files get verified by the Tester Agent. Frontend output here is
still human-reviewed at the Approval Agent gate before anything merges.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

from langchain_ollama import ChatOllama

from config.logging_config import get_logger
from config.settings import settings
from src.state import PipelineState, log_transition

logger = get_logger(__name__)

_NODE_NAME = "developer_agent"

_PROJECT_ROOT = Path("workspace/sample_project")

_SYSTEM_PROMPT = """You are the Developer Agent in an autonomous coding pipeline.
You EDIT existing files based on a spec. You are shown each target file's
CURRENT content below. Treat that as the source of truth.

Rules:
- Preserve all existing code, data, and behavior in each file EXACTLY as
  given, UNLESS the spec explicitly asks you to change that specific part.
  Do not invent new sample data, rename variables, or reformat code that
  the spec didn't ask you to touch.
- Add only what the spec asks for, in the most minimal way that fits the
  existing code style of each file.
- For EACH target file, output a section like this, in order:

### FILE: <exact relative path>
```
<full file content, including your edits>
```

- Each file's code block must be the COMPLETE file content after your
  edit, not a diff/snippet — but everything not related to the requested
  change must be byte-for-byte identical to what was shown to you.
- Keep behavior consistent across files (e.g. if the backend exposes a
  route at /export, the frontend must call exactly /export, not a
  different path).
- If told about a previous test failure, fix that specific issue without
  discarding unrelated existing code.
- Output nothing except the "### FILE:" sections and their code blocks.
"""


def _read_current_files(target_files: List[str]) -> Dict[str, str]:
    """Read each target file's current content off disk, if it exists,
    so the Developer Agent edits real code instead of guessing at it."""
    current: Dict[str, str] = {}
    for rel_path in target_files:
        full_path = _PROJECT_ROOT / rel_path
        if full_path.exists():
            current[rel_path] = full_path.read_text(encoding="utf-8")
        else:
            logger.info("Target file %s does not exist yet; will be created fresh", rel_path)
            current[rel_path] = ""
    return current


def _extract_files(raw_text: str, expected_files: List[str]) -> Dict[str, str]:
    """
    Parse '### FILE: <path>' sections followed by a fenced code block.
    Falls back to assigning the whole output to the first expected file
    if the model didn't follow the format (defensive, not the happy path).
    """
    pattern = re.compile(
        r"###\s*FILE:\s*(?P<path>\S+)\s*```(?:\w+)?\n(?P<code>.*?)```",
        re.DOTALL,
    )
    matches = pattern.finditer(raw_text)
    result: Dict[str, str] = {}
    for m in matches:
        path = m.group("path").strip()
        code = m.group("code").strip()
        result[path] = code

    missing = [f for f in expected_files if f not in result]
    if missing:
        logger.warning(
            "Developer Agent output missing expected file(s) %s; "
            "output may not have followed the '### FILE:' format",
            missing,
        )

    if not result and expected_files:
        logger.warning("No '### FILE:' sections found at all; using raw output for first target file")
        result[expected_files[0]] = raw_text.strip()

    return result


def developer_agent_node(state: PipelineState) -> dict:
    iteration = state.get("iteration_count", 0)
    target_files = state["target_files"]
    logger.info("Developer Agent starting (iteration %d, files=%s)", iteration, target_files)

    llm = ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0.1,
    )

    # On iteration 0, read fresh from disk. On retries, use the previous
    # iteration's patch_code as the "current" state to edit further,
    # since that's what actually got tested and failed.
    if iteration == 0:
        current_files = _read_current_files(target_files)
    else:
        current_files = state.get("patch_code", {}) or _read_current_files(target_files)

    files_dump = "\n\n".join(
        f"### FILE: {path}\nCurrent content:\n```\n{content}\n```"
        for path, content in current_files.items()
    )

    human_turn = (
        f"{files_dump}\n\n"
        f"Spec: {state['refined_prompt']}\n"
    )

    if iteration > 0 and state.get("test_results"):
        human_turn += (
            f"\nPrevious attempt failed. Test output:\n"
            f"{state['test_results'].get('output', 'unknown failure')}\n"
            f"Fix the issue above, keeping all files consistent with each other "
            f"and preserving everything not related to the failure."
        )

    response = llm.invoke(
        [
            ("system", _SYSTEM_PROMPT),
            ("human", human_turn),
        ]
    )
    patch_code = _extract_files(response.content, target_files)

    note = f"generated patch for {list(patch_code.keys())} (iteration {iteration})"
    return {
        "patch_code": patch_code,
        "explanation": f"Iteration {iteration}: implemented per spec across {len(patch_code)} file(s).",
        "chain_of_thought": log_transition(state, _NODE_NAME, note),
    }