"""Intent engine — calls Ollama to classify phrase into {intent, params}."""

from __future__ import annotations

import json
import logging
import re

import requests

# Comandos shell que se detectan directamente sin pasar por Ollama
SHELL_PREFIXES = ("ejecuta ", "corre ", "lanza ", "run ")
SHELL_COMMANDS = {
    "date", "uptime", "ls", "df", "free", "pwd", "whoami", "ps",
    "top", "uname", "hostname", "ip", "cat", "echo", "env", "printenv",
}

def _try_shell_shortcut(phrase: str) -> dict | None:
    """Return comando_shell intent if phrase looks like a terminal command."""
    stripped = phrase.strip()
    # Prefijo explícito: "ejecuta date", "corre ls -la"
    for prefix in SHELL_PREFIXES:
        if stripped.lower().startswith(prefix):
            cmd = stripped[len(prefix):].strip()
            return {"intent": "comando_shell", "params": {"comando": cmd}}
    # Comando conocido solo o con flags: "date", "df -h", "free -m"
    base = stripped.split()[0].lower() if stripped else ""
    if base in SHELL_COMMANDS:
        return {"intent": "comando_shell", "params": {"comando": stripped}}
    return None

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

Reglas importantes:
- Si el texto es literalmente un comando de terminal Linux de una sola palabra o frase técnica (ejemplos: "date", "uptime", "ls", "df -h", "free -m", "pwd", "whoami") O si dice "ejecuta", "corre", "lanza" seguido de algo → intent="comando_shell", params={{"comando": "<el comando exacto>"}}
- "qué hora es" o "dime la hora" → intent="hora" (NO comando_shell)
- Extrae parámetros mencionados: nombres, números, estados (encender/apagar, activar/desactivar, abrir/cerrar), temperatura, porcentajes, zonas
- Si no encaja en ninguna intención → "desconocido"

Formato: {{"intent": "nombre", "params": {{...}}}}

Texto: "{phrase}"
JSON:"""

    shortcut = _try_shell_shortcut(phrase)
    if shortcut:
        logger.debug("Shell shortcut: %s", shortcut)
        return shortcut

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
