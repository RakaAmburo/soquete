"""Task: saludo — ejemplo trivial de respuesta rápida."""

from .base import Task


class SaludoTask(Task):
    key = "saludo"

    def execute(self, phrase: str, params: dict) -> str:
        nombre = params.get("nombre", "")
        if nombre:
            return f"Hola, {nombre}!"
        return "Hola!"
