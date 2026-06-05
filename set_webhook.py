import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

base_url = os.getenv("EVOLUTION_API_URL")
instance_name = os.getenv("EVOLUTION_INSTANCE_NAME")
api_key = os.getenv("EVOLUTION_API_KEY")

if not all([base_url, instance_name, api_key]):
    print("Faltan variables de entorno en .env")
    exit(1)

# Pide la URL de ngrok al usuario
print("\n=== REGISTRO DE WEBHOOK ===")
ngrok_url = input("Ingresa la URL raiz de tu ngrok (ej. https://abcdef.ngrok.app): ").strip()

if ngrok_url.endswith("/"):
    ngrok_url = ngrok_url[:-1]

full_webhook_url = f"{ngrok_url}/webhook"

payload = {
    "webhook": {
        "enabled": True,
        "url": full_webhook_url,
        "byEvents": False,
        "base64": True,
        "events": [
            "MESSAGES_UPSERT"
        ]
    }
}

headers = {
    "apikey": api_key,
    "Content-Type": "application/json"
}

print(f"\nRegistrando webhook: {full_webhook_url} ...")
res = requests.post(f"{base_url}/webhook/set/{instance_name}", headers=headers, json=payload)

try:
    print(json.dumps(res.json(), indent=2))
    print("\n¡Webhook configurado correctamente! Si ngrok está corriendo en el puerto 8000 y FastAPI está encendido, ya deberías poder recibir mensajes.")
except Exception as e:
    print(f"Error parseando respuesta: {res.text}")
