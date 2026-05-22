"""Outbound message bus — backend → client."""

import asyncio
import logging
from typing import Callable, Awaitable

logger = logging.getLogger(__name__)

# Callback type: async function that accepts a text message
SendCallback = Callable[[str], Awaitable[None]]


class OutboundBus:
    """Allows backend components to push messages to the connected client."""

    def __init__(self) -> None:
        self._send_cb: SendCallback | None = None

    def register(self, cb: SendCallback) -> None:
        self._send_cb = cb

    def unregister(self) -> None:
        self._send_cb = None

    async def send(self, text: str) -> None:
        if self._send_cb is None:
            logger.warning("No client connected, dropping outbound message: %s", text)
            return
        await self._send_cb(text)


# Singleton bus shared across the application
bus = OutboundBus()
