import asyncio
import json
import logging
import sys
from time import sleep
from typing import Callable, Any, Optional

import paho.mqtt.client as mqtt

from common.consts import *
from models.MQTTConfigData import MQTTConfigurationData

_LOGGER = logging.getLogger(__name__)


class MQTTClient:
    def __init__(self, manager, on_message: Callable[[Any, str, dict], None]):
        self._manager = manager
        self._mqtt_config = MQTTConfigurationData()
        self._mqtt_client: Optional[mqtt.Client] = None
        self._on_message: Callable[[Any, str, dict], None] = on_message
        self._is_connected = False

    @property
    def topic_command_prefix(self):
        return self._mqtt_config.topic_command_prefix

    @property
    def topic_prefix(self):
        return self._mqtt_config.topic_prefix

    @property
    def manager(self):
        return self._manager

    @property
    def is_connected(self):
        return self._is_connected

    @property
    def on_message(self):
        return self._on_message

    def initialize(self):
        self._is_connected = False

        config = self._mqtt_config

        self._mqtt_client = mqtt.Client(config.client_id)

        self._mqtt_client.user_data_set(self)

        self._mqtt_client.username_pw_set(config.username, config.password)

        self._mqtt_client.on_connect = self._on_mqtt_connect
        self._mqtt_client.on_message = self._on_mqtt_message
        self._mqtt_client.on_disconnect = self._on_mqtt_disconnect

        while not self.is_connected:
            try:
                _LOGGER.info("MQTT Broker is trying to connect...")

                self._mqtt_client.connect(config.host, int(config.port), 60)
                self._mqtt_client.loop_start()

                self._is_connected = True

            except Exception as ex:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                error_details = f"error: {ex}, Line: {exc_tb.tb_lineno}"

                _LOGGER.error(f"Failed to connect to broker, retry in 60 seconds, {error_details}")

                sleep(60)

    @staticmethod
    def _on_mqtt_connect(client, userdata, flags, rc):
        if rc == 0:
            _LOGGER.info(f"MQTT Broker connected with result code {rc}")

            client.subscribe(f"{userdata.topic_command_prefix}#")

        else:
            error_message = MQTT_ERROR_MESSAGES.get(rc, MQTT_ERROR_DEFAULT_MESSAGE)

            _LOGGER.error(f"MQTT Broker failed due to {error_message}")

            asyncio.get_event_loop().stop()

    @staticmethod
    def _on_mqtt_message(client, userdata, msg):
        _LOGGER.debug(f"MQTT Message received, Topic: {msg.topic}, Payload: {msg.payload}")

        try:
            payload = {}

            if msg.payload is not None:
                data = msg.payload.decode("utf-8")

                if data is not None and len(data) > 0:
                    payload = json.loads(data)

            topic = msg.topic.replace(userdata.topic_command_prefix, "")

            userdata.on_message(userdata.manager, topic, payload)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()

            _LOGGER.error(
                f"Failed to invoke handler, "
                f"Topic: {msg.topic}, Payload: {msg.payload}, "
                f"Error: {ex}, Line: {exc_tb.tb_lineno}"
            )

    @staticmethod
    def _on_mqtt_disconnect(client, userdata, rc):
        reason = MQTT_ERROR_MESSAGES.get(rc, MQTT_ERROR_DEFAULT_MESSAGE)

        _LOGGER.warning(f"MQTT Broker got disconnected, Reason Code: {rc} - {reason}")

    def publish(self, topic_suffix: str, payload: dict):
        topic = f"{self.topic_prefix}/{topic_suffix}"
        _LOGGER.debug(f"Publishing MQTT message {topic}: {payload}")

        try:
            self._mqtt_client.publish(topic, json.dumps(payload, indent=4))
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()

            _LOGGER.error(
                f"Failed to publish message, "
                f"Topic: {topic}, Payload: {payload}, "
                f"Error: {ex}, Line: {exc_tb.tb_lineno}"
            )
