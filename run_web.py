from flask import Flask, render_template
import sqlite3
from settings import settings, logger
from datetime import datetime

app = Flask(__name__)

def get_tags_from_db():
    try:
        with sqlite3.connect(settings.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tags ORDER BY last_seen DESC")
            rows = cursor.fetchall()

            # Превращаем список из базы в список словарей,
            # чтобы добавить объект datetime для удобного сравнения
            tags = []
            for row in rows:
                tag = {
                    'mac': row['mac'],
                    'last_zone': row['last_zone'],
                    'rssi': row['rssi'],
                    'last_seen': row['last_seen'],
                    'dt_object': datetime.strptime(row['last_seen'], '%Y-%m-%d %H:%M:%S')
                }
                tags.append(tag)
            return tags
    except Exception as e:
        logger.error(f"Ошибка чтения БД: {e}")
        return []

@app.route('/')
def index():
    tags = get_tags_from_db()
    now = datetime.now()
    return render_template('index.html', tags=tags, now=now)

if __name__ == '__main__':
    logger.info("Запуск Веб-интерфейса ZoneHub...")
    # host='0.0.0.0' позволяет заходить на сайт с любого устройства в сети
    app.run(host='0.0.0.0', port=5000, debug=True)