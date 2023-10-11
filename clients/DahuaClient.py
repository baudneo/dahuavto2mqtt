import asyncio
import logging
import sys
from time import sleep
from typing import Optional

from clients.BaseClient import BaseClient
from clients.DahuaAPI import DahuaAPI
from common.consts import API_DEBUG
from models.DahuaConfigData import DahuaConfigurationData

logger = logging.getLogger(__name__)


class DahuaClient(BaseClient):
    def __init__(self):
        super().__init__("Dahua")

        self.dahua_config = DahuaConfigurationData()
        self.api: Optional[DahuaAPI] = None
        logger.info(f"{API_DEBUG=}")
        if API_DEBUG is True:
            logger.setLevel(logging.DEBUG)
            for handler in logger.handlers:
                handler.setLevel(logging.DEBUG)
            logger.info(f"Set DEBUG level for {__name__}")
        else:
            logger.setLevel(logging.INFO)
            for handler in logger.handlers:
                handler.setLevel(logging.INFO)
            logger.info(f"Set INFO level for {__name__}")

    def _set_api(self, api: DahuaAPI):
        self.api = api

    def _connect(self):
        super(DahuaClient, self)._connect()

        while not self.is_connected:
            sleep_time = 5

            try:
                logger.info("Connecting")

                loop = asyncio.new_event_loop()

                client = loop.create_connection(
                    lambda: DahuaAPI(self.outgoing_events, self.dahua_config, self._set_api),
                    self.dahua_config.host,
                    5000
                )

                self.is_connected = True

                loop.run_until_complete(client)
                loop.run_forever()
                loop.close()

            except Exception as ex:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                line = exc_tb.tb_lineno

                logger.error(f"Connection failed, Error: {ex}, Line: {line}")

                sleep_time = 30

            finally:
                logger.info(f"Disconnected, will try to connect in {sleep_time} seconds")

                self.is_connected = False

                sleep(sleep_time)
                self.connect()

    def _event_received(self, data):
        super(DahuaClient, self)._event_received(data)

        topic = data.get("topic")
        payload = data.get("payload")

        self.api.handle_action(topic, payload)

