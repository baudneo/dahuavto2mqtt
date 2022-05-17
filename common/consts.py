DEFAULT_MQTT_CLIENT_ID = "DahuaVTO2MQTT"
DEFAULT_MQTT_TOPIC_PREFIX = "DahuaVTO"

PROTOCOLS = {
    True: "https",
    False: "http"
}

DAHUA_DEVICE_TYPE = "deviceType"
DAHUA_SERIAL_NUMBER = "serialNumber"
DAHUA_VERSION = "version"
DAHUA_BUILD_DATE = "buildDate"

DAHUA_CONSOLE_RUN_CMD = "console.runCmd"
DAHUA_GLOBAL_LOGIN = "global.login"
DAHUA_GLOBAL_KEEPALIVE = "global.keepAlive"
DAHUA_EVENT_MANAGER_ATTACH = "eventManager.attach"
DAHUA_CONFIG_MANAGER_GETCONFIG = "configManager.getConfig"
DAHUA_MAGICBOX_GETSOFTWAREVERSION = "magicBox.getSoftwareVersion"
DAHUA_MAGICBOX_GETDEVICETYPE = "magicBox.getDeviceType"

DAHUA_ALLOWED_DETAILS = [
    DAHUA_DEVICE_TYPE,
    DAHUA_SERIAL_NUMBER
]

ENDPOINT_ACCESS_CONTROL = "accessControl.cgi?action=openDoor&UserID=101&Type=Remote&channel="
ENDPOINT_MAGICBOX_SYSINFO = "magicBox.cgi?action=getSystemInfo"

MQTT_ERROR_DEFAULT_MESSAGE = "Unknown error"

MQTT_ERROR_MESSAGES = {
    0: "MQTT Broker connected successfully",
    1: "Incorrect protocol version",
    2: "Invalid client identifier",
    3: "Server unavailable",
    4: "Bad username or password",
    5: "Not authorised",
    6: "Message not found (internal error)",
    7: "The connection was lost",
    8: "A TLS error occurred",
    9: "Payload too large",
    10: "This feature is not supported",
    11: "Authorisation failed",
    12: "Access denied by ACL",
    13: "Unknown error",
    14: "Error defined by errno",
    15: "Queue size",
}

TOPIC_COMMAND = "/Command"
TOPIC_DOOR = "Open"
TOPIC_MUTE = "Mute"
