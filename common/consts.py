
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
    1: "MQTT Broker failed to connect: incorrect protocol version",
    2: "MQTT Broker failed to connect: invalid client identifier",
    3: "MQTT Broker failed to connect: server unavailable",
    4: "MQTT Broker failed to connect: bad username or password",
    5: "MQTT Broker failed to connect: not authorised"
}

TOPIC_COMMAND = "/Command"
TOPIC_DOOR = "Open"
TOPIC_MUTE = "Mute"
