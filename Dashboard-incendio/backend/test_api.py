
# cSpell:disable
import requests
import time
import random

API_URL = "http://localhost:5001/api"

# Umbrales de alerta (deben coincidir con app.py)
UMBRAL_TEMP_MAX = 45
UMBRAL_HUM_MIN = 20
UMBRAL_LUM_MAX = 2000

# Parámetros normales
TEMP_NORMAL = 24
HUM_NORMAL = 55
LUM_NORMAL = 400

# Parámetros de incendio
TEMP_INCENDIO = 50
HUM_INCENDIO = 15
LUM_INCENDIO = 2200

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


# Estado previo para evitar repeticiones
estado_previo = None

def enviar_estado_si_cambia(temp, hum, lum):
    global estado_previo
    if temp >= UMBRAL_TEMP_MAX or hum <= UMBRAL_HUM_MIN or lum >= UMBRAL_LUM_MAX:
        nuevo_estado = "riesgo"
    else:
        nuevo_estado = "normal"
    if nuevo_estado != estado_previo:
        data = {"estado": nuevo_estado}
        try:
            response = requests.post(f"{API_URL}/estado", json=data, timeout=5)
            if response.status_code == 201:
                print(f"[ESTADO] {nuevo_estado} enviado")
            else:
                print(f"[ESTADO] Error respuesta: {response.status_code}")
        except Exception as e:

            print(f"[ESTADO] Error enviando estado: {e}")
        estado_previo = nuevo_estado


def simular_incendio():
    ciclo = 1
    while True:
        print(f"\n{'#'*60}")
        print(f"#  CICLO {ciclo} - Simulación de Incendio")
        print(f"{'#'*60}")


        # Fase normal
        for i in range(15):
            t = TEMP_NORMAL + random.uniform(-2, 2)
            h = HUM_NORMAL + random.uniform(-5, 5)
            l = LUM_NORMAL + random.uniform(-50, 50)
            enviar_datos(t, h, l)
            enviar_estado_si_cambia(t, h, l)
            time.sleep(1)

        # Fase subida
        pasos = 10
        for i in range(1, pasos+1):
            t = TEMP_NORMAL + (TEMP_INCENDIO - TEMP_NORMAL) * i/pasos + random.uniform(-1, 1)
            h = HUM_NORMAL + (HUM_INCENDIO - HUM_NORMAL) * i/pasos + random.uniform(-2, 2)
            l = LUM_NORMAL + (LUM_INCENDIO - LUM_NORMAL) * i/pasos + random.uniform(-30, 30)
            enviar_datos(t, h, l)
            enviar_estado_si_cambia(t, h, l)
            time.sleep(1)

        # Fase incendio
        for i in range(20):
            t = TEMP_INCENDIO + random.uniform(-2, 3)
            h = HUM_INCENDIO + random.uniform(-3, 2)
            l = LUM_INCENDIO + random.uniform(-100, 100)
            enviar_datos(t, h, l)
            enviar_estado_si_cambia(t, h, l)
            time.sleep(1)

        # Fase bajada
        for i in range(1, pasos+1):
            t = TEMP_INCENDIO + (TEMP_NORMAL - TEMP_INCENDIO) * i/pasos + random.uniform(-1, 1)
            h = HUM_INCENDIO + (HUM_NORMAL - HUM_INCENDIO) * i/pasos + random.uniform(-2, 2)
            l = LUM_INCENDIO + (LUM_NORMAL - LUM_INCENDIO) * i/pasos + random.uniform(-30, 30)
            enviar_datos(t, h, l)
            enviar_estado_si_cambia(t, h, l)
            time.sleep(1)

        ciclo += 1

if __name__ == "__main__":
    print("=" * 60)
    print("🔥 SIMULADOR DE INCENDIO (con transición)")
    print("=" * 60)
    print(f"API URL: {API_URL}")
    print(f"  🌡️ Temperatura máx: {UMBRAL_TEMP_MAX}°C")
    print(f"  💧 Humedad mín: {UMBRAL_HUM_MIN}%")
    print(f"  💡 Luminosidad máx: {UMBRAL_LUM_MAX} Lux")
    print("=" * 60)
    print("Simulando ciclo: normal → subida → incendio → bajada → repeat")
    try:
        simular_incendio()
    except KeyboardInterrupt:
        print("\n🛑 Simulación detenida por el usuario")
