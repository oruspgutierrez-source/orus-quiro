import requests
import time

url = "http://127.0.0.1:8000/webhook"

def make_payload(text):
    return {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "12345",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "123", "phone_number_id": "123"},
                    "contacts": [{"profile": {"name": "Test User"}, "wa_id": "111222333"}],
                    "messages": [{
                        "from": "111222333",
                        "id": "wamid.123",
                        "timestamp": "123456",
                        "text": {"body": text},
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }

messages = [
    "Hola, llevo esperando mucho tiempo.",
    "¡Esto es una estafa, no me responden nada!",
    "Quiero hablar con una persona real ya mismo."
]

print("Enviando ráfaga de mensajes simulados...")
for idx, msg in enumerate(messages):
    start = time.time()
    response = requests.post(url, json=make_payload(msg))
    end = time.time()
    print(f"Mensaje {idx+1} '{msg}' enviado. Respuesta: {response.status_code} Tiempo: {end-start:.4f}s")
    time.sleep(1) # Simular 1 seg de tecleo

print("Ráfaga completada. Esperando 10 segundos para ver si el Orquestador agrupa y responde...")
