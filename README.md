# DahuaVTO2MQTT
Listens to events from all Dahua devices - VTO, Camera, NVR unit and publishes them via MQTT Message

[Change log](https://gitlab.com/elad.bar/DahuaVTO2MQTT/-/blob/master/CHANGELOG.md)

[Dahua VTO MQTT Events - examples](https://gitlab.com/elad.bar/DahuaVTO2MQTT/-/blob/master/MQTTEvents.MD)

## How to install
### Docker Compose
```dockerfile
version: '3'
services:
  dahuavto2mqtt:
    image: "registry.gitlab.com/elad.bar/dahuavto2mqtt:latest"
    container_name: "dahuavto2mqtt"
    hostname: "dahuavto2mqtt"
    restart: "unless-stopped"
    environment:
      - DAHUA_VTO_HOST=vto-host
      - DAHUA_VTO_USERNAME=Username
      - DAHUA_VTO_PASSWORD=Password
      - MQTT_BROKER_HOST=mqtt-host
      - MQTT_BROKER_PORT=1883
      - MQTT_BROKER_USERNAME=Username
      - MQTT_BROKER_PASSWORD=Password 
      - MQTT_BROKER_TOPIC_PREFIX=DahuaVTO
      - MQTT_BROKER_CLIENT_ID=DahuaVTO2MQTT
      - DEBUG=False      
```

### Environment Variables
| Variable                 | Default       | Required | Description                |
|--------------------------|---------------|----------|----------------------------|
| DAHUA_VTO_HOST           | -             | +        | Dahua VTO hostname or IP   |
| DAHUA_VTO_USERNAME       | -             | +        | Dahua VTO user name        |
| DAHUA_VTO_PASSWORD       | -             | +        | Dahua VTO password         |
| MQTT_BROKER_HOST         | -             | +        | MQTT Broker hostname or IP |
| MQTT_BROKER_PORT         | -             | +        | MQTT Broker port           |
| MQTT_BROKER_USERNAME     | -             | +        | MQTT Broker user name      |
| MQTT_BROKER_PASSWORD     | -             | +        | MQTT Broker password       |
| MQTT_BROKER_TOPIC_PREFIX | DahuaVTO      | -        | Topic to publish messages  |
| MQTT_BROKER_CLIENT_ID    | DahuaVTO2MQTT | -        | MQTT Broker client ID      |
| DEBUG                    | false         | -        | Enable debug log messages  |

## Commands

#### Open Door
By publishing MQTT message of {MQTT_BROKER_TOPIC_PREFIX}/Command/Open an HTTP request to the unit will be sent,
If the payload of the message is empty, default door to open is 1,
If unit supports more than 1 door, please add to the payload `Door` parameter with the number of the door 

## Credits
All credits goes to <a href="https://github.com/riogrande75">@riogrande75</a> who wrote that complicated integration
Original code can be found in <a href="https://github.com/riogrande75/Dahua">@riogrande75/Dahua</a>
