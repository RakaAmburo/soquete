"""Message processor — intent dispatch with task registry."""

from __future__ import annotations

import asyncio
import logging

from src.intent_engine import classify
from src.task_registry import TaskRegistry
from src.outbound import OutboundBus

logger = logging.getLogger(__name__)


class MessageProcessor:
    """Classify incoming messages and dispatch to registered tasks."""

    RELOAD_PHRASE = "recargar tareas"

    def __init__(self, bus: OutboundBus | None = None) -> None:
        self._registry = TaskRegistry()
        self._bus = bus

    def set_bus(self, bus: OutboundBus) -> None:
        self._bus = bus

    async def handle(self, msg: str) -> str:
        # Trigger de recarga en caliente
        if msg.strip().lower() == self.RELOAD_PHRASE:
            self._registry.reload()
            return f"Tareas recargadas: {self._registry.keys}"

        # Consultar match() de cada task antes de llamar a Ollama
        matched_task = None
        matched_params = None
        for task in (self._registry.get(k) for k in self._registry.keys):
            if task is None:
                continue
            params_candidate = task.match(msg)
            if params_candidate is not None:
                matched_task = task
                matched_params = params_candidate
                break

        if matched_task is not None:
            intent = matched_task.key
            params = matched_params
        else:
            result = await asyncio.get_event_loop().run_in_executor(
                None, classify, msg, self._registry.keys
            )
            intent = result["intent"]
            params = result["params"]
        logger.info("Phrase: %r | Intent: %s | Params: %s", msg, intent, params)

        task = self._registry.get(intent)
        if task is None:
            return "No sé cómo hacer eso."

        if task.is_async():
            if self._bus:
                asyncio.ensure_future(task.run_async(msg, params, self._bus))
            quick = task.execute(msg, params)
            return quick if quick else None

        return task.execute(msg, params)
