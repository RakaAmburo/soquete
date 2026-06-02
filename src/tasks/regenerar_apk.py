"""Task: regenerar_apk — compila y hace backup del APK via Gradle en asus."""

import asyncio
import logging
import subprocess

from .base import Task
from src.outbound import OutboundBus

logger = logging.getLogger(__name__)

PROYECTOS = {
    "asistente": {"path": "C:\\repos\\voiceassistant", "nombre": "voiceassistant"},
    "centurion":  {"path": "C:\\repos\\decurion",       "nombre": "centurion"},
}

TRIGGER_WORDS = ("regenera", "genera el apk", "compila", "regenerar apk", "generar apk")


class RegenerarApkTask(Task):
    key = "regenerar_apk"

    def match(self, phrase: str) -> dict | None:
        low = phrase.strip().lower()
        if not any(kw in low for kw in TRIGGER_WORDS):
            return None
        for proyecto in PROYECTOS:
            if proyecto in low:
                return {"proyecto": proyecto}
        return None

    def is_async(self) -> bool:
        return True

    def execute(self, phrase: str, params: dict) -> str:
        return ""

    async def run_async(self, phrase: str, params: dict, bus: OutboundBus) -> None:
        proyecto = params.get("proyecto", "")
        if proyecto not in PROYECTOS:
            await bus.send(f"Proyecto '{proyecto}' no reconocido. Opciones: {list(PROYECTOS.keys())}")
            return

        cfg = PROYECTOS[proyecto]
        logger.info("Generando APK: %s", cfg["nombre"])

        cmd = f'ssh asus "cd {cfg["path"]} && gradlew.bat backApk"'
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=300
                ),
            )
            if result.returncode == 0:
                await bus.send(f"APK de {cfg['nombre']} generado y guardado en Dropbox.")
            else:
                err = (result.stderr.strip().splitlines() or ["error desconocido"])[-1]
                await bus.send(f"Error generando APK de {cfg['nombre']}: {err}")
        except subprocess.TimeoutExpired:
            await bus.send(f"Timeout generando APK de {cfg['nombre']} (>5 min).")
        except Exception as e:
            await bus.send(f"Error: {e}")
