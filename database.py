import sqlite3
from settings import settings, logger


def init_db():
    """Создает таблицу для хранения истории измерений, если её нет"""
    try:
        with sqlite3.connect(settings.DB_PATH) as conn:
            cursor = conn.cursor()
            # Важно: Убери PRIMARY KEY (mac, gateway), чтобы хранить историю
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mac TEXT,
                    gateway TEXT,
                    rssi INTEGER,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        logger.info("База данных успешно инициализирована (режим истории)")
    except Exception as e:
        logger.error(f"Критическая ошибка инициализации БД: {e}")


def update_measurement(mac, gateway, rssi):
    """Вставляет новую запись в историю и очищает старье"""
    try:
        with sqlite3.connect(settings.DB_PATH) as conn:
            cursor = conn.cursor()

            # 1. Сначала проверим, существует ли таблица (на всякий случай)
            # Если ты только что удалил файл, это создаст таблицу
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='measurements'")
            if not cursor.fetchone():
                init_db()

            # 2. Вставляем новое измерение
            cursor.execute("""
                INSERT INTO measurements (mac, gateway, rssi, last_seen)
                VALUES (?, ?, ?, datetime('now', 'localtime'))
            """, (mac, gateway, rssi))

            # 3. Удаляем данные старее 1 минуты (чтобы база не тормозила)
            cursor.execute("DELETE FROM measurements WHERE last_seen < datetime('now', 'localtime', '-1 minute')")

            conn.commit()
    except Exception as e:
        logger.error(f"Ошибка записи в БД: {e}")


# Принудительный запуск при старте скрипта
init_db()