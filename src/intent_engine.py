"""Intent engine — calls Ollama to classify phrase into {intent, params}."""

from __future__ import annotations

import json
import logging

import requests

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma3:1b"
TIMEOUT = 60


def classify(phrase: str, known_keys: list[str]) -> dict:
    """
    Send phrase to Ollama and return {intent: str, params: dict}.
    Falls back to {intent: 'desconocido', params: {}} on any error.
    """
    intents = ", ".join(known_keys + ["desconocido"])

    prompt = f"""Eres un clasificador de intenciones para automatización del hogar y sistema Linux.
Dado el texto del usuario, responde SOLO con un JSON válido.

Intenciones posibles: {intents}

Reglas:
- Extrae parámetros mencionados: nombres, números, estados (encender/apagar, activar/desactivar, abrir/cerrar), temperatura, porcentajes, zonas, comandos
- Si no encaja en ninguna intención → "desconocido"

Formato: {{"intent": "nombre", "params": {{...}}}}

Texto: "{phrase}"
JSON:"""

    try:
        r = requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "stream": False},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        raw = r.json()["response"].strip()

        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON found in response")

        data = json.loads(raw[start:end])
        intent = data.get("intent", "desconocido")
        if intent not in known_keys:
            intent = "desconocido"
        return {"intent": intent, "params": data.get("params", {})}

    except Exception as e:
        logger.error("Intent engine error: %s", e)
        return {"intent": "desconocido", "params": {}}
