#!/usr/bin/env python3

import os
import sys
import logging
from time import sleep

from clients.DahuaClient import DahuaClient
from clients.MQTTClient import MQTTClient

DEBUG = str(os.environ.get('DEBUG', False)).lower() == str(True).lower()

log_level = logging.DEBUG if DEBUG else logging.INFO

root = logging.getLogger()
root.setLevel(log_level)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(log_level)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
stream_handler.setFormatter(formatter)
root.addHandler(stream_handler)

_LOGGER = logging.getLogger(__name__)


class DahuaVTOManager:
    def __init__(self):
        self._mqtt_client = MQTTClient()
        self._dahua_client = DahuaClient()

    def initialize(self):
        self._mqtt_client.initialize(self._dahua_client.outgoing_events)
        self._dahua_client.initialize(self._mqtt_client.outgoing_events)

        while True:
            sleep(1)


manager = DahuaVTOManager()
manager.initialize()
