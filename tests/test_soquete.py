"""Tests funcionales/de integración para soquete.

Requiere el servidor corriendo en localhost:WS_PORT (PM2 o manual).
Ejecutar con: pytest tests/ -v
"""

import asyncio
import json
import os
from pathlib import Path

import pytest
import websockets

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent.parent
ENV_FILE = ROOT / ".env"

_env_vals: dict[str, str] = {}
if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            _env_vals[k.strip()] = v.strip()

AUTH_KEY = _env_vals.get("AUTH_KEY", os.getenv("AUTH_KEY", "changeme"))
WS_PORT = int(_env_vals.get("WS_PORT", os.getenv("WS_PORT", "18690")))
WS_HOST = _env_vals.get("WS_HOST", os.getenv("WS_HOST", "127.0.0.1"))
URI = f"ws://{WS_HOST}:{WS_PORT}"


# ---------------------------------------------------------------------------
# Test 1: connect → auth → send msg → receive "mensaje recibido"
# ---------------------------------------------------------------------------

@pytest.mark.asyncio(loop_scope="function")
async def test_auth_and_message():
    """Conecta, autentica, envía mensaje, verifica respuesta."""
    async with websockets.connect(URI) as ws:
        # Auth
        await ws.send(json.dumps({"key": AUTH_KEY}))
        resp = json.loads(await ws.recv())
        assert resp.get("msg") == "authenticated", f"Auth response: {resp}"

        # Mensaje
        await ws.send(json.dumps({"msg": "hola"}))
        resp = json.loads(await ws.recv())
        assert resp.get("msg") == "mensaje recibido", f"Response: {resp}"


# ---------------------------------------------------------------------------
# Test 2: outbound bus — test unitario en proceso propio
# ---------------------------------------------------------------------------

@pytest.mark.asyncio(loop_scope="function")
async def test_outbound_bus_unit():
    """
    Verifica que OutboundBus entrega mensajes al callback registrado
    y los descarta cuando no hay cliente conectado.
    """
    from src.outbound import OutboundBus

    bus = OutboundBus()
    received: list[str] = []

    async def mock_send(text: str) -> None:
        received.append(text)

    # Sin cliente registrado → warning, sin crash
    await bus.send("sin cliente")
    assert received == []

    # Con cliente registrado
    bus.register(mock_send)
    await bus.send("con cliente")
    assert received == ["con cliente"]

    # Tras desregistrar → sin entrega
    bus.unregister()
    await bus.send("sin cliente de nuevo")
    assert received == ["con cliente"]  # sin cambio


# ---------------------------------------------------------------------------
# Test 3: outbound integración — servidor embebido en test
# ---------------------------------------------------------------------------

@pytest.mark.asyncio(loop_scope="function")
async def test_outbound_integration_embedded():
    """
    Levanta un servidor soquete en un puerto temporal dentro del test,
    conecta un cliente, y verifica que bus.send() llega al cliente.
    """
    import random
    from src.config import Config
    from src.server import SoqueteServer

    port = random.randint(19000, 19999)
    config = Config(host="127.0.0.1", port=port, auth_key="testkey")
    server = SoqueteServer(config)

    # Correr servidor en background
    server_task = asyncio.create_task(server.start())
    await asyncio.sleep(0.3)  # esperar que arranque

    received: list[str] = []
    try:
        async with websockets.connect(f"ws://127.0.0.1:{port}") as ws:
            # Auth
            await ws.send(json.dumps({"key": "testkey"}))
            resp = json.loads(await ws.recv())
            assert resp.get("msg") == "authenticated"

            # Push desde backend
            await server.bus.send("mensaje saliente")
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=3))
            received.append(msg.get("msg", ""))
    finally:
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

    assert received == ["mensaje saliente"], f"Received: {received}"
