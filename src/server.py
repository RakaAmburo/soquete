"""WebSocket server — transport layer."""

import asyncio
import json
import logging
from typing import Any

import picows

from .auth import Authenticator
from .config import Config
from .outbound import OutboundBus
from .processor import MessageProcessor

logger = logging.getLogger(__name__)


class SoqueteListener(picows.WSListener):
    """Handles a single WebSocket connection."""

    def __init__(
        self,
        auth: Authenticator,
        processor: MessageProcessor,
        bus: OutboundBus,
    ) -> None:
        self._transport: picows.WSTransport | None = None
        self._auth = auth
        self._processor = processor
        self._bus = bus
        self._authenticated = False

    # --- picows callbacks ---

    def on_ws_connected(self, transport: picows.WSTransport) -> None:
        self._transport = transport
        logger.info("Client connected")
        self._bus.register(self._send_text)

    def on_ws_frame(self, transport: picows.WSTransport, frame: picows.WSFrame) -> None:
        asyncio.ensure_future(self._handle_frame(frame))

    def on_ws_disconnected(self, transport: picows.WSTransport) -> None:
        logger.info("Client disconnected")
        self._bus.unregister()

    # --- internal ---

    async def _handle_frame(self, frame: picows.WSFrame) -> None:
        try:
            raw = frame.get_payload_as_utf8_text()
        except Exception:
            raw = frame.get_payload_as_bytes().decode("utf-8", errors="replace")

        logger.debug("Frame received: %s", raw)

        try:
            data: dict[str, Any] = json.loads(raw)
        except json.JSONDecodeError:
            await self._send_error("invalid JSON")
            return

        if not self._authenticated:
            key = data.get("key", "").strip()
            if self._auth.validate(key):
                self._authenticated = True
                await self._send_text("authenticated")
                logger.info("Client authenticated")
            else:
                await self._send_error("auth failed")
                self._transport.disconnect()
            return

        msg = data.get("msg")
        if msg is None:
            await self._send_error("missing 'msg' field")
            return

        response = await self._processor.handle(msg)
        if response is not None:
            await self._send_json({"msg": response})

    async def _send_text(self, text: str) -> None:
        await self._send_json({"msg": text})

    async def _send_json(self, payload: dict[str, Any]) -> None:
        if self._transport is not None:
            self._transport.send(picows.WSMsgType.TEXT, json.dumps(payload).encode())

    async def _send_error(self, reason: str) -> None:
        if self._transport is not None:
            self._transport.send(picows.WSMsgType.TEXT, json.dumps({"error": reason}).encode())


class SoqueteServer:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._auth = Authenticator(config.auth_key)
        self._bus = OutboundBus()
        self._processor = MessageProcessor(bus=self._bus)

    @property
    def bus(self) -> OutboundBus:
        return self._bus

    async def start(self) -> None:
        def factory(request: picows.WSUpgradeRequest) -> SoqueteListener:
            return SoqueteListener(self._auth, self._processor, self._bus)

        server = await picows.ws_create_server(
            factory,
            self._config.host,
            self._config.port,
        )
        logger.info(
            "Soquete listening on ws://%s:%d", self._config.host, self._config.port
        )
        try:
            await asyncio.get_running_loop().create_future()  # run forever
        finally:
            server.close()
            await server.wait_closed()
