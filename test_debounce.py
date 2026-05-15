"""
Test de ráfaga de mensajes — Simula el escenario exacto del bug original.

Envía 6 mensajes rápidos al webhook local y verifica que el sistema
los agrupe en UNA SOLA llamada al procesador.

Uso: python test_debounce.py
Prerequisito: uvicorn main:app --port 8000 corriendo en otra terminal
"""

import asyncio
import httpx
import time

BASE_URL = "http://localhost:8000"

# Simula el payload exacto de Evolution API
def make_payload(sender: str, text: str, msg_id: str):
    return {
        "event": "messages.upsert",
        "data": {
            "key": {
                "remoteJid": sender,
                "fromMe": False,
                "id": msg_id
            },
            "message": {
                "conversation": text
            }
        }
    }


async def test_burst():
    """Envia 6 mensajes rapidos como si un usuario escribiera una rafaga."""
    sender = "5491100000000@s.whatsapp.net"
    messages = ["ola", "de nuevo", "estamos", "haciendo", "test", "contigo"]
    
    print("=" * 60)
    print("TEST DE RAFAGA - Debounce con asyncio.Task")
    print("=" * 60)
    print(f"Enviando {len(messages)} mensajes rapidos al webhook...\n")

    async with httpx.AsyncClient() as client:
        for i, text in enumerate(messages):
            msg_id = f"test_msg_{int(time.time())}_{i}"
            payload = make_payload(sender, text, msg_id)
            
            response = await client.post(f"{BASE_URL}/webhook", json=payload)
            print(f"  [{i+1}/{len(messages)}] '{text}' -> HTTP {response.status_code}")
            
            # Simular delay real entre mensajes (0.5-1 segundo)
            if i < len(messages) - 1:
                await asyncio.sleep(0.7)

    print(f"\n--- Todos los mensajes enviados ---")
    print(f"Ahora el sistema deberia esperar ~6 segundos de silencio")
    print(f"y luego procesar TODO junto en UNA sola llamada a Gemini.")
    print(f"\nRevisa los logs del servidor (uvicorn) para confirmar:")
    print(f"  - Deberia ver '[Buffer] ... +1 msg' 6 veces")
    print(f"  - Deberia ver '[Debounce] Timer cancelado' 5 veces")
    print(f"  - Deberia ver '[Processor] Procesando 6 msg(s)' UNA sola vez")
    print(f"\nEsperando 10 segundos para que el debounce termine...")
    await asyncio.sleep(10)
    print("Test completado.")


if __name__ == "__main__":
    asyncio.run(test_burst())
