import paho.mqtt.client as mqtt
import json
import time

MQTT_BROKER = "broker.hivemq.com"
TOPIC_TELEMETRY = "maryniak/fei34/telemetry"
TOPIC_COMMAND = "maryniak/fei34/command"

received_command = None
start_time = 0
latency_ms = 0

def on_connect(client, userdata, flags, rc):
    client.subscribe(TOPIC_COMMAND)

def on_message(client, userdata, msg):
    global received_command, latency_ms
    received_command = msg.payload.decode('utf-8')
    latency_ms = (time.time() - start_time) * 1000
    print(f"\n📩 Отримано команду від сервера: {received_command} за {latency_ms:.2f} мс")

def test_hardware_reaction_to_critical_temp():
    global start_time, received_command
    
    # Використовуємо VERSION1, щоб прибрати жовте попередження
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, 1883, 60)
    client.loop_start()
    
    time.sleep(1)
    
    # 1. СПОЧАТКУ ВІДПРАВЛЯЄМО НОРМУ (щоб скинути захисний гістерезис сервера)
    normal_payload = json.dumps({"power": 1.0, "temp": 25.0})
    print(f"\n🟢 Відправляємо НОРМУ для скидання стану: {normal_payload}")
    client.publish(TOPIC_TELEMETRY, normal_payload)
    time.sleep(1) # Даємо серверу секунду на обробку
    
    # Скидаємо змінну перед головним тестом
    received_command = None 
    
    # 2. ТЕПЕР ВІДПРАВЛЯЄМО АВАРІЮ
    critical_payload = json.dumps({"power": 2.0, "temp": 80.0})
    print(f"🔴 Відправляємо АВАРІЮ (Перегрів): {critical_payload}")
    
    start_time = time.time()
    client.publish(TOPIC_TELEMETRY, critical_payload)
    
    timeout = 3.0
    while received_command is None and (time.time() - start_time) < timeout:
        time.sleep(0.01)
        
    client.loop_stop()
    
    # Перевірки
    assert received_command is not None, "Сервер не відповів на аварію! Перевір, чи запущений server.py і чи збігаються топіки."
    assert received_command == "RELAY_OFF", f"Очікувалась команда RELAY_OFF, а прийшла {received_command}"
    assert latency_ms < 200.0, f"Затримка занадто велика: {latency_ms:.2f} мс!"
    
    print(f"\n✅ ТЕСТ УСПІШНИЙ! Затримка: {latency_ms:.2f} мс")