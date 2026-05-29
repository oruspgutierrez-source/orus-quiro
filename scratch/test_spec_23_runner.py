import asyncio
import httpx
import time
import uuid

async def test_webhook(message_text: str, test_name: str):
    print(f"\n--- Iniciando {test_name} ---")
    url = "http://localhost:8000/webhook"
    
    mock_id = str(uuid.uuid4())
    payload = {
        "event": "messages.upsert",
        "instance": "Orus",
        "data": {
            "key": {
                "remoteJid": "553598869018@s.whatsapp.net",
                "fromMe": False,
                "id": mock_id
            },
            "messageType": "conversation",
            "message": {
                "conversation": message_text
            }
        }
    }
    
    async with httpx.AsyncClient() as client:
        res = await client.post(url, json=payload, timeout=20.0)
        print(f"[{test_name}] Webhook aceptado HTTP {res.status_code}")
    
    print(f"[{test_name}] Esperando 25 segundos para que procese el debounce y LLM...")
    await asyncio.sleep(25)
    print(f"--- Fin {test_name} ---\n")

async def main():
    # Prueba 1: Fase 2 (Despacho de Audio)
    # Requisito: Enviar "si" a la pregunta de acogida
    # Pero para estar en acogida, necesitamos que empiece de cero, o asumimos que "si" activa algo.
    # Dado que "si" podría no ser contexto suficiente si no ha recibido la bienvenida, 
    # enviemos "hola" primero, esperamos, y luego "si".
    
    await test_webhook("hola", "Prueba 0: Hola (Acogida)")
    
    await test_webhook("si, me gustaria", "Prueba 1: Fase 2 (Audio)")
    
    await test_webhook("quiero iniciar mi proceso", "Prueba 2: Fase 3B (Cobro)")

if __name__ == "__main__":
    asyncio.run(main())
