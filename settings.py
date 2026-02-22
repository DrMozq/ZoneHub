import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

# Определяем базовую директорию проекта
BASE_DIR = Path(__file__).resolve().parent

# Загружаем переменные из .env
load_dotenv(BASE_DIR / ".env")

class Settings:
    # Настройки MQTT
    MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
    MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
    MQTT_USER = os.getenv("MQTT_USER", "admin")
    MQTT_PASS = os.getenv("MQTT_PASS", "")

    # Пути
    DATA_DIR = BASE_DIR / "data"
    DB_PATH = DATA_DIR / "zonehub.db"
    LOG_PATH = DATA_DIR / "app_{time:YYYY-MM-DD}.log"

    # Координаты шлюзов (X, Y) в метрах
    GATEWAY_COORDS = {
        "esp32_x0y0": (0.0, 0.0),  # Шлюз 1 в углу
        "esp32_x3y0": (3.0, 0.0),  # Шлюз 2 через 3 метра по X
        "esp32_x0y3": (0.0, 3.0),  # Шлюз 3 через 3 метра по Y
    }
    # Индивидуальная калибровка (RSSI на 1 метре)
    GATEWAY_CALIBRATION = {
        "esp32_x0y0": -57.0,
        "esp32_x3y0": -67.0,
        "esp32_x0y3": -67.0
    }
    N_ENVIRONMENT = 5.2  # Коэффициент затухания (2.0 - открытое пространство)

# Создаем папку для данных, если её нет
Settings.DATA_DIR.mkdir(exist_ok=True)

# Настройка Loguru# Create a new file at midnight
logger.remove()  # Удаляем стандартный обработчик

# Add console handler (colored output)
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: ^7}</level> | <cyan>{message}</cyan>",
    level="INFO"
)

# Add file handler (history and debugging)
logger.add(
    Settings.LOG_PATH,
    rotation="00:00",      # Create a new file at midnight
    retention="10 days",   # Keep logs for the last 10 days
    compression="zip",     # Compress old log files
    level="DEBUG",         # Record all technical details in the file
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: ^7} | {file}:{line} | {message}"
)

settings = Settings()