"""Authentication helper."""

import logging

logger = logging.getLogger(__name__)


class Authenticator:
    def __init__(self, expected_key: str) -> None:
        self._key = expected_key

    def validate(self, key: str) -> bool:
        ok = key == self._key
        if not ok:
            logger.warning("Auth failed: invalid key")
        return ok
