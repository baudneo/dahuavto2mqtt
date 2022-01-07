import os
from typing import Optional, Dict

from common.consts import *


class MQTTConfigurationData:
    host: Optional[str]
    username: Optional[str]
    password: Optional[str]
    port: Optional[int]
    topic_prefix: Optional[str]
    topic_command_prefix: Optional[str]

    def __init__(self):
        self.client_id = os.environ.get('MQTT_BROKER_CLIENT_ID', DEFAULT_MQTT_CLIENT_ID)
        self.host = os.environ.get('MQTT_BROKER_HOST')
        self.port = os.environ.get('MQTT_BROKER_PORT', 1883)
        self.username = os.environ.get('MQTT_BROKER_USERNAME')
        self.password = os.environ.get('MQTT_BROKER_PASSWORD')

        self.topic_prefix = os.environ.get('MQTT_BROKER_TOPIC_PREFIX', DEFAULT_MQTT_TOPIC_PREFIX)
        self.topic_command_prefix = f"{self.topic_prefix}{TOPIC_COMMAND}/"
