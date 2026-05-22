from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent.parent / ".env")


@dataclass
class Config:
    host: str = "0.0.0.0"
    port: int = 18690
    auth_key: str = "changeme"
    log_level: str = "INFO"


def load_config() -> Config:
    return Config(
        host=os.getenv("WS_HOST", "0.0.0.0"),
        port=int(os.getenv("WS_PORT", "18690")),
        auth_key=os.getenv("AUTH_KEY", "changeme"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
