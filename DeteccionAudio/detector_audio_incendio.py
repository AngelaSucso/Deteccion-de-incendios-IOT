"""
DETECTOR DE INCENDIOS POR AUDIO
Módulo independiente para analizar archivos de audio
Uso: detectar_incendio("audio_prueba.wav")
"""

import librosa
import numpy as np
import pickle
import os

# Cargar modelo entrenado
MODELO_PATH = "modelo_incendio.pkl"

def extraer_features(archivo_audio):
    """
    Extrae características del audio (igual que en entrenamiento)
    """
    try:
        y, sr = librosa.load(archivo_audio, duration=5)
        
        # Extraer características
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = np.mean(mfcc, axis=1)
        centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
        zcr = np.mean(librosa.feature.zero_crossing_rate(y))
        rms = np.mean(librosa.feature.rms(y=y))
        rolloff = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))
        
        features = np.concatenate([mfcc_mean, [centroid, zcr, rms, rolloff]])
        return features
        
    except Exception as e:
        print(f"❌ Error procesando audio: {e}")
        return None

def detectar_incendio(ruta_audio):
    """
    FUNCIÓN PRINCIPAL
    Analiza un archivo de audio y determina si hay incendio
    
    Args:
        ruta_audio (str): Ruta al archivo de audio (.wav, .mp3, etc)
    
    Returns:
        dict: {
            "incendio_detectado": bool,
            "confianza": float (0-1),
            "mensaje": str
        }
    """
    
    # Verificar que existe el audio
    if not os.path.exists(ruta_audio):
        return {
            "incendio_detectado": False,
            "confianza": 0.0,
            "mensaje": f"❌ Archivo no encontrado: {ruta_audio}"
        }
    
    # Verificar que existe el modelo
    if not os.path.exists(MODELO_PATH):
        return {
            "incendio_detectado": False,
            "confianza": 0.0,
            "mensaje": "❌ Modelo no entrenado. Ejecuta entrenar_modelo.py primero"
        }
    
    # Cargar modelo
    try:
        with open(MODELO_PATH, 'rb') as f:
            modelo = pickle.load(f)
    except Exception as e:
        return {
            "incendio_detectado": False,
            "confianza": 0.0,
            "mensaje": f"❌ Error cargando modelo: {e}"
        }
    
    # Extraer características del audio
    print(f"🔍 Analizando: {ruta_audio}...")
    features = extraer_features(ruta_audio)
    
    if features is None:
        return {
            "incendio_detectado": False,
            "confianza": 0.0,
            "mensaje": "❌ No se pudo procesar el audio"
        }
    
    # Predecir
    prediccion = modelo.predict([features])[0]
    probabilidades = modelo.predict_proba([features])[0]
    confianza = probabilidades[prediccion]
    
    # Resultado
    es_incendio = bool(prediccion == 1)
    
    if es_incendio:
        mensaje = f"🔥 ¡INCENDIO DETECTADO! (Confianza: {confianza*100:.1f}%)"
    else:
        mensaje = f"✅ No se detectó incendio (Confianza: {confianza*100:.1f}%)"
    
    return {
        "incendio_detectado": es_incendio,
        "confianza": float(confianza),
        "mensaje": mensaje
    }

# ============= TESTING =============
if __name__ == "__main__":
    import sys
    
    print("="*60)
    print("🔥 DETECTOR DE INCENDIOS POR AUDIO")
    print("="*60 + "\n")
    
    # Si pasan archivo por argumentos
    if len(sys.argv) > 1:
        archivo = sys.argv[1]
        resultado = detectar_incendio(archivo)
        print(resultado["mensaje"])
        print(f"\nResultado completo: {resultado}")
    else:
        # Modo de prueba interactivo
        print("📝 Modo de prueba")
        print("Ingresa la ruta del audio a analizar:")
        print("Ejemplo: audio_incendio.wav\n")
        
        ruta = input("Ruta del audio: ").strip()
        
        if ruta:
            resultado = detectar_incendio(ruta)
            print("\n" + "="*60)
            print(resultado["mensaje"])
            print("="*60)
            print(f"\n📊 Detalles:")
            print(f"   Incendio detectado: {resultado['incendio_detectado']}")
            print(f"   Confianza: {resultado['confianza']*100:.1f}%")
        else:
            print("❌ No ingresaste ninguna ruta")