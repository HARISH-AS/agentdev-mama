# AgentDEV-MAMA

**Multi-Agent Modular Automation** — a framework for autonomous software development, built around a five-agent LangGraph pipeline that takes a plain-English feature request and turns it into a tested, human-approved pull request.

## What it does

Give it a request like *"add a download button that exports the table as CSV"*, and AgentDEV-MAMA will:

1. **Clarify** the request if it's ambiguous (asks you directly, in the terminal)
2. **Write the code** across one or more files (backend + frontend together, kept consistent)
3. **Test it** for real, inside an isolated Docker sandbox
4. **Retry automatically** (up to 3 times) if tests fail, learning from the failure output each time
5. **Show you the full diff** and wait for explicit approval — nothing ships without a human saying yes
6. **Open a real GitHub pull request** (or just write the files locally, your choice)

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for the full pipeline diagram and design rationale.

```
Refiner → Developer → Tester → Approval → PR Agent
   ↑___________________|  (retry loop, up to 3x)
```

## Quick start

See [`docs/setup.md`](docs/setup.md) for the full environment setup (Docker, Ollama, VS Code, Python venv).

```powershell
git clone https://github.com/HARISH-AS/agentdev-mama.git
cd agentdev-mama
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Documentation

| Doc | Covers |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | System design, state machine, why it's built this way |
| [`docs/setup.md`](docs/setup.md) | Full environment setup, with screenshots |
| [`docs/workflow.md`](docs/workflow.md) | What a real run looks like, end to end, with screenshots |
| [`docs/agents.md`](docs/agents.md) | Each agent's responsibility, inputs, and outputs |
| [`docs/docker.md`](docs/docker.md) | Why and how Docker is used for test isolation |

## Project status

Core pipeline is working end-to-end and has produced a real, merged pull request against this repo. See [`docs/workflow.md`](docs/workflow.md) for a walkthrough of an actual run.

**Known limitations** (being tracked, not hidden):
- Frontend changes have no automated test coverage — only backend routes are verified by the Tester Agent; frontend diffs need manual review at the Approval step
- The Refiner Agent doesn't yet read target files' existing content before asking clarifying questions, so it sometimes asks things a human could answer by just looking at the code
- No guardrail yet against the Developer Agent adding unrequested scope beyond the spec

## Tech stack

- **Orchestration:** LangGraph (state machine, retry routing)
- **LLM:** Ollama, running locally (`qwen2.5-coder:7b` by default)
- **Isolation:** Docker (sandboxed test execution, with local subprocess fallback)
- **VCS:** GitPython + PyGithub (real commits, branches, and PRs)
- **Target demo app:** Flask backend + vanilla JS frontend, serving a sample employee table

## License

MIT — see [`LICENSE`](LICENSE).
