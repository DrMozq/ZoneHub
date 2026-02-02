import sqlite3
from settings import settings, logger


def init_db():
    """Создает таблицу для меток, если её еще нет"""
    with sqlite3.connect(settings.DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                mac TEXT PRIMARY KEY,
                last_zone TEXT,
                rssi INTEGER,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    logger.info("База данных инициализирована")


def update_tag_location(mac, zone, rssi):
    """Обновляет местоположение метки в базе данных"""
    try:
        with sqlite3.connect(settings.DB_PATH) as conn:
            cursor = conn.cursor()
            # SQL запрос: Вставить или заменить (если mac уже есть)
            cursor.execute("""
                INSERT INTO tags (mac, last_zone, rssi, last_seen)
                VALUES (?, ?, ?, datetime('now', 'localtime'))
                ON CONFLICT(mac) DO UPDATE SET
                    last_zone = excluded.last_zone,
                    rssi = excluded.rssi,
                    last_seen = excluded.last_seen
            """, (mac, zone, rssi))
            conn.commit()
    except Exception as e:
        logger.error(f"Ошибка записи в БД: {e}")

# При импорте файла сразу проверяем/создаем базу
init_db()