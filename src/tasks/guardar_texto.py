"""Task: guardar_texto — guarda texto dictado en /home/pablo/Documents/textos/sin_catalogar/"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from .base import Task
from src.outbound import OutboundBus

logger = logging.getLogger(__name__)

TRIGGER = "guardar texto"
DESTINO = Path("/home/pablo/Documents/textos/sin_catalogar")


class GuardarTextoTask(Task):
    key = "guardar_texto"

    def match(self, phrase: str) -> dict | None:
        low = self.normalize(phrase)
        if low.startswith(self.normalize(TRIGGER)):
            contenido = phrase[len(TRIGGER):].strip()
            return {"contenido": contenido}
        return None

    def is_async(self) -> bool:
        return True

    def execute(self, phrase: str, params: dict) -> str:
        return "Guardando..."

    async def run_async(self, phrase: str, params: dict, bus: OutboundBus) -> None:
        contenido = params.get("contenido", "").strip()
        if not contenido:
            await bus.send("No hay texto para guardar.")
            return

        DESTINO.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo = DESTINO / f"{timestamp}.txt"

        try:
            archivo.write_text(contenido, encoding="utf-8")
            await bus.send(f"Guardado: {archivo.name}")
        except Exception as e:
            logger.error("Error guardando texto: %s", e)
            await bus.send(f"Error al guardar: {e}")
