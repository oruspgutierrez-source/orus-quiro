import asyncio
import httpx
import time
import uuid
import subprocess
import os

async def send_whatsapp_message(message_text: str, step_name: str):
    print(f"\n[{step_name}] Enviando mensaje: '{message_text}'")
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
        print(f"[{step_name}] Respuesta webhook HTTP {res.status_code}")
    
    # Wait for debounce (10s) + LLM processing (5-10s) + extra buffer
    wait_time = 25
    print(f"[{step_name}] Esperando {wait_time}s a que se procese y responda...")
    await asyncio.sleep(wait_time)

async def main():
    print("=== INICIANDO SIMULACIÓN E2E DE ORUS QUIRO ===")
    
    # Paso 1: Saludo inicial (Acogida)
    await send_whatsapp_message("hola", "Paso 1: Saludo inicial")
    
    # Paso 2: Usuario muestra interés en saber más (Fase 2 - Despacho Audio)
    await send_whatsapp_message("si, estoy listo para iniciar el proceso", "Paso 2: Interés inicial")
    
    # Paso 3: Interés en comprar (Fase 3A - Detalles del servicio)
    await send_whatsapp_message("estoy interesado, que obtendre?", "Paso 3: Pregunta sobre servicio")
    
    # Paso 4: Intención explícita de compra (Fase 3B - Envío de Link de Pago)
    await send_whatsapp_message("quiero comprar el servicio", "Paso 4: Intención de compra")
    
    # Paso 5: Simular pago de Stripe
    print("\n[Paso 5: Pago Stripe] Simulando el webhook de pago de Stripe...")
    # Llamamos al script existente de simulación de pago
    result = subprocess.run(["python", "scratch/simulate_stripe_webhook.py"], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"Error en script de stripe: {result.stderr}")
    
    # Wait for invoice generation, sending PDF, and triggering Phase 4 proactively
    print("[Paso 5: Pago Stripe] Esperando 30s a que Orus procese el pago, envíe la factura y active el agendamiento...")
    await asyncio.sleep(30)
    
    # Paso 6: Selección de fecha (Fase 4 - Agendamiento: Elección)
    await send_whatsapp_message("quiero el jueves a las 9 am", "Paso 6: Seleccionar fecha")
    
    # Paso 7: Confirmación de datos (Fase 4 - Agendamiento: Datos)
    await send_whatsapp_message("Juan Perez, juan@gmail.com", "Paso 7: Envío de datos")
    
    # Paso 8: Confirmación final (Fase 4 - Agendamiento: Confirmación final)
    await send_whatsapp_message("si, los datos son correctos", "Paso 8: Confirmar cita")
    
    print("\n[Paso 9: Cierre E2E] Esperando 45s a que Orus complete la cita, envíe las 3 imágenes visuales, el link de Calendar y el enlace a la WebApp de biometría...")
    await asyncio.sleep(45)
    
    print("=== SIMULACIÓN E2E COMPLETADA ===")

if __name__ == "__main__":
    asyncio.run(main())
