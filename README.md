# DahuaVTO2MQTT
Listens to events from all Dahua devices - VTO, Camera, NVR unit and publishes them via MQTT Message

[Change log](./CHANGELOG.md)

[Dahua VTO MQTT Events - examples](docs/MQTTEvents.md)

[Supported Models](docs/SupportedModels.md)

## Notes
- **Lorex 2k Doorbell username is always** `admin`
- **Lorex 2k Doorbell password is whatever you set it to in the lorex mobile app**

## How to install
### Docker Compose
```docker
#version: '3'
services:
  dahuavto2mqtt:
    image: "baudneo/dahuavto2mqtt:latest"
    container_name: "dahuavto2mqtt"
    hostname: "dahuavto2mqtt"
    restart: "unless-stopped"
    environment:
      DAHUA_VTO_HOST: ip.of.vto.host
      DAHUA_VTO_USERNAME: Username
      DAHUA_VTO_PASSWORD: Password
      MQTT_BROKER_HOST: mqtt-host
      MQTT_BROKER_PORT: 1883
      MQTT_BROKER_USERNAME: Username
      MQTT_BROKER_PASSWORD: Password 
      MQTT_BROKER_TOPIC_PREFIX: DahuaVTO
      MQTT_BROKER_CLIENT_ID: DahuaVTO2MQTT
      MQTT_DEBUG: False
      API_DEBUG: False
      KEEPALIVE_DEBUG: False
      TZ: America/Chicago
```

Copy the above code into a file called `docker-compose.yml` and run 
`docker-compose up -d` in the same directory as the file. For logs, run 
`docker-compose logs -f` (Ctrl+C to exit logs) in the same directory as the file.

### Environment Variables
| Variable                   | Default         | Required | Description                                                     |
|----------------------------|-----------------|----------|-----------------------------------------------------------------|
| `DAHUA_VTO_HOST`           | -               | +        | Dahua VTO hostname or IP                                        |
| `DAHUA_VTO_USERNAME`       | -               | +        | Dahua VTO user name                                             |
| `DAHUA_VTO_PASSWORD`       | -               | +        | Dahua VTO password                                              |
| `MQTT_BROKER_HOST`         | -               | +        | MQTT Broker hostname or IP                                      |
| `MQTT_BROKER_PORT`         | -               | +        | MQTT Broker port                                                |
| `MQTT_BROKER_USERNAME`     | -               | +        | MQTT Broker user name                                           |
| `MQTT_BROKER_PASSWORD`     | -               | +        | MQTT Broker password                                            |
| `MQTT_BROKER_TOPIC_PREFIX` | DahuaVTO        | -        | Topic to publish messages                                       |
| `MQTT_BROKER_CLIENT_ID`    | DahuaVTO2MQTT   | -        | MQTT Broker client ID                                           |
| `API_DEBUG`                | false           | -        | Enable debug log messages for the connection to the VTO device  |
| `MQTT_DEBUG`               | false           | -        | Enable debug log messages for the connection to the MQTT broker |
| `KEEPALIVE_DEBUG`          | false           | -        | Enable debug log messages for keepalive packets                 |
| `TZ`                       | America/Chicago | -        | Timezone for proper logging timestamp                           |

## Commands

#### Open Door
By publishing MQTT message of {MQTT_BROKER_TOPIC_PREFIX}/Command/Open an HTTP request to the unit will be sent,
If the payload of the message is empty, default door to open is 1,
If unit supports more than 1 door, please add to the payload `Door` parameter with the number of the door 

## Home Assistant automations

### Doorbell press
If you changed the dahua topic (env: MQTT_BROKER_TOPIC_PREFIX), make sure to edit it from the below images: `DahuaVTO/`.

#### lorex2k doorbell
![Home Assistant automation example](./docs/assets/doorbell_press.png)


### Person detected

#### lorex2k doorbell
![Home Assistant automation example](./docs/assets/person_detected.png)


## Credits
- Elad Bar - [elad-bar](https://gitlab.com/elad.bar) - [DahuaVTO2MQTT](https://gitlab.com/elad.bar/DahuaVTO2MQTT)

All credits goes to [@riogrande](https://github.com/riogrande75) who wrote that complicated integration
Original code can be found in [@riogrande75/Dahua](https://github.com/riogrande75/Dahua)


