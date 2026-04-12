import paho.mqtt.client as mqtt
import json
import sqlite3
import csv
from io import StringIO
from flask import Flask, render_template, Response, request, jsonify
from flask_socketio import SocketIO

MQTT_BROKER = "test.mosquitto.org"
TOPIC_TELEMETRY = "energysaver/telemetry"
TOPIC_COMMAND = "energysaver/command"
DB_NAME = "energy_data.db"

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Глобальні змінні стану (State Machine)
is_overloaded = False
current_status = 'НОРМА'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Використовуємо DATETIME('now', 'localtime') для правильного місцевого часу
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT (DATETIME('now', 'localtime')),
            raw_power REAL, filtered_power REAL, temperature REAL
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value REAL
        );
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT (DATETIME('now', 'localtime')), message TEXT
        );
        INSERT OR IGNORE INTO settings (key, value) VALUES ('power_threshold', 5.0);
    ''')
    conn.commit()
    conn.close()

def get_threshold():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key='power_threshold'")
    val = cursor.fetchone()[0]
    conn.close()
    return val

def save_data(table, **kwargs):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    columns = ', '.join(kwargs.keys())
    placeholders = ', '.join('?' * len(kwargs))
    cursor.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", tuple(kwargs.values()))
    conn.commit()
    conn.close()

class KalmanFilter1D:
    def __init__(self, process_noise=0.05, measurement_noise=0.3):
        self.q = process_noise 
        self.r = measurement_noise 
        self.x = 0.0 
        self.p = 1.0 

    def update(self, measurement):
        p_predict = self.p + self.q
        k = p_predict / (p_predict + self.r) 
        self.x = self.x + k * (measurement - self.x)
        self.p = (1 - k) * p_predict
        return round(self.x, 2)

power_filter = KalmanFilter1D()

def on_connect(client, userdata, flags, rc):
    print("Підключено до MQTT!")
    client.subscribe(TOPIC_TELEMETRY)

def on_message(client, userdata, msg):
    global is_overloaded, current_status
    try:
        data = json.loads(msg.payload.decode('utf-8'))
        raw_power, temp = data.get("power", 0.0), data.get("temp", 0.0)
        filtered_power = power_filter.update(raw_power)
        
        save_data('telemetry', raw_power=raw_power, filtered_power=filtered_power, temperature=temp)
        threshold = get_threshold()
        
        new_status = 'НОРМА'

        # Логіка визначення нового статусу
        if is_overloaded:
            if filtered_power < (threshold * 0.7) and temp < 50.0:
                new_status = 'НОРМА'
            else:
                new_status = 'КРИТИЧНО'
        else:
            if filtered_power >= threshold or temp >= 60.0:
                new_status = 'КРИТИЧНО'
            elif filtered_power >= (threshold * 0.85):
                new_status = 'ПОПЕРЕДЖЕННЯ'

        # Відправка на фронтенд
        socketio.emit('update', {'power': filtered_power, 'temperature': temp, 'status': new_status, 'threshold': threshold})
        
        # ЛОГІКА ЗАПИСУ В БАЗУ ДАНИХ ТА КЕРУВАННЯ РЕЛЕ
        if new_status != current_status:
            # Якщо статус змінився на КРИТИЧНО
            if new_status == 'КРИТИЧНО':
                client.publish(TOPIC_COMMAND, "RELAY_OFF")
                is_overloaded = True
                # Визначаємо точну причину для логів
                reason = "ПЕРЕГРІВ" if temp >= 60.0 else "ПЕРЕВАНТАЖЕННЯ МЕРЕЖІ"
                save_data('alerts', message=f"🚨 Аварія ({reason})! P={filtered_power}кВт, T={temp}C")
            
            # Якщо статус змінився на ПОПЕРЕДЖЕННЯ
            elif new_status == 'ПОПЕРЕДЖЕННЯ':
                save_data('alerts', message=f"⚠️ Попередження: Високе навантаження! P={filtered_power}кВт")
                
            # Якщо статус повернувся до НОРМИ
            elif new_status == 'НОРМА':
                if current_status == 'КРИТИЧНО':
                    client.publish(TOPIC_COMMAND, "RELAY_ON")
                    save_data('alerts', message="✅ Система стабілізувалась (Охолодження/Норма). Реле увімкнено.")
                    is_overloaded = False
                elif current_status == 'ПОПЕРЕДЖЕННЯ':
                    save_data('alerts', message="✅ Навантаження повернулося до норми.")
            
            # Оновлюємо поточний стан системи
            current_status = new_status
            
    except Exception as e:
        print(f"Помилка обробки MQTT: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/threshold', methods=['POST'])
def update_threshold():
    new_limit = request.json.get('threshold')
    if new_limit:
        conn = sqlite3.connect(DB_NAME)
        conn.execute("UPDATE settings SET value = ? WHERE key = 'power_threshold'", (new_limit,))
        conn.commit()
        conn.close()
        save_data('alerts', message=f"⚙️ Ліміт змінено користувачем на {new_limit} кВт")
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

@app.route('/api/export')
def export_csv():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp, raw_power, filtered_power, temperature FROM telemetry ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    def generate():
        data = StringIO()
        writer = csv.writer(data)
        writer.writerow(('ID', 'Час', 'Сира Потужність (кВт)', 'Фільтрована (кВт)', 'Температура (C)'))
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)
        for row in rows:
            writer.writerow(row)
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

    response = Response(generate(), mimetype='text/csv')
    response.headers.set("Content-Disposition", "attachment", filename="energy_telemetry.csv")
    return response

if __name__ == "__main__":
    init_db()
    client = mqtt.Client()
    client.on_connect, client.on_message = on_connect, on_message
    client.connect(MQTT_BROKER, 1883, 60)
    client.loop_start()
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)