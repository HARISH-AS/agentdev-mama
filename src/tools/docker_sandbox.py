"""
Docker sandbox for running the Developer Agent's generated code against
tests, isolated from your actual machine.

Accepts an arbitrary set of {relative_path: content} files (backend +
frontend + tests), writes them preserving their relative folder
structure, and runs pytest. Frontend files (e.g. .html) have no
automated test in this MVP — they're written into the sandbox for
completeness/consistency checks but pytest simply won't touch them;
they're verified visually at the Approval Agent step instead.

If Docker isn't reachable (daemon not running), falls back to a local
subprocess run. This keeps the pipeline usable for quick iteration, but
means the "isolation" guarantee only holds when Docker is actually up —
worth knowing, not a bug.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict

import docker
from docker.errors import DockerException

from config.logging_config import get_logger
from config.settings import settings

logger = get_logger(__name__)


def _docker_available() -> bool:
    try:
        client = docker.from_env()
        client.ping()
        return True
    except DockerException:
        return False


def run_in_sandbox(files: Dict[str, str]) -> Dict[str, Any]:
    """
    files: {relative_path: content} for ALL files needed for this test
    run — backend source, test files, and (optionally) frontend files
    written for context/consistency but not exercised by pytest.

    Preserves relative folder structure inside the temp dir so imports
    like 'from backend.app import app' or pytest.ini's pythonpath
    settings behave the same as in the real repo layout.

    Returns {"passed": bool, "output": str}.
    """
    with tempfile.TemporaryDirectory(prefix="agentdev_mama_") as tmp:
        tmp_path = Path(tmp)
        for rel_path, content in files.items():
            full_path = tmp_path / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")

        if _docker_available():
            return _run_in_docker(tmp_path)

        logger.warning(
            "Docker daemon unreachable; falling back to local subprocess "
            "(no isolation for this test run)"
        )
        return _run_locally(tmp_path)


def _run_in_docker(tmp_path: Path) -> Dict[str, Any]:
    logger.info("Running tests in Docker sandbox (image=%s)", settings.DOCKER_IMAGE)
    client = docker.from_env()

    try:
        container = client.containers.run(
            image=settings.DOCKER_IMAGE,
            command=[
                "sh",
                "-c",
                "pip install --quiet pytest flask && pytest -q /workspace",
            ],
            volumes={str(tmp_path): {"bind": "/workspace", "mode": "rw"}},
            working_dir="/workspace",
            detach=True,
        )
        result = container.wait()
        exit_code = result.get("StatusCode", 1)
        output = container.logs().decode("utf-8", errors="replace")
        container.remove()

        passed = exit_code == 0
        logger.info("Docker test run finished: exit_code=%d passed=%s", exit_code, passed)
        return {"passed": passed, "output": output}

    except DockerException as e:
        logger.error("Docker execution failed unexpectedly: %s", e)
        return {"passed": False, "output": f"Docker error: {e}"}


def _run_locally(tmp_path: Path) -> Dict[str, Any]:
    logger.info("Running tests locally via subprocess")
    try:
        result = subprocess.run(
            ["pytest", "-q", str(tmp_path)],
            capture_output=True,
            text=True,
            timeout=settings.DOCKER_TIMEOUT_SECONDS,
        )
        output = result.stdout + result.stderr
        passed = result.returncode == 0
        logger.info("Local test run finished: passed=%s", passed)
        return {"passed": passed, "output": output}
    except subprocess.TimeoutExpired:
        logger.error("Local test run timed out")
        return {"passed": False, "output": "Test run timed out"}
    except FileNotFoundError:
        msg = "pytest not found locally and Docker is unreachable — install pytest or start Docker"
        logger.error(msg)
        return {"passed": False, "output": msg}