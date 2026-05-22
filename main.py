"""Entry point."""

import asyncio
import logging

from src.config import load_config
from src.server import SoqueteServer


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def main() -> None:
    config = load_config()
    setup_logging(config.log_level)
    server = SoqueteServer(config)
    asyncio.run(server.start())


if __name__ == "__main__":
    main()
