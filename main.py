# ============================================
# SISTEMA DE DETECCIÓN DE INCENDIOS
# Versión completa con AWS IoT Core
# ============================================

from awsiot import mqtt_connection_builder
from awscrt import mqtt
import json
import time
import requests
import base64
import mimetypes
import boto3
from datetime import datetime

from DeteccionAudio.detector_audio_incendio import detectar_incendio
from DeteccionImagen.detector import detect_fire
from telegram_message import enviar_alerta_telegram

# ════════════════════════════════════════════
# CONFIGURACIÓN AWS IoT CORE
# ════════════════════════════════════════════
ENDPOINT = "a1b9nxragudit3-ats.iot.us-east-1.amazonaws.com"
CLIENT_ID = "main-fire-detector"
PATH_TO_CERTIFICATE = "./arduino-incendio.cert.pem"
PATH_TO_PRIVATE_KEY = "./arduino-incendio.private.key"
PATH_TO_AMAZON_ROOT_CA_1 = "./root-CA.crt"
TOPIC_SENSORES = "sdk/test/python"

# ════════════════════════════════════════════
# CONFIGURACIÓN GENERAL
# ════════════════════════════════════════════
CAMERA_URL = "http://10.7.135.227:8080"
PHOTO_PATH = "foto_incendio.jpg"
AUDIO_PATH = "audio_incendio.wav"

# API REST DASHBOARD
API_URL = "http://localhost:5001/api"

# Umbrales
TEMP_UMBRAL = 45
LUZ_UMBRAL = 2000
HUMEDAD_MIN = 20

# Persistencia
LECTURAS_RIESGO = 5
LECTURAS_RECUPERACION = 5

# ════════════════════════════════════════════
# ESTADO LOCAL
# ════════════════════════════════════════════
estado_local = "Normal"
contador_riesgo = 0
contador_normal = 0
evidencia_tomada = False

# Umbral de decisión
PESO_IMAGEN = 0.9
PESO_AUDIO = 0.1
UMBRAL_ALERTA = 0.6
alerta_enviada = False

# Cliente S3 (opcional, para subir a AWS)
s3_client = boto3.client('s3')
BUCKET_NAME = "incendios-multimedia-227338491492"

# ════════════════════════════════════════════
# FUNCIONES DE CAPTURA
# ════════════════════════════════════════════

def tomar_foto():
    """Captura foto desde cámara IP"""
    try:
        img = requests.get(f"{CAMERA_URL}/shot.jpg", timeout=5).content
        with open(PHOTO_PATH, "wb") as f:
            f.write(img)
        print("✅ Foto capturada")
        return True
    except Exception as e:
        print(f"❌ Error tomando foto: {e}")
        return False


def grabar_audio(duracion=5):
    """Graba audio desde cámara IP"""
    try:
        response = requests.get(f"{CAMERA_URL}/audio.wav", stream=True, timeout=duracion+2)
        with open(AUDIO_PATH, "wb") as f:
            inicio = time.time()
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                if time.time() - inicio > duracion:
                    break
        print("✅ Audio grabado")
        return True
    except Exception as e:
        print(f"❌ Error grabando audio: {e}")
        return False


# ════════════════════════════════════════════
# FUNCIONES DE ANÁLISIS IA
# ════════════════════════════════════════════

def detectar_incendio_imagen(image_path):
    """Detecta incendio en imagen con YOLOv8"""
    result = detect_fire(image_path)
    
    if result is False:
        return {"confianza": 0.0}
    else:
        detected, image_path, confidence = result
        return {"confianza": confidence}


def decidir_alerta(prob_imagen, prob_audio):
    """Fusiona probabilidades de imagen y audio"""
    score = (
        PESO_IMAGEN * prob_imagen +
        PESO_AUDIO * prob_audio
    )
    return score >= UMBRAL_ALERTA, score


# ════════════════════════════════════════════
# FUNCIONES DE DASHBOARD (API REST)
# ════════════════════════════════════════════

def enviar_datos(temp, hum, lum):
    """Envía datos de sensores al dashboard"""
    data = {
        "temperatura": round(temp, 1),
        "humedad": round(hum, 1),
        "luminosidad": round(lum, 0)
    }
    try:
        response = requests.post(f"{API_URL}/sensores", json=data, timeout=5)
        if response.status_code == 201:
            print(f"📊 Dashboard actualizado: {data}")
        else:
            print(f"⚠️ Error dashboard: {response.status_code}")
    except Exception as e:
        print(f"❌ Error enviando datos dashboard: {e}")


def enviar_estado(estado):
    """Envía estado al dashboard"""
    data = {"estado": estado}
    try:
        response = requests.post(f"{API_URL}/estado", json=data, timeout=5)
        if response.status_code == 201:
            print(f"📡 Estado enviado: {estado}")
    except Exception as e:
        print(f"❌ Error enviando estado: {e}")


def enviar_imagen(ruta_imagen):
    """Envía imagen al dashboard"""
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
            print(f"📸 Imagen enviada al dashboard: {payload['nombre']}")
        else:
            print(f"⚠️ Error enviando imagen: {response.status_code}")
    except Exception as e:
        print(f"❌ Error enviando imagen: {e}")


def enviar_audio(ruta_audio):
    """Envía audio al dashboard"""
    try:
        mime_type, _ = mimetypes.guess_type(ruta_audio)
        if not mime_type:
            mime_type = "audio/wav"
        
        with open(ruta_audio, "rb") as audio_file:
            b64_string = base64.b64encode(audio_file.read()).decode("utf-8")
            data_url = f"data:{mime_type};base64,{b64_string}"
        
        payload = {
            "nombre": ruta_audio.split("/")[-1],
            "data_url": data_url
        }
        
        response = requests.post(f"{API_URL}/audio", json=payload, timeout=5)
        if response.status_code == 201:
            print(f"🎙 Audio enviado al dashboard: {payload['nombre']}")
        else:
            print(f"⚠️ Error enviando audio: {response.status_code}")
    except Exception as e:
        print(f"❌ Error enviando audio: {e}")


# ════════════════════════════════════════════
# FUNCIONES AWS (OPCIONAL - PARA LAMBDA)
# ════════════════════════════════════════════

def subir_a_s3(archivo_local, carpeta="fotos"):
    """Sube archivo a S3 (opcional)"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d")
        s3_key = f"{carpeta}/{timestamp}/{archivo_local}"
        
        print(f"☁️ Subiendo a S3: {s3_key}...")
        s3_client.upload_file(
            archivo_local,
            BUCKET_NAME,
            s3_key,
            ExtraArgs={'ContentType': 'image/jpeg' if 'foto' in archivo_local else 'audio/wav'}
        )
        
        s3_url = f"s3://{BUCKET_NAME}/{s3_key}"
        print(f"✅ Subido a S3: {s3_url}")
        return s3_url
    except Exception as e:
        print(f"❌ Error subiendo a S3: {e}")
        return None


def invocar_lambda_analisis(foto_s3, audio_s3, evento_id):
    """Invoca Lambda de análisis (opcional)"""
    try:
        lambda_client = boto3.client('lambda')
        
        payload = {
            "evento_id": evento_id,
            "foto_s3": foto_s3,
            "audio_s3": audio_s3,
            "timestamp": int(time.time())
        }
        
        print(f"🚀 Invocando Lambda...")
        response = lambda_client.invoke(
            FunctionName='AnalizadorIncendioIA',
            InvocationType='Event',
            Payload=json.dumps(payload)
        )
        
        print(f"✅ Lambda invocada")
        return True
    except Exception as e:
        print(f"❌ Error Lambda: {e}")
        return False


# ════════════════════════════════════════════
# CALLBACK: LÓGICA PRINCIPAL
# ════════════════════════════════════════════

def on_message_received(topic, payload, **kwargs):
    """
    Callback cuando llega mensaje MQTT de AWS IoT Core
    Contiene toda la lógica de detección
    """
    global estado_local
    global contador_riesgo, contador_normal
    global evidencia_tomada
    global alerta_enviada
    
    # Parsear mensaje
    data = json.loads(payload.decode('utf-8'))
    
    # Extraer datos
    temp = data.get("temp", 0)
    hum = data.get("hum", 0)
    
    # Adaptarse a ambos formatos (RGB o luz)
    if "luz" in data:
        luz = data["luz"]
    else:
        r = data.get("r", 0)
        g = data.get("g", 0)
        b = data.get("b", 0)
        luz = r + g + b
    
    print(f"\n📊 DATOS RECIBIDOS:")
    print(f"   🌡 Temp: {temp}°C | 💧 Hum: {hum}% | 💡 Luz: {luz}")
    
    # Enviar al dashboard
    enviar_datos(temp, hum, luz)
    
    # Detectar condiciones de riesgo
    condicion_riesgo = (temp > TEMP_UMBRAL) or (luz > LUZ_UMBRAL)
    
    # ════════════════════════════════════════════
    # ESTADO: NORMAL
    # ════════════════════════════════════════════
    if estado_local == "Normal":
        enviar_estado("normal")
        
        if condicion_riesgo:
            contador_riesgo += 1
            print(f"⚠️ Lecturas en riesgo: {contador_riesgo}/{LECTURAS_RIESGO}")
            
            if contador_riesgo >= LECTURAS_RIESGO:
                estado_local = "Riesgo"
                evidencia_tomada = False
                contador_normal = 0
                print("🔥 Estado: RIESGO - Capturando evidencias...")
        else:
            contador_riesgo = 0
    
    # ════════════════════════════════════════════
    # ESTADO: RIESGO
    # ════════════════════════════════════════════
    elif estado_local == "Riesgo":
        enviar_estado("riesgo")
        
        # Tomar evidencia SOLO UNA VEZ
        if not evidencia_tomada:
            if hum < HUMEDAD_MIN:
                print(f"💧 Humedad baja ({hum}%) - Condición favorable al fuego")
            
            # CAPTURAR EVIDENCIA
            foto_ok = tomar_foto()
            audio_ok = grabar_audio(5)
            evidencia_tomada = True
            
            if foto_ok and audio_ok:
                # Enviar al dashboard
                enviar_imagen(PHOTO_PATH)
                enviar_audio(AUDIO_PATH)
                
                # ===== ANÁLISIS CON IA =====
                print("\n🔍 Analizando evidencia con IA...")
                
                # Detección por audio
                resultado_audio = detectar_incendio(AUDIO_PATH)
                prob_audio = resultado_audio["confianza"]
                print(f"   🎙 Audio ML: {prob_audio*100:.1f}%")
                
                # Detección por imagen
                resultado_imagen = detectar_incendio_imagen(PHOTO_PATH)
                prob_imagen = resultado_imagen["confianza"]
                print(f"   📸 YOLOv8: {prob_imagen*100:.1f}%")
                
                # Fusión de probabilidades
                alerta_final, score = decidir_alerta(prob_imagen, prob_audio)
                print(f"   🎯 Score final: {score*100:.1f}%")
                
                if alerta_final:
                    estado_local = "Confirmado"
                    alerta_enviada = False
                    print("\n🚨🚨🚨 INCENDIO CONFIRMADO 🚨🚨🚨")
                else:
                    print("✅ Evidencia insuficiente, continuando monitoreo...")
        
        # Verificar recuperación
        if not condicion_riesgo:
            contador_normal += 1
            print(f"✅ Lecturas normales: {contador_normal}/{LECTURAS_RECUPERACION}")
            
            if contador_normal >= LECTURAS_RECUPERACION:
                estado_local = "Normal"
                contador_riesgo = 0
                contador_normal = 0
                evidencia_tomada = False
                alerta_enviada = False
                print("✅ Estado: Entorno ESTABILIZADO")
        else:
            contador_normal = 0
    
    # ════════════════════════════════════════════
    # ESTADO: CONFIRMADO
    # ════════════════════════════════════════════
    elif estado_local == "Confirmado":
        enviar_estado("incendio confirmado")
        enviar_imagen(PHOTO_PATH)
        enviar_audio(AUDIO_PATH)
        
        if not alerta_enviada:
            print("\n📱 Enviando alerta Telegram...")
            enviar_alerta_telegram(PHOTO_PATH)
            alerta_enviada = True
            
            # Subir a S3 (fotos y audios se guardan local y en S3)
            evento_id = f"incendio_{int(time.time())}"
            foto_s3 = subir_a_s3(PHOTO_PATH, "fotos")
            audio_s3 = subir_a_s3(AUDIO_PATH, "audios")
            
            # TODO: Invocar Lambda cuando los modelos estén en la nube
            # if foto_s3 and audio_s3:
            #     invocar_lambda_analisis(foto_s3, audio_s3, evento_id)
    
    print(f"📍 Estado actual: {estado_local}")
    print("-" * 60)


# ════════════════════════════════════════════
# CONEXIÓN A AWS IoT CORE
# ════════════════════════════════════════════

print("\n")
print("╔════════════════════════════════════════════════╗")
print("║  🔥 SISTEMA DE DETECCIÓN DE INCENDIOS         ║")
print("║     Versión AWS IoT Core + IA Local           ║")
print("╚════════════════════════════════════════════════╝")
print()

print("🔧 Configurando conexión a AWS IoT Core...")
print(f"   📍 Endpoint: {ENDPOINT}")
print(f"   🆔 Client ID: {CLIENT_ID}")
print(f"   📜 Certificado: {PATH_TO_CERTIFICATE}")
print(f"   🔑 Clave privada: {PATH_TO_PRIVATE_KEY}")
print(f"   🏛 Root CA: {PATH_TO_AMAZON_ROOT_CA_1}")

try:
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=ENDPOINT,
        cert_filepath=PATH_TO_CERTIFICATE,
        pri_key_filepath=PATH_TO_PRIVATE_KEY,
        ca_filepath=PATH_TO_AMAZON_ROOT_CA_1,
        client_id=CLIENT_ID,
        clean_session=False,
        keep_alive_secs=30
    )

    print("🌐 Conectando a AWS IoT Core...")
    connect_future = mqtt_connection.connect()
    connect_future.result()
    print("✅ Conectado a AWS IoT Core")
except Exception as e:
    print(f"\n❌ ERROR DE CONEXIÓN:")
    print(f"   {type(e).__name__}: {e}")
    print(f"\n🔍 POSIBLES CAUSAS:")
    print(f"   1. Certificados incorrectos o revocados")
    print(f"   2. Política de AWS IoT sin permisos suficientes")
    print(f"   3. Endpoint incorrecto")
    print(f"   4. Thing no existe o no está asociado al certificado")
    print(f"\n💡 SOLUCIÓN:")
    print(f"   • Verifica en AWS IoT Console que el certificado esté ACTIVO")
    print(f"   • Revisa que la política tenga permisos: iot:Connect, iot:Publish, iot:Subscribe, iot:Receive")
    print(f"   • Confirma que el endpoint coincida con: aws iot describe-endpoint --endpoint-type iot:Data-ATS")
    exit(1)

print(f"👂 Suscribiéndose al topic: {TOPIC_SENSORES}")
subscribe_future, packet_id = mqtt_connection.subscribe(
    topic=TOPIC_SENSORES,
    qos=mqtt.QoS.AT_LEAST_ONCE,
    callback=on_message_received
)
subscribe_result = subscribe_future.result()
print("✅ Suscrito exitosamente\n")

print("━" * 60)
print("🚨 SISTEMA ACTIVO")
print("━" * 60)
print(f"📡 Esperando datos de sensores...")
print(f"🎯 Configuración:")
print(f"   • Temperatura > {TEMP_UMBRAL}°C")
print(f"   • Luminosidad > {LUZ_UMBRAL}")
print(f"   • Humedad < {HUMEDAD_MIN}%")
print(f"   • Confirmación: {LECTURAS_RIESGO} lecturas consecutivas")
print(f"   • Dashboard: {API_URL}")
print("━" * 60)
print()

# Mantener conexión activa
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\n⛔ Deteniendo sistema...")
    mqtt_connection.disconnect()
    print("✅ Desconectado de AWS IoT Core")
    print("👋 Sistema finalizado")