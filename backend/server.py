import paho.mqtt.client as mqtt
import json

MQTT_BROKER = "test.mosquitto.org"
TOPIC_TELEMETRY = "energysaver/telemetry"
TOPIC_COMMAND = "energysaver/command"

is_overloaded = False

def on_connect(client, userdata, flags, rc):
    print("Сервер успішно підключено до MQTT Брокера!")
    client.subscribe(TOPIC_TELEMETRY)
    print(f"Очікуємо дані від ESP32 на топіку: {TOPIC_TELEMETRY}...\n")

def on_message(client, userdata, msg):
    global is_overloaded 
    payload = msg.payload.decode("utf-8")
    
    try:
        data = json.loads(payload)
        power = data.get("power", 0)
        temp = data.get("temp", 0)
        
        print(f"Отримано: Потужність = {power:.2f} кВт | Температура = {temp:.1f} °C")
        
        if power >= 5.0 or temp >= 60.0:
            if not is_overloaded:
                print("УВАГА! КРИТИЧНЕ ПЕРЕВАНТАЖЕННЯ!")
                print("Відправка команди 'RELAY_OFF' на ESP32...\n")
                client.publish(TOPIC_COMMAND, "RELAY_OFF")
                is_overloaded = True
                
        else:
            if is_overloaded:
                print("Показники в нормі. Відновлюємо живлення.")
                print("Відправка команди 'RELAY_ON' на ESP32...\n")
                client.publish(TOPIC_COMMAND, "RELAY_ON")
                is_overloaded = False
                
    except json.JSONDecodeError:
        print("Помилка декодування JSON")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print("Ініціалізація сервера...")
client.connect(MQTT_BROKER, 1883, 60)
client.loop_forever()