from ultralytics import YOLO
import cv2
import os
from datetime import datetime

# Ruta absoluta al directorio actual (DeteccionImagen/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ruta absoluta al modelo
MODEL_PATH = os.path.join(BASE_DIR, "models", "yolov8s_best.pt")

# Cargar modelo UNA SOLA VEZ
_model = YOLO(MODEL_PATH)

def detect_fire(
    image_path: str,
    resize_width: int = 800,
    resize_height: int = 600,
    conf_threshold: float = 0.25
):
    """
    Detecta fuego en una imagen.

    Returns:
        False
        OR
        (True, output_image_path, best_confidence)
    """

    frame = cv2.imread(image_path)
    frame = cv2.resize(frame, (resize_width, resize_height))

    results = _model(frame, conf=conf_threshold, verbose=False)
    result = results[0]

    # No hay detecciones
    if result.boxes is None or len(result.boxes) == 0:
        return False

    # Mejor deteccion
    best_box = max(result.boxes, key=lambda b: float(b.conf[0]))
    best_conf = round(float(best_box.conf[0]), 2)

    x1, y1, x2, y2 = map(int, best_box.xyxy[0])

    annotated_frame = frame.copy()
    cv2.rectangle(
        annotated_frame, (x1, y1), (x2, y2),
        (0, 0, 255), 2
    )

    label = f"Fire {best_conf}"
    cv2.putText(
        annotated_frame, label,
        (x1, max(y1 - 10, 20)),
        cv2.FONT_HERSHEY_SIMPLEX, 0.6,
        (0, 0, 255), 2
    )

    output_dir = "predicts_yolov8/images"
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"predict_{timestamp}.jpg")
    cv2.imwrite(output_path, annotated_frame)

    return True, output_path, best_conf
