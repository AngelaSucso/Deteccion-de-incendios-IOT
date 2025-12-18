"""
Servidor que simula una cámara y micrófono IoT
Cuando recibe un POST, espera unos segundos y retorna una imagen y audio random
Ejecutar: python camara_simulada.py
"""

from flask import Flask, jsonify, send_file
from flask_cors import CORS
import os
import random
import time
import base64

app = Flask(__name__)
CORS(app)

# Carpetas de medios (relativa al proyecto)
IMAGES_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'img')
AUDIO_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'audio')

@app.route('/api/capturar', methods=['POST'])
def capturar_imagen():
    """
    Simula la captura de imagen y audio.
    Espera unos segundos y retorna imagen + audio random en base64.
    """
    try:
        print("📷🎤 Solicitud de captura recibida...")
        
        # Simular tiempo de captura (2-4 segundos)
        delay = random.uniform(2, 4)
        print(f"⏳ Capturando imagen y audio... ({delay:.1f}s)")
        time.sleep(delay)
        
        # === IMAGEN ===
        imagenes = [f for f in os.listdir(IMAGES_FOLDER) 
                   if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
        
        imagen_data = None
        if imagenes:
            imagen_seleccionada = random.choice(imagenes)
            ruta_imagen = os.path.join(IMAGES_FOLDER, imagen_seleccionada)
            print(f"📸 Imagen seleccionada: {imagen_seleccionada}")
            
            with open(ruta_imagen, 'rb') as img_file:
                imagen_base64 = base64.b64encode(img_file.read()).decode('utf-8')
            
            extension = imagen_seleccionada.lower().split('.')[-1]
            mime_type_img = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif'
            }.get(extension, 'image/jpeg')
            
            imagen_data = {
                'nombre': imagen_seleccionada,
                'base64': imagen_base64,
                'mime_type': mime_type_img,
                'data_url': f'data:{mime_type_img};base64,{imagen_base64}'
            }
        
        # === AUDIO ===
        audios = [f for f in os.listdir(AUDIO_FOLDER) 
                 if f.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a'))]
        
        audio_data = None
        if audios:
            audio_seleccionado = random.choice(audios)
            ruta_audio = os.path.join(AUDIO_FOLDER, audio_seleccionado)
            print(f"🎵 Audio seleccionado: {audio_seleccionado}")
            
            with open(ruta_audio, 'rb') as audio_file:
                audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')
            
            extension_audio = audio_seleccionado.lower().split('.')[-1]
            mime_type_audio = {
                'mp3': 'audio/mpeg',
                'wav': 'audio/wav',
                'ogg': 'audio/ogg',
                'm4a': 'audio/mp4'
            }.get(extension_audio, 'audio/mpeg')
            
            audio_data = {
                'nombre': audio_seleccionado,
                'base64': audio_base64,
                'mime_type': mime_type_audio,
                'data_url': f'data:{mime_type_audio};base64,{audio_base64}'
            }
        
        return jsonify({
            'status': 'ok',
            'mensaje': 'Captura completada correctamente',
            'imagen': imagen_data,
            'audio': audio_data
        }), 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Verificar que el servidor de cámara/audio está funcionando"""
    imagenes = []
    audios = []
    try:
        imagenes = [f for f in os.listdir(IMAGES_FOLDER) 
                   if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
        audios = [f for f in os.listdir(AUDIO_FOLDER) 
                 if f.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a'))]
    except:
        pass
    
    return jsonify({
        'status': 'ok',
        'mensaje': 'Servidor de cámara/audio simulado funcionando',
        'imagenes_disponibles': len(imagenes),
        'audios_disponibles': len(audios),
        'carpeta_img': IMAGES_FOLDER,
        'carpeta_audio': AUDIO_FOLDER
    }), 200


if __name__ == '__main__':
    print("=" * 50)
    print("📷🎤 SERVIDOR DE CÁMARA Y AUDIO SIMULADO")
    print("=" * 50)
    print(f"Carpeta de imágenes: {IMAGES_FOLDER}")
    print(f"Carpeta de audios: {AUDIO_FOLDER}")
    
    try:
        imagenes = [f for f in os.listdir(IMAGES_FOLDER) 
                   if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
        print(f"\nImágenes encontradas: {len(imagenes)}")
        for img in imagenes:
            print(f"  📸 {img}")
    except Exception as e:
        print(f"⚠️ Error accediendo a imágenes: {e}")
    
    try:
        audios = [f for f in os.listdir(AUDIO_FOLDER) 
                 if f.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a'))]
        print(f"\nAudios encontrados: {len(audios)}")
        for aud in audios:
            print(f"  🎵 {aud}")
    except Exception as e:
        print(f"⚠️ Error accediendo a audios: {e}")
    
    print("=" * 50)
    print("🚀 Iniciando servidor en puerto 5002...")
    print("Endpoint: POST http://localhost:5002/api/capturar")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5002, debug=True)
