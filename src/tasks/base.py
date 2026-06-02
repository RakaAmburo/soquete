"""Base class for all tasks."""

from __future__ import annotations

import asyncio
import logging
import unicodedata
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.outbound import OutboundBus

logger = logging.getLogger(__name__)


class Task(ABC):
    """
    Base class for all tasks.

    Subclasses must define:
        key: str  — unique identifier used for intent routing
        execute(phrase, params) — returns a quick response string

    Optionally override run_async() for long-running work that
    should respond "procesando..." immediately and publish the
    result via the bus when done.
    """

    key: str = ""

    @staticmethod
    def normalize(s: str) -> str:
        """Strip accents and lowercase for robust matching."""
        return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode().lower()

    def match(self, phrase: str) -> dict | None:
        """
        Optional shortcut: if this task can self-detect from the phrase,
        return the params dict. Return None to fall through to Ollama.
        """
        return None

    def execute(self, phrase: str, params: dict) -> str:
        """
        Fast path: return a response string directly.
        Override this for quick tasks.
        """
        return ""

    def is_async(self) -> bool:
        """Return True if this task should run in the async path."""
        return False

    async def run_async(self, phrase: str, params: dict, bus: "OutboundBus") -> None:
        """
        Slow path: run in a thread pool and publish result via bus.
        Override this for long-running tasks.
        """
        pass
