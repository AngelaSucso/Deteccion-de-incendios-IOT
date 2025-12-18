
# cSpell:disable

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from datetime import datetime



app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Umbrales globales
UMBRALES = {
    'temperatura': {'max': 45},
    'humedad': {'min': 20},
    'luminosidad': {'max': 2000}
}

# Historial de sensores (máx 60)
MAX_HISTORIAL = 60
historial_sensores = []

# Variables para almacenar los últimos datos
ultimo_sensores = None
ultimo_estado = None
ultimo_imagen = None
ultimo_audio = None

# Endpoint de salud
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'mensaje': 'API IoT funcionando correctamente',
        'timestamp': datetime.now().isoformat()
    }), 200

# Endpoint para obtener umbrales
@app.route('/api/umbrales', methods=['GET'])
def obtener_umbrales():
    return jsonify(UMBRALES), 200

# Endpoint para recibir datos de sensores
@app.route('/api/sensores', methods=['POST'])
def recibir_sensores():
    global ultimo_sensores, historial_sensores
    data = request.get_json()
    ultimo_sensores = {
        'temperatura': data.get('temperatura'),
        'humedad': data.get('humedad'),
        'luminosidad': data.get('luminosidad'),
        'timestamp': datetime.now().isoformat()
    }
    # Guardar en historial
    historial_sensores.append(ultimo_sensores)
    if len(historial_sensores) > MAX_HISTORIAL:
        historial_sensores = historial_sensores[-MAX_HISTORIAL:]
    # Emitir datos de sensores al frontend
    socketio.emit('datos_sensores', ultimo_sensores)
    return jsonify({'status': 'ok', 'mensaje': 'Datos recibidos', 'datos': ultimo_sensores}), 201

# Endpoint para obtener historial de sensores
@app.route('/api/sensores', methods=['GET'])
def obtener_historial_sensores():
    return jsonify({'historial': historial_sensores}), 200

# Endpoint para recibir estado
@app.route('/api/estado', methods=['POST'])
def recibir_estado():
    global ultimo_estado
    data = request.get_json()
    ultimo_estado = {
        'estado': data.get('estado'),
        'timestamp': datetime.now().isoformat()
    }
    # Emitir estado al frontend
    socketio.emit('estado', ultimo_estado)
    return jsonify({'status': 'ok', 'mensaje': 'Estado recibido', 'datos': ultimo_estado}), 201


# Endpoint para recibir imagen
@app.route('/api/imagen', methods=['POST'])
def recibir_imagen():
    global ultimo_imagen
    data = request.get_json()
    ultimo_imagen = {
        'nombre': data.get('nombre'),
        'data_url': data.get('data_url'),
        'timestamp': datetime.now().isoformat()
    }
    # Emitir evidencia al frontend si también hay audio
    if ultimo_audio:
        socketio.emit('alerta_captura', {
            'imagen': ultimo_imagen,
            'audio': ultimo_audio,
            'timestamp': ultimo_imagen['timestamp']
        })
    else:
        socketio.emit('alerta_captura', {
            'imagen': ultimo_imagen,
            'audio': None,
            'timestamp': ultimo_imagen['timestamp']
        })
    return jsonify({'status': 'ok', 'mensaje': 'Imagen recibida', 'datos': ultimo_imagen}), 201


# Endpoint para recibir audio
@app.route('/api/audio', methods=['POST'])
def recibir_audio():
    global ultimo_audio
    data = request.get_json()
    ultimo_audio = {
        'nombre': data.get('nombre'),
        'data_url': data.get('data_url'),
        'timestamp': datetime.now().isoformat()
    }
    # Emitir evidencia al frontend si también hay imagen
    if ultimo_imagen:
        socketio.emit('alerta_captura', {
            'imagen': ultimo_imagen,
            'audio': ultimo_audio,
            'timestamp': ultimo_audio['timestamp']
        })
    else:
        socketio.emit('alerta_captura', {
            'imagen': None,
            'audio': ultimo_audio,
            'timestamp': ultimo_audio['timestamp']
        })
    return jsonify({'status': 'ok', 'mensaje': 'Audio recibido', 'datos': ultimo_audio}), 201

# Endpoint para obtener los últimos datos
@app.route('/api/ultimos', methods=['GET'])
def obtener_ultimos():
    return jsonify({
        'sensores': ultimo_sensores,
        'estado': ultimo_estado,
        'imagen': ultimo_imagen,
        'audio': ultimo_audio
    }), 200

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)
