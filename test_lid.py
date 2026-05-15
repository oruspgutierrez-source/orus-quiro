import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("EVOLUTION_API_URL")
INSTANCE = os.getenv("EVOLUTION_INSTANCE_NAME")
API_KEY = os.getenv("EVOLUTION_API_KEY")

async def test_lid(number, check_number):
    endpoint = f"{API_URL}/message/sendText/{INSTANCE}"
    
    payload = {
        "number": number,
        "text": f"Test lid con checkNumber={check_number}",
        "options": {
            "checkNumber": check_number
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

async def main():
    await test_lid("37598781259882@lid", False)
    await test_lid("37598781259882@lid", True)

if __name__ == "__main__":
    asyncio.run(main())
