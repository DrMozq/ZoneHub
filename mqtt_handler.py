import json
import time
from paho.mqtt.client import Client
from paho.mqtt.enums import CallbackAPIVersion
from settings import logger, settings
from database import update_tag_location

# Хранилище последних позиций (временно в памяти)
last_tags = {}


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.success("Успешное подключение к брокеру")
        client.subscribe("+/ble_tags")
    else:
        logger.error(f"Ошибка подключения, код: {rc}")


def on_message(client, userdata, msg):
    try:
        gateway_name = msg.topic.split('/')[0]
        payload = json.loads(msg.payload.decode())

        for device in payload.get("devices", []):
            mac = device["mac"]
            rssi = device["rssi"]
            now = time.time()

            # Логика определения зоны
            if mac not in last_tags or rssi > last_tags[mac]['rssi'] or (now - last_tags[mac]['time']) > 15:
                last_tags[mac] = {'gateway': gateway_name, 'rssi': rssi, 'time': now}

                logger.info(f"Метка {mac} зафиксирована в зоне: {gateway_name} (RSSI: {rssi})")
                update_tag_location(mac, gateway_name, rssi)

    except Exception as e:
        logger.error(f"Критическая ошибка при обработке сообщения: {e}")


def run_mqtt():
    logger.info("Запуск MQTT обработчика ZoneHub...")

    client = Client(CallbackAPIVersion.VERSION2)
    client.username_pw_set(settings.MQTT_USER, settings.MQTT_PASS)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(settings.MQTT_HOST, settings.MQTT_PORT, 60)
        client.loop_forever()
    except Exception as e:
        logger.error(f"Не удалось запустить MQTT клиент: {e}")


if __name__ == "__main__":
    run_mqtt()