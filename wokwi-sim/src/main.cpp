#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <DHTesp.h>
#include <esp_wifi.h> // Потрібно для керування енергозбереженням
#include "secrets.h"

#define POT_PIN 34
#define DHT_PIN 15
#define RELAY_PIN 18
#define LED_GREEN 4
#define LED_RED 2
#define BUZZER_PIN 5

WiFiClient espClient;
PubSubClient client(espClient);
LiquidCrystal_I2C lcd(0x27, 16, 2);
DHTesp dht;

unsigned long lastMsg = 0;
const unsigned long TELEMETRY_INTERVAL = 2000; 

void setup_wifi() {
  lcd.setCursor(0, 0);
  lcd.print("Connecting WiFi.");
  WiFi.begin(WIFI_SSID, WIFI_PASS, 6); // Канал 6 для Wokwi
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  // ОПТИМІЗАЦІЯ 1: Вмикаємо максимальне енергозбереження радіомодуля (Modem Sleep).
  // Це значно зменшує споживання струму (від ~100mA до ~20mA), 
  // але залишає можливість приймати MQTT команди.
  esp_wifi_set_ps(WIFI_PS_MAX_MODEM);
  
  Serial.println("\nWiFi Connected!");
  lcd.clear();
  lcd.print("WiFi Connected!");
  delay(1000);
}

void callback(char* topic, byte* payload, unsigned int length) {
  // ОПТИМІЗАЦІЯ 2: Використовуємо статичний буфер замість класу String 
  // для обробки вхідного повідомлення, щоб уникнути фрагментації купи (Heap).
  char msgBuffer[32];
  unsigned int msgLen = length < sizeof(msgBuffer) - 1 ? length : sizeof(msgBuffer) - 1;
  memcpy(msgBuffer, payload, msgLen);
  msgBuffer[msgLen] = '\0'; // Додаємо нуль-термінатор
  
  Serial.printf("Отримано команду з сервера: %s\n", msgBuffer);

  if (strcmp(msgBuffer, "RELAY_OFF") == 0) {
    digitalWrite(RELAY_PIN, LOW);
    digitalWrite(LED_GREEN, LOW);
    digitalWrite(LED_RED, HIGH);
    tone(BUZZER_PIN, 1000);
    lcd.setCursor(0, 1);
    lcd.print("SERVER: OFF_CMD ");
  } 
  else if (strcmp(msgBuffer, "RELAY_ON") == 0) {
    digitalWrite(RELAY_PIN, HIGH); 
    digitalWrite(LED_GREEN, HIGH);
    digitalWrite(LED_RED, LOW);
    noTone(BUZZER_PIN);
    lcd.setCursor(0, 1);
    lcd.print("SERVER: NORMAL  ");
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Підключення до MQTT...");
    if (client.connect("ESP32_EnergySaver_Client")) {
      Serial.println("Успішно!");
      client.subscribe("energysaver/command");
    } else {
      Serial.print("Помилка, rc=");
      Serial.print(client.state());
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  dht.setup(DHT_PIN, DHTesp::DHT22);
  lcd.init();
  lcd.backlight();

  digitalWrite(RELAY_PIN, HIGH); 
  digitalWrite(LED_GREEN, HIGH);

  setup_wifi();
  client.setServer(MQTT_SERVER, MQTT_PORT);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long now = millis();
  if (now - lastMsg >= TELEMETRY_INTERVAL) { 
    lastMsg = now;

    int potValue = analogRead(POT_PIN);
    float power_kW = (potValue / 4095.0) * 6.0;
    float temp_C = dht.getTemperature();
    if (isnan(temp_C)) temp_C = 25.0;

    lcd.setCursor(0, 0);
    // Використовуємо printf для LCD
    lcd.printf("P:%.1fkW T:%.1fC  ", power_kW, temp_C);

    // ОПТИМІЗАЦІЯ 3: Формуємо JSON за допомогою snprintf замість конкатенації String.
    // Це працює швидше і не створює "сміття" в оперативній пам'яті.
    char payload[64];
    snprintf(payload, sizeof(payload), "{\"power\": %.2f, \"temp\": %.1f}", power_kW, temp_C);
    
    Serial.printf("Відправка телеметрії: %s\n", payload);
    client.publish("energysaver/telemetry", payload);
  }
}