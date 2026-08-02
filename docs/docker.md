# Docker Sandbox

## Why Docker is here at all

The Developer Agent is an LLM writing code that nobody has reviewed yet — review happens later, at the Approval Agent step. Between generation and review, that code needs to be *executed* (to run its tests), and running unreviewed, LLM-generated code directly on the host machine is a bad idea regardless of how good the model is. Docker exists in this project for exactly one job: give that code somewhere disposable and isolated to run.

**Docker is not used for the pipeline's own dependencies.** `langgraph`, `langchain-ollama`, `PyGithub`, etc. all live in your local Python venv, installed via `pip install -r requirements.txt`, same as any normal project. Nothing about the pipeline's own code ever runs inside a container.

| Layer | Where it runs | Installed via |
|---|---|---|
| Pipeline itself (agents, LangGraph, Ollama client) | Local venv | `requirements.txt` |
| Code being tested (patched `app.py`, `index.html`, tests) | Disposable Docker container | Fresh `pip install pytest flask` per test run |

## How it works (`src/tools/docker_sandbox.py`)

1. `run_in_sandbox(files)` writes the full file set (patched files + existing tests + any unpatched backend files) into a temp directory, preserving relative paths
2. If Docker is reachable, spins up a `python:3.11-slim` container with that temp directory mounted at `/workspace`
3. Runs `pip install --quiet pytest flask && pytest -q /workspace` inside it
4. Waits for the real exit code (`container.wait()`), pulls the full combined stdout+stderr via `container.logs()`, then removes the container
5. Returns `{"passed": exit_code == 0, "output": <full log text>}`

### Why exit code, not string matching

An earlier version tried to infer pass/fail by checking whether the word "error" or "failed" appeared anywhere in the container's output. This was fragile in both directions — pip's own harmless warnings (like the "running pip as root" notice) could false-positive as a failure, and there was no reliable way to distinguish "the container itself errored" from "pytest ran fine and correctly reported one failing test." The current version uses the container's actual process exit code, which is the same signal your terminal would show you if you ran `pytest` yourself.

## Local fallback

If the Docker daemon isn't reachable (`docker.from_env().ping()` fails), `run_in_sandbox()` falls back to running `pytest` as a local subprocess instead of failing outright. This keeps the pipeline usable for quick iteration when Docker Desktop isn't running.

**This means the isolation guarantee only holds when Docker is actually up.** In fallback mode, generated code runs directly on the host, same as running pytest by hand. This is a known, accepted tradeoff for development convenience — not something to rely on for anything beyond local iteration.

## Verifying Docker itself works

Quick sanity check, independent of the pipeline, useful when debugging test failures that might actually be infrastructure issues rather than code bugs:

```powershell
docker run --rm python:3.11-slim sh -c "pip install --quiet pytest flask && echo INSTALL_OK"
```

If this prints `INSTALL_OK`, Docker has working internet access and can install packages — any sandbox test failures are therefore about the actual code, not the container environment.
