#include <Arduino_MKRIoTCarrier.h>
#include <WiFiNINA.h>
#include <ArduinoMqttClient.h>

MKRIoTCarrier carrier;

// -------- CONFIG WIFI --------
char ssid[] = "wifi-CsComputacion";
char pass[] = "EPCC2022$";

// -------- MQTT --------
const char broker[] = "test.mosquitto.org";
const char topic[]  = "incendio/sensores";

WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);

void setup() {
  Serial.begin(9600);
  delay(2000);  // solo para debug por USB

  carrier.begin();

  // Conectar WiFi
  WiFi.begin(ssid, pass);
  unsigned long t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < 15000) {
    delay(500);
  }

  // Conectar MQTT
  mqttClient.connect(broker, 1883);
}

void loop() {
  float temp = carrier.Env.readTemperature();
  float hum  = carrier.Env.readHumidity();

  // intensidad luminosa real
  int r, g, b, c;

  if (carrier.Light.colorAvailable()) {
    carrier.Light.readColor(r, g, b, c);

  // -------- PUBLICAR MQTT --------
    mqttClient.beginMessage(topic);
    mqttClient.print("{");
    mqttClient.print("\"temp\":"); mqttClient.print(temp); mqttClient.print(",");
    mqttClient.print("\"hum\":");  mqttClient.print(hum);  mqttClient.print(",");
    mqttClient.print("\"luz\":");  mqttClient.print(c);
    mqttClient.print("}");
    mqttClient.endMessage();
  }

  delay(1000);
}