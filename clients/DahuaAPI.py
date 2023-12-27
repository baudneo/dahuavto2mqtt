from __future__ import annotations
import asyncio
import hashlib
import json
import logging
import os
import queue
import struct
import sys
from threading import Timer
from typing import Optional, Dict, Any, Callable, AnyStr, TYPE_CHECKING

import requests

from common.consts import *

if TYPE_CHECKING:
    from models.DahuaConfigData import DahuaConfigurationData

logger = logging.getLogger(__name__)


class AccessControl:
    lp: str = "access ctrl::"

    def send(self, action, handler, params=None):
        """
            Get the access control configuration from the VTO device by sending a request and setting a callback.

        :return: Nothing
        """
        logger.info(f"{self.lp} Requesting configuration ({self.access_control_attempts}/{ACCESS_CONTROL_ATTEMPTS})...")

        request_data = {
            "name": "AccessControl"
        }

        # self.send(DAHUA_CONFIG_MANAGER_GETCONFIG, handle_access_control, request_data)


    def handler(self, *args, **kwargs):
        self.__call__(*args, **kwargs)

    def __call__(self, message: Dict[str, Any], *args, **kwargs):
        """
            Handle the access control response from the VTO device.
        :param message:
        :return: Nothing
        """
        # {
        # 'error': {'code': 268959743, 'message': 'Unknown error! error code was not set in service!'},
        # 'id': 4,
        # 'params': {'table': None},
        # 'result': False,
        # 'session': 1639873003
        # }
        lp = "access ctrl:hndl::"
        params = message.get("params")
        success = message.get("result")
        error = message.get("error", "<No error message returned!>")
        if success is False:
            logger.warning(f"{lp} The response data 'result' is False, the request was unsuccessful. Error message from device: {error}")
            # self.load_access_control()
            return
        if params:
            logger.debug(f"{lp} Params: {params}")
            table = params.get("table")
            if table:
                logger.debug(f"{lp} Table: {table}")
                for item in table:
                    logger.info(f"{lp} Table Item: {item}")
                    access_control = item.get('AccessProtocol')
                    if access_control:
                        logger.info(f"{lp} Access Control: {access_control}")
                        if access_control == 'Local':
                            self.hold_time = item.get('UnlockReloadInterval')
                            logger.info(f"{lp} Hold time: {self.hold_time}")
                            return
                    else:
                        logger.warning(f"{lp} Access Control (AccessProtocol) is not available in the table item!")

        logger.warning(f"{lp} No access control details available")
        # if self.access_control_attempts < ACCESS_CONTROL_ATTEMPTS:
        #     logger.info(f"{lp} Trying again!")
        #     self.access_control_attempts += 1
        #     self.load_access_control()
        # else:
        #     logger.critical(f"{lp} Giving up, exhausted attempts: {ACCESS_CONTROL_ATTEMPTS}!")


class DahuaAPI(asyncio.Protocol):
    dahua_config: DahuaConfigurationData

    requestId: int
    sessionId: int
    keep_alive_interval: int
    realm: Optional[str]
    random: Optional[str]
    dahua_details: Dict[str, Any]
    hold_time: int
    lock_status: Dict[int, bool]
    data_handlers: Dict[Any, Callable[[Any, str], None]]
    event_handlers: Dict[str, Callable[[dict], None]]

    access_control_attempts: int = 1
    version_attempts: int = 1
    serial_number_attempts: int = 1
    device_type_attempts: int = 1

    device_type: str = ""
    serial_number: str = ""


    def __init__(self, outgoing_events: queue.Queue, dahua_config: DahuaConfigurationData, set_api):
        self.dahua_config = dahua_config
        self.dahua_details = {}

        self.realm = None
        self.random = None
        self.request_id = 1
        self.sessionId = 0
        self.keep_alive_interval = 0
        self.transport: Optional[asyncio.Transport] = None
        self.hold_time = 0
        self.lock_status = {}
        self.data_handlers = {}
        self.event_handlers = {
            TOPIC_DOOR: self.access_control_open_door,
            TOPIC_MUTE: self.run_cmd_mute
        }

        self._loop = asyncio.get_event_loop()
        self.outgoing_events = outgoing_events

        set_api(self)
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


    def handle_action(self, topic: str, payload: dict):
        try:
            if topic in self.event_handlers:
                action = self.event_handlers[topic]
                action(payload)
            else:
                logger.warning(f"No MQTT message handler for {topic}, Payload: {payload}")
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()

            logger.error(f"Failed to handle callback, error: {ex}, Line: {exc_tb.tb_lineno}")

    def connection_made(self, transport: asyncio.Transport):
        lp: str = "connection_made::"
        logger.info(f"{lp} Established")

        try:
            self.transport = transport

            self.pre_login()

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()

            logger.error(f"Failed to handle message, error: {ex}, Line: {exc_tb.tb_lineno}")

    def data_received(self, data):
        lp: str = "received::"
        try:
            message = self.parse_response(data)
            if message is not None and isinstance(message, dict):
                # {
                #   'error': {
                #           'code': 268959743,
                #           'message': 'Unknown error! error code was not set in service!'
                #           },
                #   'id': 4,
                #   'params': {'table': None},
                #   'result': False,
                #   'session': 1149542436
                # }
                message_id = message.get("id")
                # Skip displaying keep alive responses
                params = message.get("params")
                method = message.get("method")
                if params and params.get("timeout") is not None:
                    pass
                elif method and method == "client.notifyEventStream":
                    pass
                else:
                    logger.debug(f"{lp} from VTO: {message}")


                if self.data_handlers:
                    handler: Optional[Callable] = self.data_handlers.get(message_id, self.handle_default)
                    if handler:
                        # logger.info(f"{lp} Handling message id: {message_id} with handler: {handler}")
                        try:
                            handler(message)
                        except Exception as ex:
                            exc_type, exc_obj, exc_tb = sys.exc_info()

                            logger.error(f"{lp} Failed to handle message: {message_id} - error: {ex}, Line: {exc_tb.tb_lineno}")
                            logger.warning(f"{lp} If this was an access control handler, there is nothing to worry about as Lorex/Amcrest doorbells dont have AccessControl!")

                    else:
                        logger.warning(f"{lp} No data handlers for message id: {message_id}")
                else:
                    logger.warning(f"{lp} No data handlers are available at all")
            else:
                logger.warning(f"{lp} Failed to parse data: {data}")

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()

            logger.error(f"{lp} Failed to handle message: {message_id} - error: {ex}, Line: {exc_tb.tb_lineno}")
            raise ex

    def handle_notify_event_stream(self, params):
        lp: str = "handle_notify_event_stream::"
        try:
            event_list = params.get("eventList")

            for message in event_list:
                code = message.get("Code")

                for k in self.dahua_details:
                    if k in DAHUA_ALLOWED_DETAILS:
                        message[k] = self.dahua_details.get(k)

                event_data = {
                    "event": f"{code}/Event",
                    "payload": message
                }

                self.outgoing_events.put(event_data)

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()

            logger.error(f"Failed to handle event, error: {ex}, Line: {exc_tb.tb_lineno}")

    def handle_default(self, message):
        logger.info(f"Data received without handler: {message}")

    def stop(self):
        lp: str = "stop::"
        if self.transport is not None:
            if self.transport.is_closing():
                logger.warning(f"{lp} transport Connection is already closing")
            else:
                self.transport.close()
        if self._loop.is_running():
            self._loop.stop()

    def eof_received(self):
        logger.info('Server sent EOF message')

        self.stop()

    def connection_lost(self, exc):
        logger.error('Server closed the connection')

        self.stop()

    def send(self, action, handler, params=None):
        lp: str = "send::"
        if params is None:
            params = {}

        self.request_id += 1

        message_data = {
            "id": self.request_id,
            "session": self.sessionId,
            "magic": "0x1234",
            "method": action,
            "params": params
        }
        # logger.info(f"Setting CALLBACK data handler for message ID {self.request_id}: {handler}")
        self.data_handlers[self.request_id] = handler
        if not self.transport.is_closing():
            message = self.convert_message(message_data)
            if action != DAHUA_GLOBAL_KEEPALIVE:
                logger.debug(f"{lp} to VTO: {message_data}")
            self.transport.write(message)

        else:
            logger.warning(f"{lp} Connection to VTO device is closed! Unable to send data!")

    @staticmethod
    def convert_message(data):
        message_data = json.dumps(data, indent=4)

        header = struct.pack(">L", 0x20000000)
        header += struct.pack(">L", 0x44484950)
        header += struct.pack(">d", 0)
        header += struct.pack("<L", len(message_data))
        header += struct.pack("<L", 0)
        header += struct.pack("<L", len(message_data))
        header += struct.pack("<L", 0)

        message = header + message_data.encode("utf-8")

        return message

    def pre_login(self):
        """First message we send is pre_login, this will give us the random, realm and session ID
         to use for the login message.

            The pre_login message is sent without a password, the login message is sent with a hashed password.

         """
        lp: str = "pre_login::"
        logger.info(f"{lp} Preparing first message to elicit a challenge...")

        def handle_pre_login(message: Dict[str, Any]):
            """Handle the pre_login response from the VTO device.

            :param message: The response from the VTO device converted to a dictionary.
            :return: Nothing
            """

            error = message.get("error")
            params = message.get("params")

            if error is not None:
                error_message = error.get("message")

                if error_message == "Component error: login challenge!":
                    self.random = params.get("random")
                    self.realm = params.get("realm")
                    self.sessionId = message.get("session")

                    self.login()
            else:
                logger.critical(f"{lp} Failed to get challenge from VTO device, error: {error}")
                self.stop()
                exit(1)

        request_data = {
            "clientType": "",
            "ipAddr": "(null)",
            "loginType": "Direct",
            "userName": self.dahua_config.username,
            "password": ""
        }

        self.send(DAHUA_GLOBAL_LOGIN, handle_pre_login, request_data)

    def login(self):
        """Login message, this will give us the keep alive interval and session ID to use for the keep alive message.

        The keep alive message is sent every keepAliveInterval-5 seconds to keep the session alive.

        Then, the following messages are sent to get the device details:
            - Access Control
            - Version
            - Serial Number
            - Device Type
            - Attach Event Manager

        """
        lp: str = "login::"
        logger.info(f"{lp} Challenge received, preparing request...")

        def handle_login(message):
            """
                Handle the login response from the VTO device. Setup the keep alive Timer.
            :param message:
            :return:
            """
            params = message.get("params")
            keep_alive_interval = params.get("keepAliveInterval")

            if keep_alive_interval is not None:
                self.keep_alive_interval = keep_alive_interval - 5
                # This is where the sequence happens, so
                # we should make the methods return True/False and retry on False

                self.load_version()
                self.load_serial_number()
                self.load_device_type()
                self.attach_event_manager()

                Timer(self.keep_alive_interval, self.keep_alive).start()

                # not needed for  Lorex/Amcrest Doorbells
                self.load_access_control()

        password = self._get_hashed_password(
            self.random,
            self.realm,
            self.dahua_config.username,
            self.dahua_config.password
        )

        request_data = {
            "clientType": "",
            "ipAddr": "(null)",
            "loginType": "Direct",
            "userName": self.dahua_config.username,
            "password": password,
            "authorityType": "Default"
        }

        self.send(DAHUA_GLOBAL_LOGIN, handle_login, request_data)

    def attach_event_manager(self):
        """
            Attach to the event manager to get the event stream.

        :return:
        """
        # Response from attaching to event manager
        # {'id': 7, 'params': {'SID': 513}, 'result': True, 'session': 828137599}
        lp: str = "event_manager::"
        logger.info(f"{lp} Attaching...")

        def handle_attach_event_manager(message):
            lp = "event manager:hndl::"
            method = message.get("method")
            params = message.get("params")
            logger.debug(f"{lp} Method: {method} Params: {params}")
            if method == "client.notifyEventStream":
                self.handle_notify_event_stream(params)
            else:
                logger.warning(f"{lp} Unknown method: {method}, unable to handle event!")

        request_data = {
            "codes": ['All']
        }

        self.send(DAHUA_EVENT_MANAGER_ATTACH, handle_attach_event_manager, request_data)

    def load_access_control(self):
        """
            Get the access control configuration from the VTO device by sending a request and setting a callback.

        :return: Nothing
        """
        lp: str = "access ctrl::"
        logger.info(f"{lp} Requesting configuration ({self.access_control_attempts}/{ACCESS_CONTROL_ATTEMPTS})...")

        def handle_access_control(message: Dict[str, Any]):
            """
                Handle the access control response from the VTO device.
            :param message:
            :return: Nothing
            """
            # {
            # 'error': {'code': 268959743, 'message': 'Unknown error! error code was not set in service!'},
            # 'id': 4,
            # 'params': {'table': None},
            # 'result': False,
            # 'session': 1639873003
            # }
            lp = "access ctrl:hndl::"
            params = message.get("params")
            success = message.get("result")
            if success is False:
                logger.warning(f"{lp} Failed to get access control details, trying again!")
                self.load_access_control()
                return
            if params:
                logger.debug(f"{lp} Params: {params}")
                table = params.get("table")
                if table:
                    logger.debug(f"{lp} Table: {table}")
                    for item in table:
                        logger.info(f"{lp} Table Item: {item}")
                        access_control = item.get('AccessProtocol')
                        if access_control:
                            logger.info(f"{lp} Access Control: {access_control}")
                            if access_control == 'Local':
                                self.hold_time = item.get('UnlockReloadInterval')
                                logger.info(f"{lp} Hold time: {self.hold_time}")
                                return
                        else:
                            logger.warning(f"{lp} Access Control (AccessProtocol) is not available in the table item!")

            logger.warning(f"{lp} No access control details available")
            if self.access_control_attempts < ACCESS_CONTROL_ATTEMPTS:
                logger.info(f"{lp} Trying again!")
                self.access_control_attempts += 1
                self.load_access_control()
            else:
                logger.critical(f"{lp} Giving up, exhausted attempts: {ACCESS_CONTROL_ATTEMPTS}!")

        request_data = {
            "name": "AccessControl"
        }

        self.send(DAHUA_CONFIG_MANAGER_GETCONFIG, handle_access_control, request_data)

    def load_version(self):
        """
            Get the version of the VTO device by sending a request and setting a callback handler.
        :return: Nothing
        """

        lp: str = "version::"
        logger.info(f"{lp} requesting ({self.version_attempts}/{VERSION_ATTEMPTS})...")

        def handle_version(message: dict):
            """Handle the version response from the VTO device.

            :param dict message: The response from the VTO device converted to a dictionary.
            :return: Nothing
            """
            lp = "version:hndl::"
            params = message.get("params")
            if params:
                version_details = params.get("version")
                if version_details:
                    build_date = version_details.get("BuildDate")
                    version = version_details.get("Version")
                    if any([build_date, version]):
                        self.dahua_details[DAHUA_VERSION] = version
                        self.dahua_details[DAHUA_BUILD_DATE] = build_date

                        logger.info(f"{lp} Version: {version}, Build Date: {build_date}")
                        return

            logger.warning(f"{lp} No version details available")
            if self.version_attempts < VERSION_ATTEMPTS:
                logger.info(f"{lp} Trying again!")
                self.version_attempts += 1
                self.load_version()
            else:
                logger.critical(f"{lp} Giving up, exhausted attempts: {VERSION_ATTEMPTS}!")
                self.stop()
                exit(1)

        self.send(DAHUA_MAGICBOX_GETSOFTWAREVERSION, handle_version)

    def load_device_type(self):
        """
            Get the device type of the VTO device by sending a request and setting a callback handler.
        :return: Nothing
        """
        lp: str = "device type::"
        logger.info(f"{lp} Requesting ({self.device_type_attempts}/{DEVICE_TYPE_ATTEMPTS})...")

        def handle_device_type(message: Dict[str, Any]):
            """
                Handle the device type response from the VTO device.
            :param message:
            :return: Nothing
            """
            lp: str = "device type:hndl::"
            params: Optional[Dict[str, Any]] = message.get("params")
            if params:
                device_type: Optional[AnyStr] = params.get("type")
                if device_type:
                    self.device_type = self.dahua_details[DAHUA_DEVICE_TYPE] = device_type

                    logger.info(f"{lp} Device Type: {device_type}")
                    return

            logger.warning(f"{lp} No device type available")
            if self.device_type_attempts < DEVICE_TYPE_ATTEMPTS:
                logger.info(f"{lp} Trying again!")
                self.device_type_attempts += 1
                self.load_device_type()
            else:
                logger.critical(f"{lp} Giving up, exhausted attempts: {DEVICE_TYPE_ATTEMPTS}!")
                self.stop()
                exit(1)

        self.send(DAHUA_MAGICBOX_GETDEVICETYPE, handle_device_type)

    def load_serial_number(self):
        """
            Get the serial number of the VTO device by sending a request and setting a callback handler.
        :return: Nothing
        """
        lp: str = "serial number::"
        logger.info(f"{lp} Requesting ({self.serial_number_attempts}/{SERIAL_NUMBER_ATTEMPTS})...")

        def handle_serial_number(message: Dict[str, Any]):
            """
                Handle the serial number response from the VTO device.
            :param message:
            :return:
            """
            lp: str = "serial number:hndl::"

            params = message.get("params")
            if params:
                table = params.get("table")
                if table:
                    serial_number = table.get("UUID")

                    self.dahua_details[DAHUA_SERIAL_NUMBER] = serial_number

                    logger.info(f"{lp} Serial Number: {serial_number}")
                    return

            logger.warning(f"{lp} No serial number available")
            if self.serial_number_attempts < SERIAL_NUMBER_ATTEMPTS:
                logger.info(f"{lp} Trying again!")
                self.serial_number_attempts += 1
                self.load_serial_number()
            else:
                logger.critical(f"{lp} Giving up, exhausted attempts: {SERIAL_NUMBER_ATTEMPTS - 1}!")
                self.stop()
                exit(1)

        request_data = {
            "name": "T2UServer"
        }

        self.send(DAHUA_CONFIG_MANAGER_GETCONFIG, handle_serial_number, request_data)

    def keep_alive(self):
        """
            Send a keep alive message to the VTO device to keep the session alive.
        :return:
        """
        lp: str = "keep_alive::"
        logger.debug(f"{lp} Sending packet") if KEEPALIVE_DEBUG else None

        def handle_keep_alive(message):
            """Handle the keep alive response from the VTO device.

            :param str message:
            """

            self.keepalive_timer = Timer(self.keep_alive_interval, self.keep_alive)
            self.keepalive_timer.start()

        request_data = {
            "timeout": self.keep_alive_interval,
            "action": True
        }

        self.send(DAHUA_GLOBAL_KEEPALIVE, handle_keep_alive, request_data)

    def run_cmd_mute(self, payload: dict):
        """
            A CallBack used to mute the VTO device.

        :param payload:
        :return: Nothing
        """
        lp: str = "run_cmd_mute::"
        logger.debug(f"{lp} Keep alive")

        def handle_run_cmd_mute(message: Dict[str, Any]):
            """
                Handle the run command mute response from the VTO device.
            :param message:
            :return: Nothing
            """
            lp: str = "run_cmd_mute:hndl::"
            logger.debug(f"{lp} message from VTO device: {message}")
            logger.info(f"{lp} Call was muted")

        request_data = {
            "command": "hc"
        }

        self.send(DAHUA_CONSOLE_RUN_CMD, handle_run_cmd_mute, request_data)

    def access_control_open_door(self, payload: dict):
        """
            A CallBack used to open the door using the Access Control API.

        :param payload:
        :return: Nothing
        """
        lp: str = "access_control_open_door::"
        door_id = payload.get("Door")
        if door_id is None:
            logger.warning(f"{lp} Door ID is not available, setting to id: 1")
            door_id = 1

        is_locked = self.lock_status.get(door_id, False)
        should_unlock = False
        logger.debug(f"{lp} Door #{door_id} is locked: {is_locked} || Should unlock: {should_unlock}")

        try:
            # todo: investigate this logic
            if is_locked:
                logger.info(f"{lp} Access Control - Door #{door_id} is already unlocked, ignoring request")

            else:
                is_locked = True
                should_unlock = True

                self.lock_status[door_id] = is_locked
                self.publish_lock_state(door_id, False)

                url = f"{self.dahua_config.base_url}{ENDPOINT_ACCESS_CONTROL}{door_id}"

                response = requests.get(url, verify=False, auth=self.dahua_config.auth)

                response.raise_for_status()

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()

            logger.error(f"Failed to open door, error: {ex}, Line: {exc_tb.tb_lineno}")
        finally:
            if should_unlock and is_locked:
                Timer(float(self.hold_time), self.magnetic_unlock, (self, door_id)).start()

    @staticmethod
    def magnetic_unlock(self, door_id):
        """
            A CallBack used to unlock the magnetic lock after the hold time has expired. Used in a threading.Timer object.
        :param self:
        :param door_id:
        :return: Nothing
        """

        self.lock_status[door_id] = False
        self.publish_lock_state(door_id, True)

    def publish_lock_state(self, door_id: int, is_locked: bool):
        """
            Publish the lock state to MQTT.
        :param door_id:
        :param is_locked:
        :return:  Nothing
        """
        lp: str = "publish_lock_state::"
        state = "Locked" if is_locked else "Unlocked"

        logger.info(f"{lp} Access Control - {state} magnetic lock #{door_id}")

        message = {
            "door": door_id,
            "isLocked": is_locked
        }

        event_data = {
            "event": "MagneticLock/Status",
            "payload": message
        }

        self.outgoing_events.put(event_data)

    @staticmethod
    def parse_response(response) -> Optional[Dict[str, Any]]:
        """
            Parse the response from the VTO device into JSON and then decode the JSON into a Python object.

        :param response:
        :return: A dictionary of the response data
        """
        # b' \x00\x00\x00DHIP\\\x89\x8eA\x07\x00\x00\x00{\x04\x00\x00\x00\x00\x00\x00{\x04\x00\x00\x00\x00\x00\x00{"id":7,"method":"client.notifyEventStream","params":{"SID":513,"eventList":[{"Action":"Start","Code":"CrossRegionDetection","Data":{"Action":"Appear","CfgRuleId":3,"Class":"Normal","CountInGroup":1,"DetectRegion":[[1692,44],[-1,3996],[-1,8185],[8188,8185],[6280,5401],[3116,5231]],"EventID":10065,"EventSeq":64,"FrameSequence":5409291,"GroupID":64,"LocaleTime":"2023-09-18 12:48:48","Mark":0,"Name":"IVS-1","Object":{"Action":"Appear","Age":0,"Angle":0,"Bag":0,"BagType":0,"BoundingBox":[2976,2688,5840,8160],"CarrierBag":0,"Center":[4408,5424],"Confidence":0,"DownClothes":0,"Express":0,"FaceFlag":0,"FaceRect":[0,0,0,0],"FrameSequence":5409291,"Gender":0,"Glass":0,"HairStyle":0,"HasHat":0,"Helmet":0,"HumanRect":[0,0,0,0],"LowerBodyColor":[0,0,0,0],"MainColor":[0,0,0,0],"MessengerBag":0,"ObjectID":4812,"ObjectType":"Human","Phone":0,"RelativeID":0,"SerialUUID":"","ShoulderBag":0,"Source":0.0,"Speed":0,"SpeedTypeInternal":0,"Umbrella":0,"UpClothes":0,"UpperBodyColor":[0,0,0,0],"UpperPattern":0},"PTS":43625989680.0,"Priority":0,"RuleID":3,"RuleId":1,"Source":-1.0,"Track":[],"UTC":1695041328,"UTCMS":10},"Index":0}]},"session":1099860316}\n',
        # error: substring not found, Line: 759
        result = None
        try:
            response_parts = str(response).split("\\x00")
            for response_part in response_parts:
                if response_part.startswith("{"):
                    end = response_part.rindex("}") + 1
                    message = response_part[0:end]

                    result = json.loads(message)

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()

            logger.error(f"Failed to read data: {response}, error: {e}, Line: {exc_tb.tb_lineno}")

        return result

    @staticmethod
    def _get_hashed_password(random, realm, username, password):
        """
            Hash the password using the random, realm and username. Uses MD5 hashing.

        :param random:
        :param realm:
        :param username:
        :param password:
        :return: a byte string of the hashed password

        """
        password_str = f"{username}:{realm}:{password}"
        password_bytes = password_str.encode('utf-8')
        password_hash = hashlib.md5(password_bytes).hexdigest().upper()

        random_str = f"{username}:{random}:{password_hash}"
        random_bytes = random_str.encode('utf-8')
        random_hash = hashlib.md5(random_bytes).hexdigest().upper()

        return random_hash
