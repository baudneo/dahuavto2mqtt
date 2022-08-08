import asyncio
import logging
import sys
from time import sleep
from typing import Optional

from clients.BaseClient import BaseClient
from clients.DahuaAPI import DahuaAPI
from models.DahuaConfigData import DahuaConfigurationData

_LOGGER = logging.getLogger(__name__)


class DahuaClient(BaseClient):
    def __init__(self):
        super().__init__("Dahua")

        self.dahua_config = DahuaConfigurationData()
        self.api: Optional[DahuaAPI] = None

    def _set_api(self, api: DahuaAPI):
        self.api = api

    def _connect(self):
        super(DahuaClient, self)._connect()

        while not self.is_connected:
            sleep_time = 5

            try:
                _LOGGER.info("Connecting")

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

                _LOGGER.error(f"Connection failed, Error: {ex}, Line: {line}")

                sleep_time = 30

            finally:
                _LOGGER.info(f"Disconnected, will try to connect in {sleep_time} seconds")

                self.is_connected = False

                sleep(sleep_time)

    def _event_received(self, data):
        super(DahuaClient, self)._event_received(data)

        topic = data.get("topic")
        payload = data.get("payload")

        self.api.handle_action(topic, payload)

