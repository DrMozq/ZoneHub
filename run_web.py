from flask import Flask, render_template
import sqlite3
import math
from datetime import datetime
from settings import settings, logger

app = Flask(__name__)


def rssi_to_meters(rssi, gateway_name):
    """Индивидуальный расчет расстояния для каждого шлюза"""
    # Берем А из калибровки или -65 по умолчанию
    a = settings.GATEWAY_CALIBRATION.get(gateway_name, -65.0)

    if rssi == 0: return 10.0

    # Формула с твоим новым коэффициентом N
    dist = 10 ** ((a - rssi) / (10 * settings.N_ENVIRONMENT))
    return round(dist, 2)

def trilaterate(distances):
    """
    Трилатерация (расчет X, Y) по методу линеаризации.
    distances: словарь { 'имя_шлюза': расстояние_в_метрах }
    """
    names = list(distances.keys())
    # Нам нужно минимум 3 шлюза, чьи координаты описаны в settings.GATEWAY_COORDS
    active_gateways = [n for n in names if n in settings.GATEWAY_COORDS]

    if len(active_gateways) < 3:
        return None

    try:
        # Берем первые три подходящих шлюза
        g1_name, g2_name, g3_name = active_gateways[:3]

        # Координаты шлюзов
        x1, y1 = settings.GATEWAY_COORDS[g1_name]
        x2, y2 = settings.GATEWAY_COORDS[g2_name]
        x3, y3 = settings.GATEWAY_COORDS[g3_name]

        # Расстояния
        d1 = distances[g1_name]
        d2 = distances[g2_name]
        d3 = distances[g3_name]

        # Система линейных уравнений Ax + By = C и Dx + Ey = F
        A = 2 * x2 - 2 * x1
        B = 2 * y2 - 2 * y1
        C = d1 ** 2 - d2 ** 2 - x1 ** 2 + x2 ** 2 - y1 ** 2 + y2 ** 2

        D = 2 * x3 - 2 * x2
        E = 2 * y3 - 2 * y2
        F = d2 ** 2 - d3 ** 2 - x2 ** 2 + x3 ** 2 - y2 ** 2 + y3 ** 2

        # Решение методом Крамера
        denominator = (A * E - D * B)
        if abs(denominator) < 0.0001:
            return None  # Шлюзы стоят на одной линии

        x = (C * E - F * B) / denominator
        y = (A * F - D * C) / denominator

        return round(x, 2), round(y, 2)

    except Exception as e:
        logger.error(f"Ошибка в трилатерации: {e}")
        return None


def get_tags_positioning():
    """
    Основная функция: собирает усредненные данные из БД за последние 15 секунд
    и рассчитывает координаты X, Y для каждой метки.
    """
    tags_output = []
    try:
        with sqlite3.connect(settings.DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 1. Получаем список вообще всех уникальных MAC-адресов, которые когда-либо были в базе
            cursor.execute("SELECT DISTINCT mac FROM measurements")
            macs = [row['mac'] for row in cursor.fetchall()]

            for mac in macs:
                # 2. Для каждой метки берем УСРЕДНЕННЫЙ RSSI по каждому шлюзу
                # Это фильтрует случайные скачки сигнала
                cursor.execute("""
                    SELECT gateway, AVG(rssi) as avg_rssi, MAX(last_seen) as ls
                    FROM measurements 
                    WHERE mac = ? AND last_seen > datetime('now', 'localtime', '-15 seconds')
                    GROUP BY gateway
                """, (mac,))
                rows = cursor.fetchall()

                distances = {}
                latest_time = None

                # Если за последние 15 секунд есть хоть какие-то данные
                if rows:
                    for r in rows:
                        # Считаем расстояние по усредненному значению
                        distances[r['gateway']] = rssi_to_meters(r['avg_rssi'], r['gateway'])

                        # Определяем время самого последнего пакета для этой метки
                        if latest_time is None or r['ls'] > latest_time:
                            latest_time = r['ls']

                    # 3. Пытаемся рассчитать координаты (нужно минимум 3 шлюза)
                    coords = trilaterate(distances)

                    status_coords = f"X: {coords[0]}м, Y: {coords[1]}м" if coords else "Калибровка (нужно 3 шлюза)"
                    active_gateways = len(distances)

                else:
                    # Если данных за 15 сек нет, метка считается Offline
                    # Берем самое последнее время появления этой метки из истории
                    cursor.execute("SELECT MAX(last_seen) as ls FROM measurements WHERE mac = ?", (mac,))
                    res = cursor.fetchone()
                    latest_time = res['ls'] if res['ls'] else datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    status_coords = "Offline"
                    active_gateways = 0

                # 4. Формируем итоговый объект для отображения в шаблоне index.html
                tags_output.append({
                    'mac': mac,
                    'gateways_count': active_gateways,
                    'coords': status_coords,
                    'last_seen': latest_time,
                    # dt_object нужен для сравнения времени в HTML (статус Online/Offline)
                    'dt_object': datetime.strptime(latest_time, '%Y-%m-%d %H:%M:%S')
                })

        return tags_output

    except Exception as e:
        logger.error(f"Ошибка в функции позиционирования: {e}")
        return []


@app.route('/')
def index():
    # Получаем данные
    tags = get_tags_positioning()
    # Текущее время для расчета статуса Online/Offline в шаблоне
    now = datetime.now()
    return render_template('index.html', tags=tags, now=now)


if __name__ == '__main__':
    logger.info("Запуск Веб-интерфейса трилатерации ZoneHub...")
    app.run(host='0.0.0.0', port=5000, debug=True)