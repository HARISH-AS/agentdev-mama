# Agents

Each agent is a single function in `src/agents/`, taking the current `PipelineState` and returning a dict of updates. None of them call each other directly — `src/graph.py` owns all routing.

## Refiner Agent (`refiner_agent.py`)

**Input:** `raw_prompt`, and on a loop-back, `clarifying_answers`
**Output:** either `clarifying_questions` (if the spec is ambiguous) or `refined_prompt` (if it's ready to build)

Calls Ollama once, asks it to either emit up to 2 clarifying questions or a `FINAL:` spec line. To prevent an infinite clarification loop, the agent forces itself to finalize on the second pass regardless of how vague the answers were — `already_asked = bool(state.get("clarifying_answers"))` gates this.

**Known limitation:** this agent does not currently read the actual content of the target files — it only sees your typed prompt and the filenames. This means it sometimes asks questions a human could answer just by looking at the code (e.g. "what format is the data in?" when the data structure is sitting right there in `app.py`). Fixing this is tracked as a follow-up: feed each target file's current content into the Refiner's prompt, same way the Developer Agent already does.

## Developer Agent (`developer_agent.py`)

**Input:** `refined_prompt`, `target_files`, and on retry, the previous `test_results` + previous `patch_code`
**Output:** `patch_code` (a `{file_path: full_content}` dict)

Reads each target file's *current* content off disk before calling Ollama (on iteration 0) or reuses its own previous attempt (on retries, since that's what was actually tested and failed). The system prompt explicitly instructs the model to preserve everything not related to the requested change and never invent new data — this was added after an early run silently replaced a real 5-row dataset with 3 invented rows while "adding" an unrelated CSV export feature.

Output format is a series of `### FILE: <path>` headers each followed by a fenced code block; `_extract_files()` parses these back into the `patch_code` dict.

**Known gap:** no guardrail currently prevents the model from adding features beyond what was asked. One real run asked only for a background color change and got that plus an unrequested (and non-functional, since the backend was never updated to match) search box. The Approval Agent step is the only safety net for this today — read diffs carefully.

## Tester Agent (`tester_agent.py`)

**Input:** `patch_code`, plus whatever exists in `tests/` and `backend/` on disk
**Output:** `test_results`, `status` (`PASSED`/`FAILED`), incremented `iteration_count`

Assembles the full file set the sandbox needs: the patched files, the existing test files (which the Developer Agent never touches), `pytest.ini`, and — critically — any **unpatched** backend `.py` files, so a frontend-only run still has a complete, importable app to test against. This last part was a real bug fix: an early version only included files targeted in the current run, so a frontend-only patch would fail every test with `ModuleNotFoundError: No module named 'app'`, since the backend was never copied into the sandbox at all.

Delegates actual execution to `src/tools/docker_sandbox.py`.

**Known limitation:** only backend Python files are exercised by pytest. Frontend files (`.html`, `.js`) are written into the sandbox for path/import consistency but nothing runs against them — there is no automated frontend testing in this version by design (a deliberate scope decision, not an oversight).

## Approval Agent (`approval_agent.py`)

**Input:** everything generated so far
**Output:** `approved` (bool)

Prints the full spec, test output, and every patched file's complete content, then blocks on a real `input()` — `Approve this change and open a PR? [y/N]`. This is the one hard gate in the system: nothing reaches the PR Agent without this returning `True`.

## PR Agent (`pr_agent.py`)

**Input:** `patch_code`, `approved`
**Output:** `pr_url`

Only runs if `approved` is `True` (enforced by `graph.py`'s `approval_router`, not by this agent itself). Asks at runtime whether to:
- **Write locally only** — plain file writes to `workspace/sample_project/`, no git involved. Always works, no setup required.
- **Push a real GitHub PR** — commits via `src/tools/git_tool.py`, pushes a new branch, opens a PR via PyGithub. Requires `GITHUB_TOKEN`, `REPO_OWNER`, `REPO_NAME` in `.env`, and the repo to actually exist with a `main` branch already pushed. Falls back to local-only with a warning if these aren't configured.

## Cross-cutting: `chain_of_thought`

Every agent calls `src.state.log_transition()` instead of building its own log entry, which does two things at once: writes a structured log line (via `config/logging_config.py`) and appends a human-readable string to `state["chain_of_thought"]`. `main.py` prints this list at the end of every run — it's the fastest way to see what actually happened without scrolling through timestamped logs.
