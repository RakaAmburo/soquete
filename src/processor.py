"""Message processor — decoupled from transport layer."""

import logging

logger = logging.getLogger(__name__)


class MessageProcessor:
    """Process incoming messages and return a response."""

    async def handle(self, msg: str) -> str:
        """Handle a message and return the response text."""
        logger.debug("Processing message: %s", msg)
        # Primera iteración: respuesta fija
        return "mensaje recibido"
