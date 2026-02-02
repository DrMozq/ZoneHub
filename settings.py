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