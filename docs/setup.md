# Setup

This walks through the full environment setup used for AgentDEV-MAMA, from a clean machine to a working `python main.py` run.

> **Note:** the screenshots below are pulled from the actual setup session. If any caption doesn't match what's shown, it's a labeling mismatch from compiling this doc after the fact — the steps themselves are accurate regardless.

## 1. Install Docker Desktop

Download from docker.com, install, restart if prompted. Verify with:
```bash
docker run hello-world
```

![Docker and development environment setup](screenshots/setup-1.png)
*Docker install verification alongside the rest of the development environment overview.*

## 2. Install Ollama

Download from ollama.com, then pull a coding model:
```bash
ollama pull qwen2.5-coder:7b
ollama serve
```

![Ollama running confirmation](screenshots/setup-2.png)
*Confirming Ollama is installed and the local server responds.*

## 3. Install Python 3.11+ and set up VS Code

Install the Python and Docker extensions in VS Code. Confirm the interpreter is set to the project's venv (`Ctrl+Shift+P` → "Python: Select Interpreter").

![VS Code project structure](screenshots/setup-3.png)
*Project structure as seen in the VS Code Explorer after initial scaffolding.*

## 4. Create the GitHub repo and clone locally

```powershell
git clone https://github.com/HARISH-AS/agentdev-mama.git
cd agentdev-mama
code .
```

![Project folder opened in VS Code](screenshots/setup-4.png)

## 5. Create the virtual environment

```powershell
python -m venv venv
venv\Scripts\activate
```

Select the interpreter in VS Code so linting/running/debugging all use the venv.

![Virtual environment and dependency installation](screenshots/setup-5.png)

## 6. Install dependencies

```powershell
pip install langgraph langchain langchain-ollama langchain-community gitpython docker python-dotenv rich pydantic PyGithub flask pytest
pip list
```

![pip list confirming installed packages](screenshots/setup-6.png)
*Confirming all required packages installed correctly, including transitive dependencies like `langchain-core`.*

## 7. Resolve import/config issues

A few things came up during setup that are worth documenting since they're easy to hit again:

- **Missing `config/logging_config.py`** — caused an unresolved-import Problem in `state.py`/`graph.py` until added alongside the existing `config/settings.py`.
- **Pylance flagging `from app import app`** — cosmetic only; fixed properly via a `conftest.py` in `workspace/sample_project/` that inserts `backend/` onto `sys.path`, which works regardless of pytest version or invocation directory (more reliable than `pytest.ini`'s `pythonpath` option).

![Problems panel showing an unresolved import](screenshots/setup-7.png)
*Pylance flagging an import before the conftest.py fix.*

![Confirming pytest.ini/conftest.py placement](screenshots/setup-8.png)
*Correct placement of pytest.ini inside workspace/sample_project/, not the outer repo root.*

## 8. Set up GitHub authentication

Two separate credentials are needed, for two different purposes:

1. **Personal access token (classic)**, `repo` scope only — used by PyGithub inside `pr_agent.py` to open real pull requests. Generate at GitHub → Settings → Developer settings → Personal access tokens (classic).
2. **Git CLI auth** — separate from the token above; `git push` authenticates via browser OAuth (or the token as a password) the first time, then Windows Credential Manager remembers it.

![GitHub personal access token setup](screenshots/setup-9.png)

![GitHub credentials overview page](screenshots/setup-10.png)

Add the token to `.env` (never committed — confirm `.gitignore` excludes it):
```
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
REPO_OWNER=HARISH-AS
REPO_NAME=agentdev-mama
```

## 9. Verify Docker sandbox connectivity

```powershell
docker run --rm python:3.11-slim sh -c "pip install --quiet pytest flask && echo INSTALL_OK"
```

If this prints `INSTALL_OK`, the sandbox has working internet access and any future test failures are about the code, not infrastructure.

## Done

At this point, `python main.py` from the project root should run the full pipeline end-to-end. See [`workflow.md`](workflow.md) for what an actual run looks like.
