"""MQTT listener — forwards notifications to the connected WebSocket client."""

import asyncio
import json
import logging

import paho.mqtt.client as mqtt

from .config import Config
from .outbound import OutboundBus

logger = logging.getLogger(__name__)

NOTIFY_TOPIC = "soquete/notify"


class MqttListener:
    """Subscribes to MQTT and pushes incoming notifications to the WS client."""

    def __init__(self, config: Config, bus: OutboundBus) -> None:
        self._bus = bus
        self._loop: asyncio.AbstractEventLoop | None = None
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._mqtt_host = config.mqtt_host
        self._mqtt_port = config.mqtt_port

    def _on_connect(self, client, userdata, flags, rc, properties) -> None:
        logger.info("MQTT connected, subscribing to %s", NOTIFY_TOPIC)
        client.subscribe(NOTIFY_TOPIC)

    def _on_message(self, client, userdata, msg) -> None:
        try:
            text = msg.payload.decode("utf-8")
        except Exception as e:
            logger.error("Failed to decode MQTT payload: %s", e)
            return

        logger.info("MQTT notification received: %s", text)

        payload = json.dumps({"type": "notification", "text": text})

        if self._loop is not None:
            asyncio.run_coroutine_threadsafe(self._bus.send(payload), self._loop)

    async def start(self) -> None:
        self._loop = asyncio.get_running_loop()
        self._client.connect_async(self._mqtt_host, self._mqtt_port)
        self._client.loop_start()
        logger.info("MqttListener started (topic: %s)", NOTIFY_TOPIC)
