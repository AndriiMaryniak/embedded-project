import paho.mqtt.client as mqtt
import json
import csv
from io import StringIO
from flask import Flask, Response, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
import sqlite3

from database import init_db, get_threshold, save_data, DB_NAME

MQTT_BROKER = "broker.hivemq.com"
TOPIC_TELEMETRY = "energysaver/telemetry"
TOPIC_COMMAND = "energysaver/command"

app = Flask(__name__)
CORS(app) # Дозволяємо фронтенду звертатися до API
socketio = SocketIO(app, cors_allowed_origins="*")

is_overloaded = False
current_status = 'НОРМА'

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

        socketio.emit('update', {'power': filtered_power, 'temperature': temp, 'status': new_status, 'threshold': threshold})
        
        if new_status != current_status:
            if new_status == 'КРИТИЧНО':
                client.publish(TOPIC_COMMAND, "RELAY_OFF")
                is_overloaded = True
                save_data('alerts', message=f"Аварія! P={filtered_power}кВт, T={temp}C")
            
            elif new_status == 'ПОПЕРЕДЖЕННЯ':
                save_data('alerts', message=f"Попередження: Високе навантаження! P={filtered_power}кВт")
                
            elif new_status == 'НОРМА':
                if current_status == 'КРИТИЧНО':
                    client.publish(TOPIC_COMMAND, "RELAY_ON")
                    save_data('alerts', message="Система стабілізувалась. Реле увімкнено.")
                    is_overloaded = False
            
            current_status = new_status
            
    except Exception as e:
        print(f"Помилка обробки MQTT: {e}")

# API для оновлення ліміту
@app.route('/api/threshold', methods=['GET', 'POST'])
def handle_threshold():
    if request.method == 'POST':
        new_limit = request.json.get('threshold')
        if new_limit is not None:
            with sqlite3.connect(DB_NAME) as conn:
                conn.execute("UPDATE settings SET value = ? WHERE key = 'power_threshold'", (new_limit,))
                conn.commit()
            return jsonify({"status": "success", "new_limit": new_limit})
        return jsonify({"status": "error"}), 400
    
    # GET метод для тестів
    return jsonify({"threshold": get_threshold()})

# API для експорту
@app.route('/api/export')
def export_csv():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, timestamp, raw_power, filtered_power, temperature FROM telemetry ORDER BY id DESC")
        rows = cursor.fetchall()

    def generate():
        data = StringIO()
        writer = csv.writer(data)
        writer.writerow(('ID', 'Час', 'Сира Потужність', 'Фільтрована', 'Температура'))
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