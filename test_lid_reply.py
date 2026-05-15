import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("EVOLUTION_API_URL")
INSTANCE = os.getenv("EVOLUTION_INSTANCE_NAME")
API_KEY = os.getenv("EVOLUTION_API_KEY")

async def test_lid_reply():
    endpoint = f"{API_URL}/message/sendText/{INSTANCE}"
    
    # Payload real de la prueba
    payload = {
        "number": "37598781259882@lid",
        "text": "Respuesta probando quoted message",
        "options": {
            "quoted": {
                "key": {
                    "id": "ACBCDC0A8C21261E384F30ED302A8428",
                    "fromMe": False,
                    "remoteJid": "37598781259882@lid"
                },
                "message": {
                    "conversation": "Que significa el monte"
                }
            }
        }
    }
    
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json"
    }
    
    print(f"Probando: {payload}")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(endpoint, json=payload, headers=headers) as response:
                data = await response.json()
                print(f"Status HTTP: {response.status}")
                print(f"Respuesta API: {data}")
        except Exception as e:
            print(f"Error en solicitud: {e}")

if __name__ == "__main__":
    asyncio.run(test_lid_reply())
