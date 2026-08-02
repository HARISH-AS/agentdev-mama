"""
Central config object. Every agent reads settings from here instead of
calling os.getenv() directly, so there's exactly one place that knows
about environment variable names.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    REPO_OWNER: str = os.getenv("REPO_OWNER", "")
    REPO_NAME: str = os.getenv("REPO_NAME", "demo_repo")

    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "3"))

    DOCKER_IMAGE: str = os.getenv("DOCKER_IMAGE", "python:3.11-slim")
    DOCKER_TIMEOUT_SECONDS: int = int(os.getenv("DOCKER_TIMEOUT_SECONDS", "60"))

    @property
    def github_enabled(self) -> bool:
        """PR Agent uses this to decide real push vs simulated mode."""
        return bool(self.GITHUB_TOKEN and self.REPO_OWNER)


settings = Settings()