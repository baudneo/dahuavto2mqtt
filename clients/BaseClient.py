import queue
import logging

from threading import Timer
from typing import Optional


_LOGGER = logging.getLogger(__name__)


class BaseClient:
    def __init__(self, client_name):
        self.client_name = client_name
        self.is_connected = False
        self.is_running = True
        self._timer_listen: Optional[Timer] = None
        self._timer_connect: Optional[Timer] = None
        self._incoming_events = None
        self.outgoing_events = queue.Queue()

    @property
    def should_connect(self):
        return self.is_running and not self.is_connected

    def initialize(self, incoming_events: queue.Queue):
        _LOGGER.info(f"Initialize {self.client_name}Client")

        self._incoming_events = incoming_events

        self._timer_listen = Timer(1.0, self._listen)
        self._timer_listen.start()

        self.connect()

    def terminate(self):
        _LOGGER.info(f"Terminating {self.client_name}Client")

        self.is_connected = False
        self.is_running = False

        self.outgoing_events.empty()
        self.outgoing_events = None

    def connect(self):
        _LOGGER.info(f"Starting to connect {self.client_name}Client, Should connect: {self.should_connect}")

        if self.should_connect:
            self._timer_connect = Timer(1.0, self._connect)
            self._timer_connect.start()

    def _connect(self):
        if not self.is_running:
            self.terminate()

    def _listen(self):
        if self.is_running:
            data = self._incoming_events.get()

            if data is None:
                self.terminate()

            else:
                self._event_received(data)

                self._incoming_events.task_done()

                self._timer_listen = Timer(0, self._listen)
                self._timer_listen.start()

    def _event_received(self, data):
        _LOGGER.debug(f"{self.client_name}Client Event received, Data: {data}")
