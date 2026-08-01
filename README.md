# 🤖 AgentDEV-MAMA

<p align="center">

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-success)
![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-black)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker)
![GitHub](https://img.shields.io/badge/GitHub-Automation-181717?logo=github)
![License](https://img.shields.io/badge/License-MIT-green)

</p>

<h1 align="center">
AgentDEV-MAMA
</h1>

<p align="center">
<b>Multi-Agent Modular Automation</b>
</p>

<p align="center">
A modular multi-agent framework for autonomous software development powered by <b>LangGraph</b>, <b>Ollama</b>, <b>Docker</b>, and <b>GitHub</b>.
</p>

---

# 🚀 Overview

AgentDEV-MAMA is an autonomous software engineering framework where specialized AI agents collaborate to transform a user requirement into tested source code and a GitHub-ready pull request.

Instead of relying on a single LLM, the framework assigns dedicated responsibilities to independent agents, enabling modular reasoning, iterative refinement, isolated testing, and automated development workflows.

---

# ✨ Features

- 🧠 Requirement Refinement Agent
- 💻 Autonomous Code Generation
- 🧪 Automated Testing
- 🐳 Docker Sandbox Execution
- ✅ AI-Based Code Approval
- 🌿 Git Branch Automation
- 🔀 Pull Request Generation
- 🔒 Local LLM (No cloud API required)
- ⚡ Modular LangGraph Workflow

---

# 🏗️ System Architecture

```text
                   ┌────────────────────┐
                   │   User Requirement │
                   └─────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │  Refiner Agent      │
                  └─────────┬───────────┘
                            │
                            ▼
                  ┌─────────────────────┐
                  │ Developer Agent     │
                  └─────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Docker Sandbox Tool  │
                 └─────────┬────────────┘
                           │
                           ▼
                  ┌─────────────────────┐
                  │ Tester Agent        │
                  └─────────┬───────────┘
                            │
                 ┌──────────┴──────────┐
                 │                     │
             Tests Pass           Tests Fail
                 │                     │
                 ▼                     │
        ┌─────────────────┐           │
        │ Approval Agent  │           │
        └────────┬────────┘           │
                 │                    │
                 ▼                    │
          ┌──────────────┐            │
          │ PR Agent     │◄───────────┘
          └──────┬───────┘
                 │
                 ▼
          GitHub Repository
```

---

# 🤖 Multi-Agent Workflow

| Agent | Responsibility |
|--------|----------------|
| Refiner Agent | Clarifies and restructures user requirements |
| Developer Agent | Generates production-ready source code |
| Tester Agent | Executes automated tests inside Docker |
| Approval Agent | Reviews implementation quality |
| PR Agent | Creates commits, branches and Pull Requests |

---

# 🛠 Tech Stack

| Technology | Purpose |
|------------|---------|
| Python 3.13 | Backend |
| LangGraph | Agent orchestration |
| Ollama | Local LLM inference |
| Qwen2.5-Coder | Coding model |
| Docker | Secure code execution |
| GitPython | Git automation |
| PyGithub | GitHub integration |
| python-dotenv | Environment management |

---

# 📂 Project Structure

```text
agentdev-mama/

│
├── config/
│   └── settings.py
│
├── src/
│   ├── agents/
│   │   ├── refiner_agent.py
│   │   ├── developer_agent.py
│   │   ├── tester_agent.py
│   │   ├── approval_agent.py
│   │   └── pr_agent.py
│   │
│   ├── tools/
│   │   ├── docker_sandbox.py
│   │   └── git_tool.py
│   │
│   ├── graph.py
│   └── state.py
│
├── demo_repo/
│
├── docs/
│
├── requirements.txt
│
├── .env
│
└── main.py
```

---

# ⚙️ Installation

Clone the repository

```bash
git clone https://github.com/<your_username>/agentdev-mama.git

cd agentdev-mama
```

Create a virtual environment

```bash
python -m venv venv
```

Activate it

Windows

```bash
venv\Scripts\activate
```

Linux / macOS

```bash
source venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# 🦙 Configure Ollama

Install Ollama

```bash
https://ollama.com/download
```

Download the model

```bash
ollama pull qwen2.5-coder:7b
```

Start Ollama

```bash
ollama serve
```

Verify

```bash
curl http://localhost:11434
```

---

# ▶️ Running

```bash
python main.py
```

---

# 💡 Example

### Input

```text
Create a Flask API with a /health endpoint.
```

### Agent Workflow

```
Requirement
        │
        ▼
Refiner Agent

        ▼
Developer Agent

        ▼
Docker Testing

        ▼
Approval

        ▼
Git Commit

        ▼
Pull Request
```

### Output

```text
✔ Requirement refined

✔ Flask application generated

✔ Docker tests passed

✔ Code approved

✔ Pull Request created
```

---

# 📈 Roadmap

- [x] LangGraph Workflow
- [x] Ollama Integration
- [x] Docker Sandbox
- [x] GitHub Automation
- [ ] Web Dashboard
- [ ] RAG Memory
- [ ] Multi-LLM Support
- [ ] Security Review Agent
- [ ] Documentation Agent
- [ ] Performance Optimization Agent

---

# 🤝 Contributing

Contributions are welcome!

Feel free to open Issues and Pull Requests.

---

# 📜 License

This project is licensed under the MIT License.

---

# 👨‍💻 Author

**Harish A S**

Built as part of research and experimentation in autonomous AI software engineering using LangGraph and local large language models.

---

<p align="center">
⭐ If you find this project useful, consider giving it a star!
</p>

