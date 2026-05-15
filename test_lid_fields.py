import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("EVOLUTION_API_URL")
INSTANCE = os.getenv("EVOLUTION_INSTANCE_NAME")
API_KEY = os.getenv("EVOLUTION_API_KEY")

async def test_lid_fields():
    endpoint = f"{API_URL}/message/sendText/{INSTANCE}"
    
    payloads = [
        {"jid": "37598781259882@lid", "text": "Testing jid parameter"},
        {"number": "37598781259882@lid", "text": "Testing number parameter with check=false", "checkNumber": False},
        {"number": "37598781259882@lid", "text": "Testing number parameter with options", "options": {"verifyNumber": False}},
    ]
    
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        for payload in payloads:
            print(f"\nProbando: {payload}")
            try:
                async with session.post(endpoint, json=payload, headers=headers) as response:
                    data = await response.json()
                    print(f"Status HTTP: {response.status}")
                    print(f"Respuesta API: {data}")
            except Exception as e:
                print(f"Error en solicitud: {e}")

if __name__ == "__main__":
    asyncio.run(test_lid_fields())
