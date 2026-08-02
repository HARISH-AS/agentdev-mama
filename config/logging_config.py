"""
Centralized logging configuration for AgentDEV-MAMA.

Import get_logger(__name__) in any module instead of calling
logging.getLogger directly, so formatting/level stays consistent
project-wide and can be changed in exactly one place.
"""
from __future__ import annotations

import logging
import os
import sys

LOG_LEVEL = os.getenv("AGENTDEV_LOG_LEVEL", "INFO").upper()

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-28s | %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"

_configured = False


def _configure_root() -> None:
    global _configured
    if _configured:
        return

    root = logging.getLogger("agentdev_mama")
    root.setLevel(LOG_LEVEL)

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))
    root.addHandler(handler)
    root.propagate = False

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Return a logger namespaced under 'agentdev_mama', e.g.:
        get_logger(__name__) -> agentdev_mama.src.graph
    """
    _configure_root()
    if not name.startswith("agentdev_mama"):
        name = f"agentdev_mama.{name}"
    return logging.getLogger(name)