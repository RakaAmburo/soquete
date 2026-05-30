"""Entry point."""

import asyncio
import logging

from src.config import load_config
from src.server import SoqueteServer
from src.mqtt_listener import MqttListener


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


async def run() -> None:
    config = load_config()
    setup_logging(config.log_level)
    server = SoqueteServer(config)
    mqtt_listener = MqttListener(config, server.bus)
    await asyncio.gather(
        server.start(),
        mqtt_listener.start(),
    )


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
