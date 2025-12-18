"""
Script para entrenar el detector de incendios por audio
Ejecutar DESPUÉS de descargar_dataset.py
"""

import os
import librosa
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import pickle

def extraer_features(archivo_audio):
    """
    Extrae características importantes del audio para ML
    """
    try:
        # Cargar audio
        y, sr = librosa.load(archivo_audio, duration=5)
        
        # Características importantes para detectar fuego:
        # 1. MFCC - Captura textura del sonido (crepitar)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = np.mean(mfcc, axis=1)
        
        # 2. Spectral Centroid - Brillo del sonido
        centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
        
        # 3. Zero Crossing Rate - Cambios rápidos (crepitar)
        zcr = np.mean(librosa.feature.zero_crossing_rate(y))
        
        # 4. RMS Energy - Intensidad del sonido
        rms = np.mean(librosa.feature.rms(y=y))
        
        # 5. Spectral Rolloff - Energía en altas frecuencias
        rolloff = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))
        
        # Combinar todas las features
        features = np.concatenate([mfcc_mean, [centroid, zcr, rms, rolloff]])
        return features
        
    except Exception as e:
        print(f"❌ Error procesando {archivo_audio}: {e}")
        return None

def cargar_dataset():
    """
    Carga todos los audios y extrae sus características
    """
    X = []  # Features
    y = []  # Labels (0=no incendio, 1=incendio)
    
    print("🔍 Procesando audios de INCENDIO...")
    carpeta_incendio = "dataset/incendio"
    for archivo in os.listdir(carpeta_incendio):
        ruta = os.path.join(carpeta_incendio, archivo)
        features = extraer_features(ruta)
        if features is not None:
            X.append(features)
            y.append(1)  # Etiqueta: SÍ es incendio
            print(f"  ✅ {archivo}")
    
    print("\n🔍 Procesando audios NORMALES...")
    carpeta_normal = "dataset/no_incendio"
    for archivo in os.listdir(carpeta_normal):
        ruta = os.path.join(carpeta_normal, archivo)
        features = extraer_features(ruta)
        if features is not None:
            X.append(features)
            y.append(0)  # Etiqueta: NO es incendio
            print(f"  ✅ {archivo}")
    
    return np.array(X), np.array(y)

def entrenar_modelo():
    """
    Entrena el clasificador con los audios del dataset
    """
    print("\n" + "="*50)
    print("🧠 ENTRENANDO MODELO DETECTOR DE INCENDIOS")
    print("="*50 + "\n")
    
    # Cargar datos
    X, y = cargar_dataset()
    
    print(f"\n📊 Dataset cargado:")
    print(f"   Total audios: {len(X)}")
    print(f"   Incendios: {np.sum(y == 1)}")
    print(f"   Normales: {np.sum(y == 0)}")
    
    # Dividir en entrenamiento y prueba
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Entrenar modelo
    print("\n🔥 Entrenando Random Forest...")
    modelo = RandomForestClassifier(
    n_estimators=200,      # Más árboles = mejor
    max_depth=10,          # Más profundidad
    min_samples_split=2,   # Menos muestras para dividir
    random_state=42
)
    modelo.fit(X_train, y_train)
    
    # Evaluar
    y_pred = modelo.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n✅ Entrenamiento completado!")
    print(f"📈 Precisión: {accuracy*100:.1f}%")
    print("\n📋 Reporte detallado:")
    print(classification_report(y_test, y_pred, 
                                target_names=['No Incendio', 'Incendio']))
    
    # Guardar modelo entrenado
    with open('modelo_incendio.pkl', 'wb') as f:
        pickle.dump(modelo, f)
    
    print("\n💾 Modelo guardado como 'modelo_incendio.pkl'")
    print("✅ ¡Listo para usar en detector_audio_incendio.py!")

if __name__ == "__main__":
    entrenar_modelo()