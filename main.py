import json
import time
import requests
import paho.mqtt.client as mqtt
import base64
import mimetypes

from DeteccionAudio.detector_audio_incendio import detectar_incendio
from DeteccionImagen.detector import detect_fire
from telegram_message import enviar_alerta_telegram
# ================== CONFIGURACIÓN ==================
BROKER = "test.mosquitto.org"
TOPIC = "incendio/sensores"
CAMERA_URL = "http://10.7.135.227:8080"
PHOTO_PATH = "foto_incendio.jpg"
AUDIO_PATH = "audio_incendio.wav"

# ============ API REST  DASHBOARD ==================
API_URL = "http://localhost:5001/api"

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
PESO_IMAGEN = 0.9
PESO_AUDIO = 0.1
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


# ================== API REST=============

def enviar_datos(temp, hum, lum):
    data = {
        "temperatura": round(temp, 1),
        "humedad": round(hum, 1),
        "luminosidad": round(lum, 0)
    }
    try:
        response = requests.post(f"{API_URL}/sensores", json=data, timeout=5)
        if response.status_code == 201:
            print(f"Datos: {data}")
        else:
            print(f"Error respuesta: {response.status_code}")
    except Exception as e:
        print(f"Error enviando datos: {e}")

def enviar_imagen(ruta_imagen):
    try:
        with open(ruta_imagen, "rb") as img_file:
            b64_string = base64.b64encode(img_file.read()).decode("utf-8")
            data_url = f"data:image/jpeg;base64,{b64_string}"
        payload = {
            "nombre": ruta_imagen.split("/")[-1],
            "data_url": data_url
        }
        response = requests.post(f"{API_URL}/imagen", json=payload, timeout=5)
        if response.status_code == 201:
            print(f"Imagen enviada: {payload['nombre']}")
        else:
            print(f"Error respuesta imagen: {response.status_code}")
    except Exception as e:
        print(f"Error enviando imagen: {e}")

def enviar_audio(ruta_audio):
    try:
        # Detectar el tipo MIME del archivo
        mime_type, _ = mimetypes.guess_type(ruta_audio)
        if not mime_type:
            mime_type = "audio/mpeg"  # Valor predeterminado para .mp3

        with open(ruta_audio, "rb") as audio_file:
            b64_string = base64.b64encode(audio_file.read()).decode("utf-8")
            data_url = f"data:{mime_type};base64,{b64_string}"
        payload = {
            "nombre": ruta_audio.split("/")[-1],
            "data_url": data_url
        }
        response = requests.post(f"{API_URL}/audio", json=payload, timeout=5)
        if response.status_code == 201:
            print(f"Audio enviado: {payload['nombre']}")
        else:
            print(f"Error respuesta audio: {response.status_code}")
    except Exception as e:
        print(f"Error enviando audio: {e}")

# ================== MQTT ==================

def on_message(client, userdata, msg):
    global estado_local
    global contador_riesgo, contador_normal
    global evidencia_tomada
    global alerta_enviada 

    data = json.loads(msg.payload.decode())

    temp = data["temp"]
    hum  = data["hum"]
    luz  = data["luz"]
    enviar_datos(temp, hum, luz)

    print(f"Temp={temp}°C | Hum={hum}% | Luz={luz}")

    condicion_riesgo = (temp > TEMP_UMBRAL) or (luz > LUZ_UMBRAL)

    # ================== ESTADO NORMAL ==================
    if estado_local == "Normal":
        data = {"estado": estado_local}
        response = requests.post(f"{API_URL}/estado", json=data)

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
        data = {"estado": estado_local}
        response = requests.post(f"{API_URL}/estado", json=data)

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
                alerta_enviada = False 
                print("Estado: Entorno estabilizado..")
        else:
            contador_normal = 0
    # ================== ESTADO CONFIRMADO ==================
    elif estado_local == "Confirmado":
        data = {"estado": estado_local}
        response = requests.post(f"{API_URL}/estado", json=data)
        if not alerta_enviada:
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