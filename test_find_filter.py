import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("EVOLUTION_API_URL")
INSTANCE = os.getenv("EVOLUTION_INSTANCE_NAME")
API_KEY = os.getenv("EVOLUTION_API_KEY")

async def test_find_with_filter():
    endpoint = f"{API_URL}/chat/findContacts/{INSTANCE}"
    
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "where": {
            "pushName": "orus peña"
        }
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(endpoint, json=payload, headers=headers) as response:
                data = await response.json()
                print(f"Total encontrados: {len(data)}")
                for c in data:
                    print(c)
        except Exception as e:
            print(f"Error en solicitud: {e}")

if __name__ == "__main__":
    asyncio.run(test_find_with_filter())
