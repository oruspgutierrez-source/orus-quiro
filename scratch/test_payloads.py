import asyncio
import os
import base64
import aiohttp
from dotenv import load_dotenv
load_dotenv()

API_URL = os.getenv("EVOLUTION_API_URL")
INSTANCE = os.getenv("EVOLUTION_INSTANCE_NAME")
API_KEY = os.getenv("EVOLUTION_API_KEY")

def get_headers():
    return {
        "apikey": API_KEY,
        "Content-Type": "application/json",
        "Host": "whatsapp.orusquiroterapia.online"
    }

async def send_audio_test(audio_data):
    endpoint = f"{API_URL}/message/sendWhatsAppAudio/{INSTANCE}"
    payload = {
        "number": "553598869018@s.whatsapp.net",
        "audio": audio_data,
        "delay": 1200,
        "encoding": True
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(endpoint, json=payload, headers=get_headers(), ssl=False) as response:
            return response.status, await response.json()

async def main():
    audio_path = "resources/media/audios/explicacion_proceso.ogg"
    with open(audio_path, "rb") as f:
        raw_bytes = f.read()
        encoded = base64.b64encode(raw_bytes).decode("utf-8")
    
    # Pruebas:
    # 1. Clean base64
    print("Probando con base64 limpio...")
    status, res = await send_audio_test(encoded)
    print(f"Limpio -> Status: {status}, Response: {res}")
    
    # 2. Con prefijo data:audio/ogg;base64,
    print("\nProbando con prefijo data:audio/ogg;base64,...")
    status, res = await send_audio_test(f"data:audio/ogg;base64,{encoded}")
    print(f"Con prefijo -> Status: {status}, Response: {res}")

if __name__ == "__main__":
    asyncio.run(main())
