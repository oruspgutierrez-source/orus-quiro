import requests
import json
import os
import time
from dotenv import load_dotenv
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main():
    print("=== AUTOMATIC WEBHOOK REGISTRATION ===")
    
    # 1. Obtener URL de ngrok de forma dinámica
    ngrok_api_url = "http://127.0.0.1:4040/api/tunnels"
    ngrok_url = None
    
    # Intentar hasta 5 veces por si ngrok tarda en levantar
    for i in range(5):
        try:
            res = requests.get(ngrok_api_url, timeout=3)
            data = res.json()
            if "tunnels" in data and len(data["tunnels"]) > 0:
                ngrok_url = data["tunnels"][0]["public_url"]
                break
        except Exception:
            pass
        print(f"Esperando que ngrok levante (intento {i+1}/5)...")
        time.sleep(2)
        
    if not ngrok_url:
        print("Error: No se pudo obtener la URL pública de ngrok. ¿Está corriendo ngrok?")
        return
        
    print(f"URL de ngrok detectada: {ngrok_url}")
    
    # 2. Cargar variables de entorno
    load_dotenv()
    base_url = os.getenv("EVOLUTION_API_URL")
    instance_name = os.getenv("EVOLUTION_INSTANCE_NAME")
    api_key = os.getenv("EVOLUTION_API_KEY")
    
    if not all([base_url, instance_name, api_key]):
        print("Error: Faltan variables de entorno en el archivo .env")
        return
        
    if ngrok_url.endswith("/"):
        ngrok_url = ngrok_url[:-1]
        
    full_webhook_url = f"{ngrok_url}/webhook"
    
    # 3. Payload de registro
    payload = {
        "webhook": {
            "enabled": True,
            "url": full_webhook_url,
            "byEvents": False,
            "base64": False,
            "events": [
                "MESSAGES_UPSERT"
            ]
        }
    }
    
    headers = {
        "apikey": api_key,
        "Content-Type": "application/json",
        "Host": "whatsapp.orusquiroterapia.online"
    }
    
    print(f"Registrando webhook en Evolution API: {full_webhook_url} ...")
    try:
        response = requests.post(f"{base_url}/webhook/set/{instance_name}", headers=headers, json=payload, timeout=10, verify=False)
        print("Respuesta de Evolution API:")
        print(json.dumps(response.json(), indent=2))
        print("\n¡Webhook configurado automáticamente de forma exitosa!")
    except Exception as e:
        print(f"Error registrando el webhook: {e}")

if __name__ == "__main__":
    main()
