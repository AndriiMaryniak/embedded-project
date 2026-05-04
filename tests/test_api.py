import pytest
import requests
import json
import paho.mqtt.client as mqtt
import time

BASE_URL = "http://127.0.0.1:5000"
MQTT_BROKER = "broker.hivemq.com"
TOPIC_TELEMETRY = "energysaver/telemetry"

# 1. Тест API оновлення ліміту
def test_update_threshold_api():
    """Перевіряє, чи працює REST API оновлення лімітів."""
    # Спочатку встановлюємо тестове значення
    test_limit = 4.8
    response = requests.post(f"{BASE_URL}/api/threshold", json={"threshold": test_limit})
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Перевіряємо, чи воно дійсно оновилося (ми додали GET метод для цього)
    get_response = requests.get(f"{BASE_URL}/api/threshold")
    assert get_response.status_code == 200
    assert get_response.json()["threshold"] == test_limit

# 2. Тест експорту CSV
def test_csv_export():
    """Перевіряє, чи сервер віддає CSV файл."""
    response = requests.get(f"{BASE_URL}/api/export")
    assert response.status_code == 200
    assert "text/csv" in response.headers["Content-Type"]
    assert "ID,Час,Сира Потужність" in response.text # Перевіряємо заголовки

# 3. Тест MQTT підключення
def test_mqtt_telemetry_publish():
    """Перевіряє, чи брокер приймає наші повідомлення."""
    client = mqtt.Client()
    client.connect(MQTT_BROKER, 1883, 60)
    
    test_payload = json.dumps({"power": 2.5, "temp": 25.0})
    result = client.publish(TOPIC_TELEMETRY, test_payload)
    
    # wait_for_publish гарантує, що повідомлення дійсно пішло
    result.wait_for_publish(timeout=2)
    assert result.is_published() == True