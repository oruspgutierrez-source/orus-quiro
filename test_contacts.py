import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("EVOLUTION_API_URL")
INSTANCE = os.getenv("EVOLUTION_INSTANCE_NAME")
API_KEY = os.getenv("EVOLUTION_API_KEY")

async def get_contacts():
    endpoint = f"{API_URL}/chat/findContacts/{INSTANCE}"
    
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json"
    }
    
    print(f"Buscando contactos...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(endpoint, json={"where": {}}, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"Total contactos: {len(data)}")
                    for c in data:
                        if "orus peña" in str(c).lower() or "37598781259882" in str(c):
                            print(f"Encontrado: {c}")
                else:
                    print(f"Status HTTP: {response.status}")
                    print(await response.text())
        except Exception as e:
            print(f"Error en solicitud: {e}")

if __name__ == "__main__":
    asyncio.run(get_contacts())
