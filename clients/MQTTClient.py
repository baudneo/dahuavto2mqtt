import asyncio
import json
import logging
import sys
from time import sleep
from typing import Callable, Any

import paho.mqtt.client as mqtt

from common.consts import *
from models.MQTTConfigData import MQTTConfigurationData

_LOGGER = logging.getLogger(__name__)


class MQTTClient(asyncio.Protocol):
    mqtt_config: MQTTConfigurationData
    on_message: Callable[[Any, str, dict], None]
    manager: Any

    def __init__(self, manager, on_message: Callable[[Any, str, dict], None]):
        self.manager = manager
        self.mqtt_config = MQTTConfigurationData()
        self._mqtt_client = mqtt.Client(self.mqtt_config.client_id)
        self.on_message = on_message

    def initialize(self):
        _LOGGER.info("Initializing MQTT Broker")
        connected = False
        self._mqtt_client.user_data_set(self)

        self._mqtt_client.username_pw_set(self.mqtt_config.username, self.mqtt_config.password)

        self._mqtt_client.on_connect = self.on_mqtt_connect
        self._mqtt_client.on_message = self.on_mqtt_message
        self._mqtt_client.on_disconnect = self.on_mqtt_disconnect

        while not connected:
            try:
                _LOGGER.info("MQTT Broker is trying to connect...")

                self._mqtt_client.connect(self.mqtt_config.host, int(self.mqtt_config.port), 60)
                self._mqtt_client.loop_start()

                connected = True

            except Exception as ex:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                error_details = f"error: {ex}, Line: {exc_tb.tb_lineno}"

                _LOGGER.error(f"Failed to connect to broker, retry in 60 seconds, {error_details}")

                sleep(60)

    @staticmethod
    def on_mqtt_connect(client, userdata, flags, rc):
        if rc == 0:
            _LOGGER.info(f"MQTT Broker connected with result code {rc}")

            client.subscribe(f"{userdata.mqtt_config.topic_command_prefix}#")

        else:
            error_message = MQTT_ERROR_MESSAGES.get(rc, MQTT_ERROR_DEFAULT_MESSAGE)

            _LOGGER.error(error_message)

            asyncio.get_event_loop().stop()

    @staticmethod
    def on_mqtt_message(client, userdata, msg):
        _LOGGER.debug(f"MQTT Message received, Topic: {msg.topic}, Payload: {msg.payload}")

        try:
            payload = None

            if msg.payload is not None:
                data = msg.payload.decode("utf-8")

                if data is not None and len(data) > 0:
                    payload = json.loads(data)

            topic = msg.topic.replace(userdata.mqtt_config.topic_command_prefix, "")

            userdata.on_message(userdata.manager, topic, payload)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()

            _LOGGER.error(
                f"Failed to invoke handler, "
                f"Topic: {msg.topic}, Payload: {msg.payload}, "
                f"Error: {ex}, Line: {exc_tb.tb_lineno}"
            )

    @staticmethod
    def on_mqtt_disconnect(client, userdata, rc):
        _LOGGER.warning(f"MQTT Broker got disconnected, will try to reconnect in 1 minute...")
        sleep(60)

        connected = False

        while not connected:
            try:
                _LOGGER.info(f"MQTT Broker - trying to reconnect...")

                client.connect(userdata.mqtt_config.host, int(userdata.mqtt_config.port), 60)
                client.loop_start()

                connected = True

            except Exception as ex:
                exc_type, exc_obj, exc_tb = sys.exc_info()

                _LOGGER.error(f"Failed to reconnect, retry in 60 seconds, error: {ex}, Line: {exc_tb.tb_lineno}")

                sleep(60)

    def publish(self, topic_suffix: str, payload: dict):
        topic = f"{self.mqtt_config.topic_prefix}/{topic_suffix}"
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
