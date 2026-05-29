import os
import sys
import requests
import urllib3
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

base_url = os.getenv("EVOLUTION_API_URL")
instance_name = os.getenv("EVOLUTION_INSTANCE_NAME")
api_key = os.getenv("EVOLUTION_API_KEY")

headers = {
    "apikey": api_key,
    "Content-Type": "application/json",
    "Host": "whatsapp.orusquiroterapia.online"
}

number = "553598869018"
payload = {
    "number": number,
    "text": "🤖 Hola! Este es un mensaje de prueba automática del sistema para verificar la salida de Evolution API."
}

url = f"{base_url}/message/sendText/{instance_name}"
print(f"Enviando mensaje de prueba a {number} via: {url}")

try:
    res = requests.post(url, json=payload, headers=headers, verify=False, timeout=10)
    print(f"Status Code: {res.status_code}")
    print("Respuesta:")
    print(res.text)
except Exception as e:
    print(f"Error enviando mensaje: {e}")
