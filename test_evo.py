import os
import sys
import asyncio
import aiohttp
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

API_URL = os.getenv("EVOLUTION_API_URL")
INSTANCE = os.getenv("EVOLUTION_INSTANCE_NAME")
API_KEY = os.getenv("EVOLUTION_API_KEY")

async def test_number(number, label):
    print(f"\n--- Probando {label}: {number} ---")
    endpoint = f"{API_URL}/message/sendText/{INSTANCE}"
    
    payload = {
        "number": number,
        "text": f"✅ Test automático de conexión para formato: {label}"
    }
    
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(endpoint, json=payload, headers=headers) as response:
                data = await response.json()
                print(f"Status HTTP: {response.status}")
                print(f"Respuesta API: {data}")
        except Exception as e:
            print(f"Error en solicitud: {e}")

async def main():
    print(f"Configuración cargada:\nURL: {API_URL}\nInstance: {INSTANCE}\n")
    
    # Pruebas con diferentes formatos del número de Brasil
    
    # 1. Sin el 9 (Como llega en el webhook localmente)
    await test_number("553798433269", "Sin noveno dígito (Crudo)")
    
    # 2. Con el 9 (El formato móvil estándar brasileño actual)
    await test_number("5537998433269", "Con noveno dígito")
    
    # 3. Con @s.whatsapp.net (Para forzar a la API)
    await test_number("5537998433269@s.whatsapp.net", "Con sufijo JID")

if __name__ == "__main__":
    asyncio.run(main())
