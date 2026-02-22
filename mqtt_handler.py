import json
import time
from paho.mqtt.client import Client
from paho.mqtt.enums import CallbackAPIVersion
from settings import logger, settings
from database import update_measurement

from run_web import rssi_to_meters


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.success("Успешное подключение к брокеру")
        # Подписываемся на все топики, заканчивающиеся на /ble_tags
        client.subscribe("+/ble_tags")
    else:
        logger.error(f"Ошибка подключения, код: {rc}")

sum_rssi = {}
n_tags = {}


def on_message(client, userdata, msg):
    try:
        gateway_name = msg.topic.split('/')[0]
        payload = json.loads(msg.payload.decode())
        devices = payload.get("devices", [])

        if devices:
            for device in devices:
                mac = device["mac"]
                rssi = device["rssi"]

                # Расстояние для лога (мгновенное)
                m = rssi_to_meters(rssi, gateway_name)

                logger.info(
                    f"Шлюз {gateway_name} | Метка: {mac} | RSSI: {rssi} | Расстояние: {m}м")

                # Записываем в БД (SQLite сохранит время автоматически)
                update_measurement(mac, gateway_name, rssi)
    except Exception as e:
        logger.error(f"Ошибка парсинга MQTT: {e}")


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