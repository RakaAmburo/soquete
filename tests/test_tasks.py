"""Tests básicos para task registry y tasks."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.task_registry import TaskRegistry
from src.tasks.saludo import SaludoTask
from src.tasks.hora import HoraTask


def test_registry_loads_tasks():
    registry = TaskRegistry()
    assert "saludo" in registry.keys
    assert "hora" in registry.keys
    assert "comando_shell" in registry.keys


def test_registry_get():
    registry = TaskRegistry()
    task = registry.get("saludo")
    assert task is not None
    assert isinstance(task, SaludoTask)


def test_saludo_sin_nombre():
    task = SaludoTask()
    result = task.execute("hola", {})
    assert result == "Hola!"


def test_saludo_con_nombre():
    task = SaludoTask()
    result = task.execute("hola pablo", {"nombre": "Pablo"})
    assert "Pablo" in result


def test_hora():
    task = HoraTask()
    result = task.execute("qué hora es", {})
    assert "Son las" in result


def test_registry_reload():
    registry = TaskRegistry()
    keys_before = set(registry.keys)
    registry.reload()
    keys_after = set(registry.keys)
    assert keys_before == keys_after


def test_unknown_task():
    registry = TaskRegistry()
    assert registry.get("desconocido") is None


def test_comando_shell_is_async():
    from src.tasks.comando_shell import ComandoShellTask
    task = ComandoShellTask()
    assert task.is_async() is True
    assert task.execute("ejecuta algo", {}) == ""


async def _run_comando_shell():
    from src.tasks.comando_shell import ComandoShellTask
    from src.outbound import OutboundBus

    received = []

    class MockBus(OutboundBus):
        async def send(self, text: str) -> None:
            received.append(text)

    task = ComandoShellTask()
    bus = MockBus()
    await task.run_async("", {"comando": "echo hola"}, bus)
    return received


def test_comando_shell_async():
    received = asyncio.run(_run_comando_shell())
    assert received == ["hola"]
