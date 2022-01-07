#!/usr/bin/env python3

import os
import sys
import logging
import asyncio
from time import sleep

from clients.DahuaClient import DahuaClient

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
        self._host = os.environ.get('DAHUA_VTO_HOST')

    def initialize(self):
        while True:
            try:
                _LOGGER.info("Connecting")

                loop = asyncio.new_event_loop()

                client = loop.create_connection(DahuaClient, self._host, 5000)
                loop.run_until_complete(client)
                loop.run_forever()
                loop.close()

                _LOGGER.warning("Disconnected, will try to connect in 5 seconds")

                sleep(5)

            except Exception as ex:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                line = exc_tb.tb_lineno

                _LOGGER.error(f"Connection failed will try to connect in 30 seconds, error: {ex}, Line: {line}")

                sleep(30)


manager = DahuaVTOManager()
manager.initialize()
