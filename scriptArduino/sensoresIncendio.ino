#include <Arduino_MKRIoTCarrier.h>
#include <WiFiNINA.h>
#include <ArduinoMqttClient.h>

MKRIoTCarrier carrier;

// -------- WIFI --------
char ssid[] = "wifi-CsComputacion";
char pass[] = "EPCC2022$";

// -------- MQTT --------
const char broker[] = "test.mosquitto.org";
const char topic[]  = "incendio/sensores";

WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);

// -------- VALORES VALIDOS --------
float temp_valida = 0.0;
float hum_valida  = 0.0;
int   luz_valida  = 0;

void setup() {
  Serial.begin(9600);
  delay(4000);

  carrier.begin();

  // -------- PANTALLA: TEXTO FIJO --------
  carrier.display.fillScreen(ST77XX_BLACK);
  carrier.display.setTextColor(ST77XX_WHITE);
  carrier.display.setTextSize(2);

  carrier.display.setCursor(10, 30);
  carrier.display.print("Temp (C):");

  carrier.display.setCursor(10, 70);
  carrier.display.print("Hum  (%):");

  carrier.display.setCursor(10, 110);
  carrier.display.print("Luz:");

  // -------- WIFI --------
  WiFi.begin(ssid, pass);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }

  // -------- MQTT --------
  mqttClient.connect(broker, 1883);
}

void loop() {
  // -------- LECTURA SENSORES --------
  float temp = carrier.Env.readTemperature();
  float hum  = carrier.Env.readHumidity();

  if (temp != 0) temp_valida = temp;
  if (hum  != 0) hum_valida  = hum;

  int r, g, b, c = 0;
  if (carrier.Light.colorAvailable()) {
    carrier.Light.readColor(r, g, b, c);
    if (c != 0) luz_valida = c;
  }

  // -------- ACTUALIZAR SOLO VALORES --------
  carrier.display.fillRect(160, 30, 70, 25, ST77XX_BLACK);
  carrier.display.fillRect(160, 70, 70, 25, ST77XX_BLACK);
  carrier.display.fillRect(160, 110, 70, 25, ST77XX_BLACK);

  carrier.display.setCursor(160, 30);
  carrier.display.print(temp_valida, 1);

  carrier.display.setCursor(160, 70);
  carrier.display.print(hum_valida, 1);

  carrier.display.setCursor(160, 110);
  carrier.display.print(luz_valida);

  // -------- MQTT --------
  mqttClient.beginMessage(topic);
  mqttClient.print("{");
  mqttClient.print("\"temp\":"); mqttClient.print(temp_valida); mqttClient.print(",");
  mqttClient.print("\"hum\":");  mqttClient.print(hum_valida);  mqttClient.print(",");
  mqttClient.print("\"luz\":");  mqttClient.print(luz_valida);
  mqttClient.print("}");
  mqttClient.endMessage();

  delay(1000);
}