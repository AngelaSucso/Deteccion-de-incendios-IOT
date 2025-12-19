import json
import time
import requests
import paho.mqtt.client as mqtt

from DeteccionAudio.detector_audio_incendio import detectar_incendio
from DeteccionImagen.detector import detect_fire
from telegram_message import enviar_alerta_telegram
# ================== CONFIGURACIÓN ==================
BROKER = "test.mosquitto.org"
TOPIC = "incendio/sensores"

CAMERA_URL = "http://10.7.135.219:8080"
PHOTO_PATH = "foto_incendio.jpg"
AUDIO_PATH = "audio_incendio.wav"

# Umbrales
TEMP_UMBRAL = 45
LUZ_UMBRAL = 2000
HUMEDAD_MIN = 20

# Persistencia
LECTURAS_RIESGO = 5
LECTURAS_RECUPERACION = 5

# ================== ESTADO LOCAL ==================
estado_local = "Normal"
contador_riesgo = 0
contador_normal = 0
evidencia_tomada = False

#=================== UMBRAL DE DESICION==============
PESO_IMAGEN = 0.7
PESO_AUDIO = 0.3
UMBRAL_ALERTA = 0.6
alerta_enviada = False

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
        print("Error grabando audio:", e)


def decidir_alerta(prob_imagen, prob_audio):
    score = (
        PESO_IMAGEN * prob_imagen +
        PESO_AUDIO * prob_audio
    )
    return score >= UMBRAL_ALERTA, score


def detectar_incendio_imagen(image_path):
    result = detect_fire(image_path)

    if result is False:
        return {"confianza": 0.0}
    else:
        detected, image_path, confidence = result
        return {"confianza": confidence}

# ================== MQTT ==================

def on_message(client, userdata, msg):
    global estado_local
    global contador_riesgo, contador_normal
    global evidencia_tomada

    data = json.loads(msg.payload.decode())

    temp = data["temp"]
    hum  = data["hum"]
    luz  = data["luz"]

    print(f"Temp={temp}°C | Hum={hum}% | Luz={luz}")

    condicion_riesgo = (temp > TEMP_UMBRAL) or (luz > LUZ_UMBRAL)

    # ================== ESTADO NORMAL ==================
    if estado_local == "Normal":

        if condicion_riesgo:
            contador_riesgo += 1
            print(f"Lecturas en riesgo: {contador_riesgo}/{LECTURAS_RIESGO}")

            if contador_riesgo >= LECTURAS_RIESGO:
                estado_local = "Riesgo"
                evidencia_tomada = False
                contador_normal = 0
                print("Estado: Capturando evidencias..")

        else:
            contador_riesgo = 0

    # ================== ESTADO RIESGO ==================
    elif estado_local == "Riesgo":

        # Tomar evidencia SOLO UNA VEZ
        if not evidencia_tomada:
            if hum < HUMEDAD_MIN:
                print("Humedad baja: condición favorable al fuego")

            tomar_foto()
            grabar_audio(5)
            evidencia_tomada = True

            # ===== DETECCIÓN POR AUDIO =====
            resultado_audio = detectar_incendio(AUDIO_PATH)
            prob_audio = resultado_audio["confianza"]

            # ===== DETECCIÓN POR IMAGEN =====
            resultado_imagen = detectar_incendio_imagen(PHOTO_PATH)
            prob_imagen = resultado_imagen["confianza"]

            # ===== FUSIÓN =====
            alerta_final, score = decidir_alerta(prob_imagen, prob_audio)
            print(f"Score final: {score:.2f}")

            if alerta_final:
                estado_local = "Confirmado"
                alerta_enviada = False 
                print("INCENDIO CONFIRMADO")
            else:
                print("Evidencia insuficiente, monitoreando...")

        # Verificar recuperación
        if not condicion_riesgo:
            contador_normal += 1
            print(f"Lecturas normales: {contador_normal}/{LECTURAS_RECUPERACION}")

            if contador_normal >= LECTURAS_RECUPERACION:
                estado_local = "Normal"
                contador_riesgo = 0
                contador_normal = 0
                evidencia_tomada = False
                print("Estado: Entorno estabilizado..")
        else:
            contador_normal = 0
    # ================== ESTADO CONFIRMADO ==================
    elif estado_local == "Confirmado":
        enviar_alerta_telegram(PHOTO_PATH)
        alerta_enviada = True


    print(f"Estado local: {estado_local}")
    print("-" * 40)

# ================== MAIN ==================

client = mqtt.Client()
client.on_message = on_message

client.connect(BROKER, 1883)
client.subscribe(TOPIC)

print("Edge IoT iniciado...")
client.loop_forever()