"""Task: comando_shell — ejecuta un comando del sistema (async, resultado por bus)."""

import asyncio
import logging
import subprocess

from .base import Task
from src.outbound import OutboundBus

logger = logging.getLogger(__name__)


class ComandoShellTask(Task):
    key = "comando_terminal"

    def is_async(self) -> bool:
        return True

    def execute(self, phrase: str, params: dict) -> str:
        return "procesando..."

    async def run_async(self, phrase: str, params: dict, bus: OutboundBus) -> None:
        cmd = params.get("comando", "")
        if not cmd:
            await bus.send("No se especificó ningún comando.")
            return

        logger.info("Ejecutando comando: %s", cmd)
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=30
                ),
            )
            output = result.stdout.strip() or result.stderr.strip() or "(sin salida)"
        except subprocess.TimeoutExpired:
            output = "El comando tardó demasiado."
        except Exception as e:
            output = f"Error: {e}"

        await bus.send(output)
