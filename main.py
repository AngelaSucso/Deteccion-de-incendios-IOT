import json
import time
import requests
import paho.mqtt.client as mqtt

# ================== CONFIGURACIÓN ==================
BROKER = "test.mosquitto.org"
TOPIC = "incendio/sensores"

CAMERA_URL = "http://10.7.135.219:8080"
PHOTO_PATH = "foto_incendio.jpg"
AUDIO_PATH = "audio_incendio.wav"

TEMP_UMBRAL = 45
LUZ_UMBRAL = 2000   # ajustar con pruebas reales
HUMEDAD_MIN = 20 
LECTURAS_CONFIRMACION = 5

contador_luz = 0
alerta_disparada = False

# ================== FUNCIONES ==================

def tomar_foto():
    try:
        img = requests.get(f"{CAMERA_URL}/shot.jpg", timeout=5).content
        with open(PHOTO_PATH, "wb") as f:
            f.write(img)
        print("Foto capturada")
    except Exception as e:
        print("Error tomando foto:", e)

def grabar_audio(duracion=5):
    try:
        response = requests.get(f"{CAMERA_URL}/audio.wav", stream=True, timeout=5)
        with open(AUDIO_PATH, "wb") as f:
            inicio = time.time()
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                if time.time() - inicio > duracion:
                    break
        print("Audio grabado")
    except Exception as e:
        print(" Error grabando audio:", e)

# ================== MQTT ==================

def on_message(client, userdata, msg):
    global contador_luz, alerta_disparada

    data = json.loads(msg.payload.decode())

    temp = data["temp"]
    hum  = data["hum"]
    luz  = data["luz"]

    print(f" {temp}°C |  {hum}% |  Luz={luz}")

    # -------- LÓGICA DE PERSISTENCIA --------
    if (luz > LUZ_UMBRAL) or (temp > TEMP_UMBRAL):
        contador_luz += 1
        print(f"Lecturas altas consecutivas: {contador_luz}")
    else:
        contador_luz = 0
        alerta_disparada = False  # rearmar sistema

    # -------- DISPARO FINAL --------
    if contador_luz >= LECTURAS_CONFIRMACION and not alerta_disparada:
        print("RIESGO DE INCENDIO: Cuidado")

        # Contexto ambiental
        if hum < HUMEDAD_MIN:
            print("Humedad baja: condición favorable al fuego")

        alerta_disparada = True
        contador_luz = 0  # evita múltiples disparos seguidos
        tomar_foto()
        grabar_audio(5)

# ================== MAIN ==================

client = mqtt.Client()
client.on_message = on_message

client.connect(BROKER, 1883)
client.subscribe(TOPIC)

print("Sistema de monitoreo iniciado...")
client.loop_forever()