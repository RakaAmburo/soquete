"""Task: regenerar_apk — compila y hace backup del APK via Gradle en asus."""

import subprocess
import logging

from .base import Task
from src.outbound import OutboundBus

logger = logging.getLogger(__name__)

PROYECTOS = {
    "asistente": {
        "path": "C:\\repos\\voiceassistant",
        "nombre": "voiceassistant",
    },
    "decurion": {
        "path": "C:\\repos\\decurion",
        "nombre": "decurion",
    },
}


class RegenerarApkTask(Task):
    key = "regenerar_apk"

    def is_async(self) -> bool:
        return True

    def execute(self, phrase: str, params: dict) -> str:
        proyecto = params.get("proyecto", "")
        if proyecto not in PROYECTOS:
            return f"Proyecto '{proyecto}' no reconocido. Opciones: {list(PROYECTOS.keys())}"
        nombre = PROYECTOS[proyecto]["nombre"]
        return f"Generando APK de {nombre}, aviso cuando termine..."

    async def run_async(self, phrase: str, params: dict, bus: OutboundBus) -> None:
        import asyncio

        proyecto = params.get("proyecto", "")
        if proyecto not in PROYECTOS:
            await bus.send(f"Proyecto '{proyecto}' no reconocido.")
            return

        cfg = PROYECTOS[proyecto]
        logger.info("Generando APK: %s en %s", cfg["nombre"], cfg["path"])

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
                err = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "error desconocido"
                await bus.send(f"Error generando APK de {cfg['nombre']}: {err}")
        except subprocess.TimeoutExpired:
            await bus.send(f"Timeout generando APK de {cfg['nombre']} (>5 min).")
        except Exception as e:
            await bus.send(f"Error: {e}")
