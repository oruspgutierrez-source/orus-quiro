import asyncio
import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno antes de cualquier importación de módulos internos
load_dotenv()

# Añadir la raíz del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.wa_client import wa_client

async def test_real_audio_send():
    # Destinatario del test real resuelto en logs
    to_number = "553598869018@s.whatsapp.net"
    audio_path = "resources/media/audios/explicacion_proceso.ogg"
    
    print("=== PRUEBA DE ENVÍO DIRECTO DE AUDIO DE RECURSOS ===")
    print(f"Ruta del archivo local: {audio_path}")
    print(f"Existe el archivo?: {os.path.exists(audio_path)}")
    if os.path.exists(audio_path):
        print(f"Tamaño del archivo: {os.path.getsize(audio_path)} bytes")
    
    print(f"\nEnviando audio a {to_number}...")
    try:
        response = await wa_client.send_audio_message(to_number, audio_path, delay=2000)
        print("\nRespuesta de la API:")
        import json
        print(json.dumps(response, indent=2))
        print("\n¡Prueba de envío finalizada!")
    except Exception as e:
        print(f"Error en el envío: {e}")

if __name__ == "__main__":
    asyncio.run(test_real_audio_send())
