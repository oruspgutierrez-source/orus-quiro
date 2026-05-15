import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("EVOLUTION_API_URL")
INSTANCE = os.getenv("EVOLUTION_INSTANCE_NAME")
API_KEY = os.getenv("EVOLUTION_API_KEY")

async def logout_instance():
    endpoint = f"{API_URL}/instance/logout/{INSTANCE}"
    headers = {"apikey": API_KEY}
    
    print(f"Cerrando sesión de la instancia {INSTANCE}...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.delete(endpoint, headers=headers) as response:
                if response.status in (200, 201):
                    print("✅ Sesión cerrada exitosamente. Revisa el Evolution Manager para escanear el QR.")
                else:
                    data = await response.text()
                    print(f"⚠️ Error al cerrar sesión: {response.status} - {data}")
        except Exception as e:
            print(f"Error crítico: {e}")

if __name__ == "__main__":
    asyncio.run(logout_instance())
