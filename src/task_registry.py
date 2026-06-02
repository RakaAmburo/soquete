"""Dynamic task registry — scans src/tasks/ and loads Task subclasses."""

from __future__ import annotations

import importlib
import importlib.util
import logging
import pkgutil
from pathlib import Path
from typing import TYPE_CHECKING

from src.tasks.base import Task

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Carpeta donde viven las tasks
TASKS_PACKAGE = "src.tasks"
TASKS_DIR = Path(__file__).parent / "tasks"


class TaskRegistry:
    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self.load()

    def load(self) -> None:
        """Scan tasks/ and register all Task subclasses by their key."""
        found: dict[str, Task] = {}

        for module_info in pkgutil.iter_modules([str(TASKS_DIR)]):
            if module_info.name == "base":
                continue
            module_name = f"{TASKS_PACKAGE}.{module_info.name}"
            try:
                module = importlib.import_module(module_name)
            except Exception as e:
                logger.error("Error importing task module %s: %s", module_name, e)
                continue

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, Task)
                    and attr is not Task
                    and attr.key
                ):
                    instance = attr()
                    found[instance.key] = instance
                    logger.debug("Registered task: %s", instance.key)

        self._tasks = found
        logger.info("Tasks loaded: %s", list(self._tasks.keys()))

    def reload(self) -> None:
        """Reload all task modules (hot reload without restart)."""
        import sys

        # Remove cached task modules (skip base to keep Task reference stable)
        to_remove = [
            k for k in sys.modules
            if k.startswith(TASKS_PACKAGE) and not k.endswith(".base")
        ]
        for key in to_remove:
            del sys.modules[key]

        self.load()
        logger.info("Tasks reloaded.")

    def get(self, key: str) -> Task | None:
        return self._tasks.get(key)

    @property
    def keys(self) -> list[str]:
        return list(self._tasks.keys())
