#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <DHTesp.h>

#define POT_PIN 34
#define DHT_PIN 15
#define RELAY_PIN 18
#define LED_GREEN 4
#define LED_RED 2
#define BUZZER_PIN 5

const char* ssid = "Wokwi-GUEST"; 
const char* password = "";
const char* mqtt_server = "test.mosquitto.org";

WiFiClient espClient;
PubSubClient client(espClient);

LiquidCrystal_I2C lcd(0x27, 16, 2);
DHTesp dht;

unsigned long lastMsg = 0;

void setup_wifi() {
  lcd.setCursor(0, 0);
  lcd.print("Connecting WiFi.");
  WiFi.begin(ssid, password, 6);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected!");
  lcd.clear();
  lcd.print("WiFi Connected!");
  delay(1000);
}

void callback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println("Отримано команду з сервера: " + message);

  if (message == "RELAY_OFF") {
    digitalWrite(RELAY_PIN, LOW);
    digitalWrite(LED_GREEN, LOW);
    digitalWrite(LED_RED, HIGH);
    tone(BUZZER_PIN, 1000);
    lcd.setCursor(0, 1);
    lcd.print("SERVER: OFF_CMD ");
  } 
  else if (message == "RELAY_ON") {
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
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long now = millis();
  if (now - lastMsg > 2000) { 
    lastMsg = now;

    int potValue = analogRead(POT_PIN);
    float power_kW = (potValue / 4095.0) * 6.0;
    float temp_C = dht.getTemperature();
    if (isnan(temp_C)) temp_C = 25.0;

    lcd.setCursor(0, 0);
    lcd.print("P:"); lcd.print(power_kW, 1);
    lcd.print("kW T:"); lcd.print(temp_C, 1); lcd.print("C  ");

    String payload = "{\"power\": " + String(power_kW, 2) + ", \"temp\": " + String(temp_C, 1) + "}";
    
    Serial.print("Відправка телеметрії: ");
    Serial.println(payload);
    
    client.publish("energysaver/telemetry", payload.c_str());
  }
}