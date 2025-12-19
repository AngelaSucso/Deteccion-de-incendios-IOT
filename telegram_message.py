import requests

TOKEN = "8510166570:AAHLXgXM0_EUQAneW-XLSnQHdCeyMYYN0KQ"
CHAT_ID = "8532744967"
MENSAJE = "¡Alerta! Incendio detectado 🔥"
foto_path = "foto_incendio.jpg"

def enviar_alerta_telegram(foto_path):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"

    with open(foto_path, "rb") as foto:
        files = {"photo": foto}
        data = {
            "chat_id": CHAT_ID,
            "caption": MENSAJE
        }
        
        # Enviar la foto con el mensaje
        response = requests.post(url, files=files, data=data)

    # Verifica si el mensaje fue enviado correctamente
    if response.status_code == 200:
        print("Foto enviada correctamente")
    else:
        print(f"Error al enviar la foto: {response.text}")