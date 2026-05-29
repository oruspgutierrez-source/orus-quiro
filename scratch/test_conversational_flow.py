import requests
import json
import time

def simulate_message(text: str):
    print(f"\n--- SIMULANDO MENSAJE ENTRANTE: '{text}' ---")
    
    # Payload simulado de Evolution API v2 para mensajes de texto
    payload = {
        "event": "messages.upsert",
        "instance": "OrusBot",
        "data": {
            "key": {
                "remoteJid": "37598781259882@lid",
                "fromMe": False,
                "id": f"TEST_MSG_{int(time.time())}"
            },
            "pushName": "Mario Pacnaca",
            "message": {
                "conversation": text
            },
            "messageType": "conversation"
        }
    }
    
    url = "http://localhost:8000/webhook"
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=15)
        print(f"Respuesta del webhook: HTTP {res.status_code}")
        print(f"Cuerpo: {res.text}")
    except Exception as e:
        print(f"Error enviando mensaje: {e}")

if __name__ == "__main__":
    # Simular una consulta ordinaria de precio
    simulate_message("Quiero saber el precio de la lectura")
    
    # Esperar a que el message processor local de asyncio termine de debouncar y procesar (espera de 10s debounce + inferencia)
    print("Esperando 15 segundos para que finalice el debounce y la llamada a Gemini...")
    time.sleep(15)
    
    # Simular intención de compra
    simulate_message("Quiero comprar una lectura")
