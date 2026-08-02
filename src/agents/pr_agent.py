"""
PR Agent.

Final step: after human approval, asks (each run) whether to write the
approved patch_code locally only, or go through the full commit/push/
GitHub PR flow. Local-only requires nothing extra. GitHub mode requires
GITHUB_TOKEN + REPO_OWNER/REPO_NAME in .env, and workspace/sample_project
being an actual git repo with a configured 'origin' remote.
"""
from __future__ import annotations

import time
from pathlib import Path

from github import Github

from config.logging_config import get_logger
from config.settings import settings
from src.state import PipelineState, log_transition
from src.tools import git_tool

logger = get_logger(__name__)

_NODE_NAME = "pr_agent"

_PROJECT_SUBDIR = "workspace/sample_project"  # where patch_code's relative paths live
_GIT_REPO_ROOT = "."  # agentdev-mama is the actual git repo; sample_project is just a folder in it


def _write_files_locally(files: dict) -> None:
    """Plain file writes, no git involved at all."""
    for rel_path, content in files.items():
        full_path = Path(_PROJECT_SUBDIR) / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        logger.info("Wrote %s locally", full_path)


def pr_agent_node(state: PipelineState) -> dict:
    logger.info("PR Agent starting")

    choice = input(
        "\nWrite approved change [l]ocally only, or push a real GitHub PR [g]? [l/g]: "
    ).strip().lower()

    if choice != "g":
        _write_files_locally(state["patch_code"])
        note = f"wrote {list(state['patch_code'].keys())} locally (no git/GitHub)"
        return {
            "pr_url": "(local write only, no PR created)",
            "chain_of_thought": log_transition(state, _NODE_NAME, note),
        }

    if not settings.github_enabled:
        msg = (
            "GitHub mode requested but GITHUB_TOKEN/REPO_OWNER not set in .env. "
            "Falling back to local-only write. Set GITHUB_TOKEN, REPO_OWNER, "
            "REPO_NAME in .env and make workspace/sample_project a git repo "
            "with an 'origin' remote to enable real PRs."
        )
        logger.warning(msg)
        _write_files_locally(state["patch_code"])
        return {
            "pr_url": "(local write only — GitHub not configured)",
            "chain_of_thought": log_transition(state, _NODE_NAME, msg),
        }

    branch_name = f"agentdev-mama/{int(time.time())}"
    commit_message = f"AgentDEV-MAMA: {state.get('explanation', 'automated change')}"

    try:
        prefixed_files = {
            f"{_PROJECT_SUBDIR}/{rel_path}": content
            for rel_path, content in state["patch_code"].items()
        }
        git_tool.commit_change(
            repo_path=_GIT_REPO_ROOT,
            files=prefixed_files,
            branch_name=branch_name,
            commit_message=commit_message,
        )
        git_tool.push_branch(repo_path=_GIT_REPO_ROOT, branch_name=branch_name)

        gh = Github(settings.GITHUB_TOKEN)
        repo = gh.get_repo(f"{settings.REPO_OWNER}/{settings.REPO_NAME}")
        pr = repo.create_pull(
            title=f"AgentDEV-MAMA: {', '.join(state['target_files'])}",
            body=state.get("explanation", ""),
            head=branch_name,
            base="main",
        )
        logger.info("Opened PR: %s", pr.html_url)

        return {
            "pr_url": pr.html_url,
            "chain_of_thought": log_transition(state, _NODE_NAME, f"opened PR {pr.html_url}"),
        }

    except Exception as e:
        logger.error("PR Agent failed: %s", e)
        return {
            "pr_url": None,
            "chain_of_thought": log_transition(state, _NODE_NAME, f"PR creation failed: {e}"),
        }