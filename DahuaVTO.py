#!/usr/bin/env python3

import sys
import logging
from time import sleep

from clients.DahuaClient import DahuaClient
from clients.MQTTClient import MQTTClient


class DahuaVTOManager:
    def __init__(self):
        self._mqtt_client = MQTTClient()
        self._dahua_client = DahuaClient()

    def initialize(self):
        self._mqtt_client.initialize(self._dahua_client.outgoing_events)
        self._dahua_client.initialize(self._mqtt_client.outgoing_events)

        while True:
            sleep(1)


if __name__ == "__main__":
    log_level = logging.DEBUG
    root = logging.getLogger()
    root.setLevel(log_level)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)
    formatter = logging.Formatter(
        "'%(asctime)s.%(msecs)04d' " "%(levelname)s %(module)s:%(lineno)d -> %(message)s",
        "%m/%d/%y %H:%M:%S",
    )
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    logger = logging.getLogger(__name__)

    manager = DahuaVTOManager()
    manager.initialize()
