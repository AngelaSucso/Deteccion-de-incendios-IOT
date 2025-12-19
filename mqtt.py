# mqtt_bridge.py
# Puente entre Mosquitto y AWS IoT Core

from awsiot import mqtt_connection_builder
from awscrt import mqtt as aws_mqtt
import paho.mqtt.client as paho_mqtt
import json
import time

# ════════════════════════════════════════════
# CONFIGURACIÓN AWS
# ════════════════════════════════════════════
ENDPOINT = "a1b9nxragudit3-ats.iot.us-east-1.amazonaws.com"
CLIENT_ID = "sdk-java"  # ← CAMBIADO: antes era "mqtt-bridge"
PATH_TO_CERTIFICATE = "./arduino-incendio.cert.pem"
PATH_TO_PRIVATE_KEY = "./arduino-incendio.private.key"
PATH_TO_AMAZON_ROOT_CA_1 = "./root-CA.crt"
AWS_TOPIC = "sdk/test/python"

# ════════════════════════════════════════════
# CONFIGURACIÓN MOSQUITTO
# ════════════════════════════════════════════
MOSQUITTO_BROKER = "test.mosquitto.org"
MOSQUITTO_TOPIC = "incendio/sensores"

# ════════════════════════════════════════════
# CONEXIÓN AWS IoT
# ════════════════════════════════════════════
print("🔧 Conectando a AWS IoT Core...")
aws_connection = mqtt_connection_builder.mtls_from_path(
    endpoint=ENDPOINT,
    cert_filepath=PATH_TO_CERTIFICATE,
    pri_key_filepath=PATH_TO_PRIVATE_KEY,
    ca_filepath=PATH_TO_AMAZON_ROOT_CA_1,
    client_id=CLIENT_ID,
    clean_session=False,
    keep_alive_secs=30
)

connect_future = aws_connection.connect()
connect_future.result()
print("✅ AWS IoT conectado\n")

# ════════════════════════════════════════════
# CALLBACK: Cuando llegan datos de Arduino
# ════════════════════════════════════════════
def on_mosquitto_message(client, userdata, msg):
    """
    Recibe mensaje de Mosquitto (Arduino)
    y lo reenvía a AWS IoT Core
    """
    from datetime import datetime
    payload = msg.payload.decode('utf-8')
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] 📥 Arduino → Mosquitto: {payload}")
    
    # Reenviar a AWS IoT
    aws_connection.publish(
        topic=AWS_TOPIC,
        payload=payload,
        qos=aws_mqtt.QoS.AT_LEAST_ONCE
    )
    
    print(f"[{timestamp}] 📤 Bridge → AWS IoT: OK\n")

# ════════════════════════════════════════════
# CONEXIÓN MOSQUITTO
# ════════════════════════════════════════════
def on_mosquitto_connect(client, userdata, flags, rc):
    """Callback cuando se conecta a Mosquitto"""
    if rc == 0:
        print(f"✅ Mosquitto conectado (código: {rc})")
        client.subscribe(MOSQUITTO_TOPIC)
        print(f"👂 Suscrito al topic: {MOSQUITTO_TOPIC}")
        print("⏳ Esperando mensajes del Arduino...\n")
    else:
        print(f"❌ Error conectando a Mosquitto (código: {rc})")

print("🔧 Conectando a Mosquitto...")
mosquitto_client = paho_mqtt.Client()
mosquitto_client.on_connect = on_mosquitto_connect
mosquitto_client.on_message = on_mosquitto_message

mosquitto_client.connect(MOSQUITTO_BROKER, 1883)
print("✅ Conexión iniciada\n")

# ════════════════════════════════════════════
# MANTENER BRIDGE ACTIVO
# ════════════════════════════════════════════
print("🌉 MQTT BRIDGE ACTIVO")
print("   Arduino → Mosquitto → AWS IoT → main.py")
print("   Presiona Ctrl+C para detener\n")

try:
    mosquitto_client.loop_forever()
except KeyboardInterrupt:
    print("\n⛔ Deteniendo bridge...")
    mosquitto_client.disconnect()
    aws_connection.disconnect()
    print("✅ Desconectado")