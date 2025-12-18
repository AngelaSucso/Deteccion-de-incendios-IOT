from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import json
import requests
import threading

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# ============================================
# 🔥 CONFIGURACIÓN DE UMBRALES DE INCENDIO
# Modifica estos valores según tus necesidades
# ============================================
UMBRALES = {
    'temperatura': {
        'max': 35,          # Temperatura máxima antes de alerta (°C)
        'warning': 30       # Temperatura de advertencia (°C)
    },
    'humedad': {
        'min': 30,          # Humedad mínima antes de alerta (%)
        'warning': 40       # Humedad de advertencia (%)
    },
    'luminosidad': {
        'max': 900,         # Luminosidad máxima antes de alerta (Lux)
        'warning': 750      # Luminosidad de advertencia (Lux)
    }
}

# Configuración de carpetas
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp3', 'wav', 'ogg', 'm4a'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB máximo

# Almacenamiento en memoria de datos de sensores
sensor_data = {
    'temperatura': [],
    'humedad': [],
    'luminosidad': []
}

MAX_POINTS = 60  # Últimos 60 segundos de datos

# URL del servidor de cámara simulada
CAMARA_URL = 'http://localhost:5002/api/capturar'

# Control para no pedir imagen múltiples veces seguidas
# COOLDOWN: tiempo mínimo entre capturas (en segundos)
CAMARA_COOLDOWN = 120  # 2 minutos
ultima_alerta_imagen = None
solicitando_imagen = False


def verificar_alerta(temperatura, humedad, luminosidad):
    """Verifica si hay condiciones de alerta"""
    alertas = []
    if temperatura >= UMBRALES['temperatura']['max']:
        alertas.append(f'🌡️ Temperatura ALTA: {temperatura:.1f}°C')
    if humedad <= UMBRALES['humedad']['min']:
        alertas.append(f'💧 Humedad BAJA: {humedad:.1f}%')
    if luminosidad >= UMBRALES['luminosidad']['max']:
        alertas.append(f'💡 Luminosidad ALTA: {luminosidad:.0f} Lux')
    return alertas


def solicitar_imagen_camara():
    """Solicita imagen y audio al servidor de cámara en un thread separado"""
    global solicitando_imagen, ultima_alerta_imagen
    
    try:
        print("📷🎤 Solicitando captura a la cámara/micrófono...")
        response = requests.post(CAMARA_URL, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            imagen_data = data.get('imagen')
            audio_data = data.get('audio')
            
            if imagen_data:
                print(f"✅ Imagen recibida: {imagen_data.get('nombre')}")
            if audio_data:
                print(f"✅ Audio recibido: {audio_data.get('nombre')}")
            
            # Emitir imagen y audio al frontend via WebSocket
            socketio.emit('alerta_captura', {
                'imagen': {
                    'nombre': imagen_data.get('nombre') if imagen_data else None,
                    'data_url': imagen_data.get('data_url') if imagen_data else None
                },
                'audio': {
                    'nombre': audio_data.get('nombre') if audio_data else None,
                    'data_url': audio_data.get('data_url') if audio_data else None
                },
                'timestamp': datetime.now().isoformat()
            })
            
            ultima_alerta_imagen = datetime.now()
        else:
            print(f"❌ Error obteniendo captura: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("⚠️ Cámara/micrófono no disponible (servidor no está corriendo)")
    except Exception as e:
        print(f"❌ Error solicitando captura: {e}")
    finally:
        solicitando_imagen = False


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/health', methods=['GET'])
def health():
    """Verificar que la API está funcionando"""
    return jsonify({
        'status': 'ok',
        'mensaje': 'API IoT funcionando correctamente',
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/api/umbrales', methods=['GET'])
def obtener_umbrales():
    """Obtener los umbrales configurados en el servidor"""
    return jsonify(UMBRALES), 200


@app.route('/api/sensores', methods=['POST'])
def recibir_sensores():
    """
    Recibir datos de sensores
    JSON esperado:
    {
        "temperatura": 25.5,
        "humedad": 60.2,
        "luminosidad": 800
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No se envió JSON'}), 400
        
        temperatura = data.get('temperatura')
        humedad = data.get('humedad')
        luminosidad = data.get('luminosidad')
        
        if temperatura is None or humedad is None or luminosidad is None:
            return jsonify({'error': 'Faltan datos de sensores'}), 400
        
        # Agregar timestamp
        timestamp = datetime.now().isoformat()
        
        # Almacenar datos
        sensor_data['temperatura'].append({
            'valor': temperatura,
            'timestamp': timestamp
        })
        sensor_data['humedad'].append({
            'valor': humedad,
            'timestamp': timestamp
        })
        sensor_data['luminosidad'].append({
            'valor': luminosidad,
            'timestamp': timestamp
        })
        
        # Mantener solo los últimos MAX_POINTS
        for key in sensor_data:
            if len(sensor_data[key]) > MAX_POINTS:
                sensor_data[key] = sensor_data[key][-MAX_POINTS:]
        
        # Emitir en tiempo real a los clientes conectados
        socketio.emit('datos_sensores', {
            'temperatura': temperatura,
            'humedad': humedad,
            'luminosidad': luminosidad,
            'timestamp': timestamp
        })
        
        # Verificar si hay alerta y solicitar imagen
        global solicitando_imagen, ultima_alerta_imagen
        alertas = verificar_alerta(temperatura, humedad, luminosidad)
        
        # Solo pedir imagen cuando hay 3 alertas (ALERTA DE INCENDIO)
        if len(alertas) >= 3 and not solicitando_imagen:
            # Solo pedir imagen si no se pidió en los últimos CAMARA_COOLDOWN segundos
            ahora = datetime.now()
            if ultima_alerta_imagen is None or (ahora - ultima_alerta_imagen).seconds >= CAMARA_COOLDOWN:
                print(f"🔥 ¡ALERTA DE INCENDIO! Solicitando captura de cámara... (próxima en {CAMARA_COOLDOWN}s)")
                solicitando_imagen = True
                # Ejecutar en thread separado para no bloquear
                thread = threading.Thread(target=solicitar_imagen_camara)
                thread.start()
        
        return jsonify({
            'status': 'ok',
            'mensaje': 'Datos recibidos correctamente',
            'datos': {
                'temperatura': temperatura,
                'humedad': humedad,
                'luminosidad': luminosidad
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sensores', methods=['GET'])
def obtener_sensores():
    """Obtener histórico de datos de sensores"""
    return jsonify({
        'datos': sensor_data,
        'total_puntos': {
            'temperatura': len(sensor_data['temperatura']),
            'humedad': len(sensor_data['humedad']),
            'luminosidad': len(sensor_data['luminosidad'])
        }
    }), 200


@app.route('/api/sensores/limpiar', methods=['DELETE'])
def limpiar_sensores():
    """Limpiar histórico de datos"""
    global sensor_data
    sensor_data = {
        'temperatura': [],
        'humedad': [],
        'luminosidad': []
    }
    return jsonify({
        'status': 'ok',
        'mensaje': 'Datos limpiados correctamente'
    }), 200


@app.route('/api/archivo/subir', methods=['POST'])
def subir_archivo():
    """
    Subir foto o archivo de audio
    Usar multipart/form-data con campo 'file'
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No se envió archivo'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Archivo vacío'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': f'Tipo de archivo no permitido. Permitidos: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        return jsonify({
            'status': 'ok',
            'mensaje': 'Archivo subido correctamente',
            'archivo': filename,
            'url': f'/api/archivo/descargar/{filename}'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/archivo/descargar/<filename>', methods=['GET'])
def descargar_archivo(filename):
    """Descargar o visualizar archivo subido"""
    try:
        filename = secure_filename(filename)
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        return jsonify({'error': 'Archivo no encontrado'}), 404


@app.route('/api/archivos/listar', methods=['GET'])
def listar_archivos():
    """Listar todos los archivos subidos"""
    try:
        files = os.listdir(app.config['UPLOAD_FOLDER'])
        return jsonify({
            'total': len(files),
            'archivos': files
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/archivos/eliminar/<filename>', methods=['DELETE'])
def eliminar_archivo(filename):
    """Eliminar archivo subido"""
    try:
        filename = secure_filename(filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({
                'status': 'ok',
                'mensaje': f'Archivo {filename} eliminado correctamente'
            }), 200
        else:
            return jsonify({'error': 'Archivo no encontrado'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# WebSocket para actualizaciones en tiempo real
@socketio.on('connect')
def handle_connect():
    print('Cliente conectado')
    emit('respuesta', {'data': 'Conectado al servidor'})


@socketio.on('disconnect')
def handle_disconnect():
    print('Cliente desconectado')


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)
