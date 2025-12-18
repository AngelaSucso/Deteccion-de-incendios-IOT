from detector import detect_fire

image_path = "C:/Users/OWEN ROQUE/Downloads/fire_test.jpg"

result = detect_fire(image_path)

if result is False:
    print("No se detectó fuego")
    # logica...
else:
    detected, image_path, confidence = result
    print("Fuego detectado")
    print("Imagen:", image_path)
    print("Confidence:", confidence)

    if confidence >= 0.8:
        print("ALERTA CRÍTICA")
