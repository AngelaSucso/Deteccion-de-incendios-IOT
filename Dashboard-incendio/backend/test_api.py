"""
Script para simular un incendio de forma realista
- Empieza con parámetros normales
- Poco a poco se provoca el incendio (no lineal, con fluctuaciones)
- Se mantiene en estado de incendio 3 minutos
- Luego baja gradualmente a normal
- Se repite el ciclo

Ejecutar: python test_api.py
"""

import requests
import time
import random
from datetime import datetime

API_URL = "http://localhost:5001/api"

# Umbrales de alerta (deben coincidir con app.py)
UMBRAL_TEMP_MAX = 35      # Temperatura máxima antes de alerta
UMBRAL_HUM_MIN = 30       # Humedad mínima antes de alerta
UMBRAL_LUM_MAX = 900      # Luminosidad máxima antes de alerta

# Parámetros normales
TEMP_NORMAL = 24
HUM_NORMAL = 55
LUM_NORMAL = 400

# Parámetros de incendio
TEMP_INCENDIO = 45
HUM_INCENDIO = 18
LUM_INCENDIO = 1100

# Tiempos (en segundos)
TIEMPO_SUBIDA = 60        # 1 minuto para que suba al incendio
TIEMPO_INCENDIO = 180     # 3 minutos en estado de incendio
TIEMPO_BAJADA = 60        # 1 minuto para volver a normal
TIEMPO_NORMAL = 30        # 30 segundos en estado normal antes de repetir


def fluctuar(valor, rango=2):
    """Agrega fluctuación realista al valor (sube/baja un poco)"""
    return valor + random.uniform(-rango, rango)


def transicion_con_ruido(valor_actual, valor_objetivo, paso_base, rango_ruido=1.5):
    """
    Hace una transición gradual con ruido (no lineal)
    A veces sube más, a veces menos, a veces retrocede un poco
    """
    # Dirección general
    if valor_actual < valor_objetivo:
        # Subiendo
        paso = random.uniform(paso_base * 0.3, paso_base * 1.5)  # Variación en el paso
        # A veces retrocede un poco (20% de probabilidad)
        if random.random() < 0.2:
            paso = -random.uniform(0.5, 1.5)
        nuevo_valor = valor_actual + paso
        return min(nuevo_valor, valor_objetivo + rango_ruido)
    else:
        # Bajando
        paso = random.uniform(paso_base * 0.3, paso_base * 1.5)
        # A veces sube un poco (20% de probabilidad)
        if random.random() < 0.2:
            paso = -random.uniform(0.5, 1.5)
        nuevo_valor = valor_actual - paso
        return max(nuevo_valor, valor_objetivo - rango_ruido)


def enviar_datos(temp, hum, lum):
    """Envía datos al servidor"""
    try:
        data = {
            "temperatura": round(temp, 1),
            "humedad": round(hum, 1),
            "luminosidad": round(lum, 0)
        }
        response = requests.post(f"{API_URL}/sensores", json=data, timeout=5)
        return response.status_code == 201
    except:
        return False


def mostrar_estado(fase, temp, hum, lum, tiempo_restante=None):
    """Muestra el estado actual en consola"""
    # Determinar alertas
    alertas = []
    if temp >= UMBRAL_TEMP_MAX:
        alertas.append("🌡️")
    if hum <= UMBRAL_HUM_MIN:
        alertas.append("💧")
    if lum >= UMBRAL_LUM_MAX:
        alertas.append("💡")
    
    alerta_str = " ".join(alertas) if alertas else "✅"
    tiempo_str = f" ({tiempo_restante}s)" if tiempo_restante else ""
    
    print(f"[{fase}]{tiempo_str} Temp={temp:.1f}°C | Hum={hum:.1f}% | Lum={lum:.0f}Lux {alerta_str}")


def fase_normal(temp, hum, lum, duracion):
    """Estado normal - valores estables con pequeñas fluctuaciones"""
    print(f"\n{'='*50}")
    print(f"🌿 FASE NORMAL - {duracion} segundos")
    print(f"{'='*50}")
    
    for i in range(duracion):
        # Pequeñas fluctuaciones alrededor de valores normales
        temp = TEMP_NORMAL + random.uniform(-2, 2)
        hum = HUM_NORMAL + random.uniform(-5, 5)
        lum = LUM_NORMAL + random.uniform(-50, 50)
        
        if enviar_datos(temp, hum, lum):
            mostrar_estado("NORMAL", temp, hum, lum, duracion - i)
        
        time.sleep(1)
    
    return temp, hum, lum


def fase_subida(temp, hum, lum, duracion):
    """Transición de normal a incendio - gradual con ruido"""
    print(f"\n{'='*50}")
    print(f"🔥 FASE SUBIDA (provocando incendio) - {duracion} segundos")
    print(f"{'='*50}")
    
    # Calcular pasos base por segundo
    paso_temp = (TEMP_INCENDIO - TEMP_NORMAL) / duracion
    paso_hum = (HUM_NORMAL - HUM_INCENDIO) / duracion  # Humedad baja
    paso_lum = (LUM_INCENDIO - LUM_NORMAL) / duracion
    
    for i in range(duracion):
        # Transición con ruido (no lineal)
        temp = transicion_con_ruido(temp, TEMP_INCENDIO, paso_temp, rango_ruido=2)
        hum = transicion_con_ruido(hum, HUM_INCENDIO, paso_hum, rango_ruido=3)
        lum = transicion_con_ruido(lum, LUM_INCENDIO, paso_lum * 1.2, rango_ruido=30)
        
        # Asegurar que no se pase de los límites
        temp = max(TEMP_NORMAL - 2, min(temp, TEMP_INCENDIO + 5))
        hum = max(HUM_INCENDIO - 5, min(hum, HUM_NORMAL + 5))
        lum = max(LUM_NORMAL - 50, min(lum, LUM_INCENDIO + 100))
        
        if enviar_datos(temp, hum, lum):
            mostrar_estado("SUBIDA", temp, hum, lum, duracion - i)
        
        time.sleep(1)
    
    return temp, hum, lum


def fase_incendio(temp, hum, lum, duracion):
    """Estado de incendio - valores altos con fluctuaciones intensas"""
    print(f"\n{'='*50}")
    print(f"🚨 FASE INCENDIO - {duracion} segundos (3 minutos)")
    print(f"{'='*50}")
    
    for i in range(duracion):
        # Fluctuaciones más intensas durante el incendio
        temp = TEMP_INCENDIO + random.uniform(-3, 5)  # Puede subir más
        hum = HUM_INCENDIO + random.uniform(-3, 5)    # Muy baja
        lum = LUM_INCENDIO + random.uniform(-100, 150)  # Muy variable (llamas)
        
        if enviar_datos(temp, hum, lum):
            mostrar_estado("🔥INCENDIO��", temp, hum, lum, duracion - i)
        
        time.sleep(1)
    
    return temp, hum, lum


def fase_bajada(temp, hum, lum, duracion):
    """Transición de incendio a normal - gradual con ruido"""
    print(f"\n{'='*50}")
    print(f"💨 FASE BAJADA (controlando incendio) - {duracion} segundos")
    print(f"{'='*50}")
    
    # Calcular pasos base por segundo
    paso_temp = (TEMP_INCENDIO - TEMP_NORMAL) / duracion
    paso_hum = (HUM_NORMAL - HUM_INCENDIO) / duracion
    paso_lum = (LUM_INCENDIO - LUM_NORMAL) / duracion
    
    for i in range(duracion):
        # Transición con ruido
        temp = transicion_con_ruido(temp, TEMP_NORMAL, paso_temp, rango_ruido=2)
        hum = transicion_con_ruido(hum, HUM_NORMAL, paso_hum, rango_ruido=3)
        lum = transicion_con_ruido(lum, LUM_NORMAL, paso_lum, rango_ruido=30)
        
        # Asegurar límites
        temp = max(TEMP_NORMAL - 2, min(temp, TEMP_INCENDIO + 3))
        hum = max(HUM_INCENDIO - 3, min(hum, HUM_NORMAL + 5))
        lum = max(LUM_NORMAL - 50, min(lum, LUM_INCENDIO + 50))
        
        if enviar_datos(temp, hum, lum):
            mostrar_estado("BAJADA", temp, hum, lum, duracion - i)
        
        time.sleep(1)
    
    return temp, hum, lum


def simular_ciclo_incendio():
    """Ejecuta un ciclo completo de simulación"""
    ciclo = 1
    
    # Valores iniciales normales
    temp = TEMP_NORMAL
    hum = HUM_NORMAL
    lum = LUM_NORMAL
    
    while True:
        print(f"\n{'#'*60}")
        print(f"#  CICLO {ciclo} - Simulación de Incendio")
        print(f"#  Duración total del ciclo: ~{TIEMPO_NORMAL + TIEMPO_SUBIDA + TIEMPO_INCENDIO + TIEMPO_BAJADA} segundos")
        print(f"{'#'*60}")
        
        # 1. Estado normal
        temp, hum, lum = fase_normal(temp, hum, lum, TIEMPO_NORMAL)
        
        # 2. Subida gradual hacia incendio
        temp, hum, lum = fase_subida(temp, hum, lum, TIEMPO_SUBIDA)
        
        # 3. Estado de incendio (3 minutos)
        temp, hum, lum = fase_incendio(temp, hum, lum, TIEMPO_INCENDIO)
        
        # 4. Bajada gradual hacia normal
        temp, hum, lum = fase_bajada(temp, hum, lum, TIEMPO_BAJADA)
        
        print(f"\n✅ Ciclo {ciclo} completado. Iniciando siguiente ciclo...")
        ciclo += 1


if __name__ == "__main__":
    print("=" * 60)
    print("🔥 SIMULADOR DE INCENDIO REALISTA")
    print("=" * 60)
    print(f"API URL: {API_URL}")
    print(f"\nUmbrales de alerta:")
    print(f"  🌡️ Temperatura máx: {UMBRAL_TEMP_MAX}°C")
    print(f"  💧 Humedad mín: {UMBRAL_HUM_MIN}%")
    print(f"  💡 Luminosidad máx: {UMBRAL_LUM_MAX} Lux")
    print(f"\nFases del ciclo:")
    print(f"  1. Normal: {TIEMPO_NORMAL}s")
    print(f"  2. Subida: {TIEMPO_SUBIDA}s")
    print(f"  3. Incendio: {TIEMPO_INCENDIO}s (3 min)")
    print(f"  4. Bajada: {TIEMPO_BAJADA}s")
    print(f"\nDuración total por ciclo: ~{TIEMPO_NORMAL + TIEMPO_SUBIDA + TIEMPO_INCENDIO + TIEMPO_BAJADA}s")
    print("=" * 60)
    
    # Verificar conexión
    print("\nVerificando conexión con el servidor...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor conectado correctamente\n")
        else:
            print("⚠️ Servidor respondió pero con error")
    except Exception as e:
        print(f"❌ No se pudo conectar al servidor: {e}")
        print("Asegúrate de que app.py está corriendo en el puerto 5001")
        exit(1)
    
    print("Presiona Ctrl+C para detener la simulación\n")
    
    try:
        simular_ciclo_incendio()
    except KeyboardInterrupt:
        print("\n\n🛑 Simulación detenida por el usuario")
