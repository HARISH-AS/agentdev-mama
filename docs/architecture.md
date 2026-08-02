# Architecture

## Overview

AgentDEV-MAMA is a LangGraph state machine with five agent nodes and two human checkpoints. Each agent is a plain Python function that reads a shared `PipelineState` dict and returns a partial update to it — no agent calls another agent directly, and no agent knows the pipeline's overall shape. Routing between agents is handled entirely by `src/graph.py`, which is the only file that knows the full flow.

This separation is the core design decision: **agents are replaceable independently**. Swapping the Developer Agent's local Ollama call for, say, a Claude Code invocation later means editing one file — `graph.py`'s wiring and every other agent stay untouched.

## Flow

```
                    ┌─────────────┐
                    │   Refiner   │◄──────────┐
                    └──────┬──────┘            │
                           │                    │
              needs clarification?              │
                    │              │            │
                   yes            no            │
                    │              │            │
                    ▼              ▼            │
             ┌─────────────┐ ┌───────────┐      │
             │  ask_human  │ │ Developer │      │
             └──────┬──────┘ └─────┬─────┘      │
                    │              │            │
                    └──────────────┘            │
                    (loop back with answers) ────┘
                                   │
                                   ▼
                            ┌───────────┐
                            │  Tester   │
                            └─────┬─────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                 passed      failed, retries   failed, out
                    │           left            of retries
                    ▼             │                │
             ┌───────────┐        │                ▼
             │ Approval  │        │              END
             └─────┬─────┘        │
                    │              │
          ┌─────────┴────┐        │
          │              │        │
       approved       declined    │
          │              │        │
          ▼              ▼        │
   ┌───────────┐        END       │
   │ PR Agent  │                  │
   └─────┬─────┘                  │
          │                       │
          ▼                       │
         END ◄──────(developer)───┘
```

## Why a state machine, not a fixed pipeline

A linear pipeline (Refiner → Developer → Tester → done) can't represent two things this project needed on day one:

1. **Retries.** Generated code frequently fails tests on the first attempt. The Tester Agent needs to be able to route *backward* to the Developer Agent with the failure context attached, up to a bounded number of times (`max_iterations`, default 3), before giving up.
2. **Human-in-the-loop branching.** The Refiner Agent might need clarification, which means pausing for terminal input and looping back — a shape a simple sequential script handles awkwardly.

LangGraph's `StateGraph` with conditional edges (`add_conditional_edges`) maps directly onto both of these without hand-rolled control flow.

## Shared state (`src/state.py`)

Every agent reads and writes a single `PipelineState` TypedDict. Keeping one typed, centrally-defined state shape — rather than each agent inventing its own ad-hoc dict — means:
- No `KeyError` surprises deep inside a node from a missing key (`new_initial_state()` guarantees every key is populated from the start)
- Every field's purpose and owner is documented in one place
- `chain_of_thought` accumulates a human-readable trace across the whole run, independent of the structured logs

## Multi-file support

`target_files: List[str]` and `patch_code: Dict[str, str]` allow one run to touch multiple files coherently (e.g. a backend route and the frontend code that calls it). The Developer Agent is shown each target file's *current* content before generating anything, and is explicitly instructed to preserve everything not related to the requested change — this was added after an early version regenerated entire files from scratch and silently discarded real data. See `docs/agents.md` for the specifics.

## Test isolation (`src/tools/docker_sandbox.py`)

The Tester Agent never executes LLM-generated code directly on the host machine. It writes the patch + existing tests into a temp directory, then runs pytest inside a disposable `python:3.11-slim` Docker container, using the container's real exit code (not string-matching stdout) to determine pass/fail. See `docs/docker.md` for the full rationale and a local-fallback note.

## Human checkpoints

There are exactly two points where the pipeline stops and waits for a person:
1. **`ask_human`** — only if the Refiner Agent has genuine clarifying questions
2. **`approval_agent`** — always, on every run that reaches it. No code reaches the PR Agent without an explicit human "yes." This is intentional and non-negotiable in the current design — there's no "auto-approve" flag.
