"""
Thin wrapper around GitPython for the local commit/branch operations
the PR Agent needs before pushing. Kept separate from pr_agent.py so
git plumbing and GitHub API calls (PyGithub) stay independently testable.
"""
from __future__ import annotations

from pathlib import Path

import git

from config.logging_config import get_logger

logger = get_logger(__name__)


def commit_change(
    repo_path: str,
    files: dict,
    branch_name: str,
    commit_message: str,
) -> str:
    """
    Write each {relative_path: content} in files inside repo_path,
    create/checkout branch_name, commit ALL of them together as one
    atomic commit (so backend + frontend changes for one feature never
    land split across commits), and return the branch name for the PR
    Agent to push and reference.
    """
    repo = git.Repo(repo_path)
    logger.info(
        "Preparing commit of %d file(s) on branch '%s' in %s",
        len(files),
        branch_name,
        repo_path,
    )

    # Create branch from current HEAD if it doesn't already exist.
    if branch_name not in [h.name for h in repo.heads]:
        repo.git.checkout("-b", branch_name)
    else:
        repo.git.checkout(branch_name)

    for rel_path, content in files.items():
        file_path = Path(repo_path) / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

    repo.index.add(list(files.keys()))
    repo.index.commit(commit_message)
    logger.info("Committed change: %s (%d file(s))", commit_message, len(files))

    return branch_name


def push_branch(repo_path: str, branch_name: str, remote_name: str = "origin") -> None:
    repo = git.Repo(repo_path)
    remote = repo.remote(name=remote_name)
    logger.info("Pushing branch '%s' to remote '%s'", branch_name, remote_name)
    remote.push(refspec=f"{branch_name}:{branch_name}")