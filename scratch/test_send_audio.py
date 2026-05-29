import asyncio
import os
from dotenv import load_dotenv
load_dotenv()
from api.services.wa_client import wa_client

async def test():
    to = "553598869018@s.whatsapp.net"
    audio_path = "resources/media/audios/explicacion_proceso.ogg"
    print(f"Probando envío de audio a {to}...")
    res = await wa_client.send_audio_message(to, audio_path)
    print("Resultado:", res)

if __name__ == "__main__":
    asyncio.run(test())
