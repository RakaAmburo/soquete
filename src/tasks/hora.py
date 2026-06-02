"""Task: hora — devuelve la hora actual."""

from datetime import datetime
from .base import Task


class HoraTask(Task):
    key = "hora"

    def execute(self, phrase: str, params: dict) -> str:
        now = datetime.now().strftime("%H:%M")
        return f"Son las {now}."
