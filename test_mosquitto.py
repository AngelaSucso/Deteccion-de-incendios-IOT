# Test: Escuchar mensajes directos de Mosquitto
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print(f"✅ Conectado a Mosquitto (código: {rc})")
    client.subscribe("incendio/sensores")
    print("👂 Escuchando topic: incendio/sensores")
    print("⏳ Esperando mensajes del Arduino...\n")

def on_message(client, userdata, msg):
    print(f"📥 MENSAJE RECIBIDO:")
    print(f"   Topic: {msg.topic}")
    print(f"   Payload: {msg.payload.decode()}")
    print("-" * 50)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print("🔧 Conectando a test.mosquitto.org...")
client.connect("test.mosquitto.org", 1883, 60)

client.loop_forever()
