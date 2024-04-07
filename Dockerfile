FROM python:3.12.2-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY ./requirements.txt /tmp

RUN set -x \
    && apk update \
    && apk add --no-cache curl \
    && cat <<EOF > /tmp/pip.conf
[install]
compile = no

[global]
no-cache-dir = True
EOF

RUN set -x \
    && pip install -r /tmp/requirements.txt

ENV DAHUA_VTO_HOST=DeviceIP
ENV DAHUA_VTO_USERNAME=DeviceUsername
ENV DAHUA_VTO_PASSWORD=DevicePassword
ENV MQTT_BROKER_HOST=mqtt-host
ENV MQTT_BROKER_PORT=1883
ENV MQTT_BROKER_USERNAME=MQTTUsername
ENV MQTT_BROKER_PASSWORD=MQTTPassword
ENV MQTT_BROKER_TOPIC_PREFIX=DahuaVTO
ENV MQTT_BROKER_CLIENT_ID=DahuaVTO2MQTT
ENV MQTT_DEBUG=False
ENV API_DEBUG=False
ENV KEEPALIVE_DEBUG=False
ENV TZ=America/Chicago

COPY ./clients/ /app/clients/
COPY ./common/ /app/common/
COPY ./models/ /app/models/
COPY ./DahuaVTO.py /app

LABEL org.opencontainers.image.source = "https://github.com/baudneo/dahuavto2mqtt"

ENTRYPOINT ["python3", "/app/DahuaVTO.py"]