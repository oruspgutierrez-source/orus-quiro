import os
import sys
import asyncio
from dotenv import load_dotenv
load_dotenv()
sys.path.append('.')

from api.services.gemini_client import generate_response

history_msgs = [
    {"role": "user", "text": "Ya pagué"},
    {"role": "model", "text": "¡Perfecto! Tu pago ha sido confirmado. Retomamos el proceso de agendamiento para tu sesión. [##EOS##]"}
]

prompt = "[Metadatos del Remitente: JID=553598869018@s.whatsapp.net]\nUsuario: Ok"

async def test_call():
    print("Calling generate_response simulating 'Ok' after payment confirmation...")
    try:
        response_dict = await generate_response(
            prompt, 
            media=None, 
            history=history_msgs,
            payment_status='paid',
            appointment_date=None
        )
        print("\n--- RESPONSE FROM GEMINI ---")
        print(response_dict)
        print("----------------------------")
        
    except Exception as e:
        print("Error:", e)

async def main():
    await test_call()

if __name__ == "__main__":
    asyncio.run(main())
