# Deteccion-de-incendios-IOT
---

<!-- TABLA DE CONTENIDOS -->
<!-- TABLA DE CONTENIDOS -->
<details>
  <summary>Tabla de Contenidos</summary>
  <ol>
    <li>
      <a href="#1-acerca-del-proyecto">1. Acerca del Proyecto</a>
      <ol>
        <li><a href="#11-descripcion-general-del-sistema">1.1 Descripción General del Sistema</a></li>
        <li><a href="#12-arquitectura-del-sistema">1.2 Arquitectura del Sistema</a></li>
        <li><a href="#13-tecnologias-utilizadas">1.3 Tecnologías Utilizadas</a></li>
      </ol>
    </li>
    <li>
      <a href="#2-primeros-pasos">2. Primeros Pasos</a>
      <ol>
        <li><a href="#21-requisitos-previos">2.1 Requisitos Previos</a></li>
        <li><a href="#22-instalacion">2.2 Instalación</a></li>
      </ol>
    </li>
    <li>
      <a href="#3-uso-del-sistema">3. Uso del Sistema</a>
      <ol>
        <li><a href="#31-estado-de-monitoreo-normal">3.1 Estado de Monitoreo Normal</a></li>
        <li><a href="#32-estado-de-deteccion-de-riesgo">3.2 Estado de Detección de Riesgo</a></li>
        <li><a href="#33-captura-multimedia">3.3 Captura Multimedia</a></li>
        <li><a href="#34-confirmacion-de-incendio">3.4 Confirmación de Incendio</a></li>
        <li><a href="#35-envio-de-alertas">3.5 Envío de Alertas</a></li>
      </ol>
    </li>
    <li><a href="#4-hoja-de-ruta">4. Hoja de Ruta</a></li>
    <li><a href="#5-contribuciones">5. Contribuciones</a></li>
    <li><a href="#6-licencia">6. Licencia</a></li>
    <li><a href="#7-contacto">7. Contacto</a></li>
    <li><a href="#8-agradecimientos">8. Agradecimientos</a></li>
  </ol>
</details>


## 1. Acerca del Proyecto
### 1.1 Descripción General del Sistema
### 1.2 Arquitectura del Sistema
### 1.3 Tecnologías Utilizadas
  **Lenguaje de programación**
  - **Python**: lenguaje principal del sistema, utilizado para el backend, procesamiento de datos y scripts de análisis.

  **Backend y servidor**
  - **Flask**: framework web para el servidor backend.
  - **Flask-SocketIO**: comunicación en tiempo real con el dashboard.
  - **Flask-CORS**: gestión de políticas CORS.
  - **Werkzeug**: utilidades internas del servidor.

  **Frontend y visualización**
  - **HTML / CSS**: interfaz web estática ubicada en la carpeta `front-end`.
  - **Streamlit**: interfaz gráfica para la detección de incendios por imagen (módulo `DeteccionImagen`).

  **Detección de incendios por imagen (Visión por Computadora)**
  - **Ultralytics YOLOv8** (`ultralytics`): modelo de detección de fuego.
  - **Modelo entrenado**: `models/yolov8s_best.pt`.
  - **OpenCV** (`opencv-python`): procesamiento de imágenes y video.
  - **Pillow**: carga y manipulación de imágenes.

  **Detección de incendios por audio (Aprendizaje Automático)**
  - **Librosa**: extracción de características de audio.
  - **NumPy**: procesamiento numérico.
  - **scikit-learn**: modelo basado en **Random Forest** para clasificación de sonidos.
  - Scripts ubicados en el módulo `DeteccionAudio`.

  **Análisis de datos y visualización**
  - **pandas**: manipulación y análisis de datos.
  - **plotly**: visualización interactiva de resultados.

  **Integración y utilidades**
  - **python-dotenv**: gestión de variables de entorno.
  - **python-engineio**: soporte para comunicación en tiempo real.

  **Telemetría y notificaciones**
  - **Telegram Bot API**: envío de alertas automáticas al usuario.
  - Implementación en el archivo `telegram_message.py`.

  **Soporte de audio**
  - **soundfile** (`libsndfile`): lectura y escritura de archivos de audio.
  - Dependencias adicionales requeridas por **librosa**.

  **Video y fuentes externas**
  - **pytube**: descarga de videos desde YouTube para pruebas (módulo `DeteccionImagen`).

  **IoT y hardware**
  - **Arduino MKR1010 WiFi** con **IoT Carrier**.
  - Código del microcontrolador ubicado en `scriptArduino/sensoresIncendio.ino`.

  **Estructura del proyecto**
  - **Backend**: `backend/app.py`.
  - **Frontend estático**: `front-end/index.html`.
  - **Datasets**: carpetas `dataset/` y `DeteccionImagen/datasets`.

## 2. Primeros Pasos
### 2.1 Requisitos Previos
- **Python** 3.10+ instalado.
- **pip** y herramienta de entornos virtuales (`venv` o `virtualenv`).
- **Git** (para clonar el repositorio).
- **Dependencias del sistema** para audio/video: `libsndfile` (para `soundfile`/`librosa`) y `ffmpeg` (opcional, para manejo de video). En Windows puede requerirse instalar Visual C++ Build Tools.
- **Opcional (GPU)**: drivers CUDA y versión de PyTorch compatible si se desea acelerar la detección por imagen.
- **Arduino IDE** para programar el sketch `scriptArduino/sensoresIncendio.ino`.
- Cámara IP o webcam para pruebas de video (si aplica).
- Variables de entorno para integraciones (p. ej. token de Telegram).

### 2.2 Instalación
1. Clonar el repositorio:
```bash
git clone <repo-url>
cd Deteccion-de-incendios-IOT
```

2. Crear y activar un entorno virtual (Windows):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1   # PowerShell
# o
.venv\Scripts\activate.bat   # CMD
```

3. Actualizar `pip` e instalar dependencias principales:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r DeteccionImagen/requirements.txt
```

4. (Opcional) Instalar dependencias del sistema para audio/video:
- Windows: instalar `libsndfile`/paquetes redistribuibles según la guía de cada librería.
- Linux/macOS: usar `apt`, `brew` o el gestor correspondiente (`libsndfile`, `ffmpeg`).

5. Configurar variables de entorno (archivo `.env` recomendado). Ejemplo mínimo:
```
TELEGRAM_TOKEN=xxxxx
TELEGRAM_CHAT_ID=yyyyy
MQTT_BROKER=broker.example.com
MQTT_PORT=1883
```

6. Ejecutar componentes:
- Backend / monitor (desde la raíz — si usas el script principal):
```bash
python main.py
```
- Interfaz de detección por imagen (Streamlit):
```bash
streamlit run DeteccionImagen/main.py
```
- Entrenamiento o pruebas de audio:
```bash
python DeteccionAudio/entrenar_modelo.py
```
- Subir código al Arduino: abrir `scriptArduino/sensoresIncendio.ino` en el Arduino IDE y cargar al dispositivo.

7. Notas:
- Para detección de imágenes con GPU, instala la versión de `torch` compatible con tu CUDA y reinicia.
- Al usar IP Webcam app, actualiza la URL/credenciales en la configuración correspondiente.

## 3. Uso del Sistema
### 3.1 Estado de Monitoreo Normal
### 3.2 Estado de Detección de Riesgo
### 3.3 Captura Multimedia
### 3.4 Confirmación de Incendio
### 3.5 Envío de Alertas

## 4. Hoja de Ruta
## 5. Contribuciones
## 6. Licencia
## 7. Contacto
## 8. Agradecimientos



### ⚙️ Funcionamiento
1. El sistema se suscribe a un tópico MQTT y recibe datos en formato JSON.
2. Se evalúan los valores de temperatura, humedad y luz según umbrales definidos.
3. Si las condiciones de riesgo se mantienen durante varias lecturas consecutivas, se confirma la alerta.
4. Ante una alerta confirmada:
   - Se detecta el riesgo de incendio.
   - Se analiza la humedad ambiental.
   - Se captura una imagen desde la cámara IP.

     <img src="images/ipwebcam.jpeg" width="400">

   - Se graba un archivo de audio.
5. El sistema evita alertas repetidas hasta que las condiciones vuelvan a la normalidad.

---

### Datos esperados (MQTT)
El sistema espera mensajes en formato JSON con la siguiente estructura:

```json

{
  "temp": 45,
  "hum": 18,
  "luz": 2300
}