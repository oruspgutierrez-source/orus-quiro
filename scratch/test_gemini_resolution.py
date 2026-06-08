import os
import sys
import asyncio
from dotenv import load_dotenv
load_dotenv()
sys.path.append('.')

from api.services.gemini_client import generate_response

history_msgs = [
    {"role": "user", "text": "Hola, ya pagué. ¿Cómo agendo?"},
    {"role": "model", "text": "Excelente. Tu pago ha sido confirmado. Para agendar tu sesión de Mapeo, disponemos de los siguientes horarios:\n\nMartes 9 de junio:\n- Mañana: 8am, 9am, 10am, 11am\n- Tarde: 2pm, 3pm, 4pm, 5pm\n\nMiércoles 10 de junio:\n- Mañana: 8am, 9am, 10am, 11am\n- Tarde: 2pm, 3pm, 4pm, 5pm\n\n¿Qué día y hora prefieres? [##EOS##]"}
]

prompt = "[Metadatos del Remitente: JID=553598869018@s.whatsapp.net]\nUsuario: Martes 9 de junio"

async def test_call():
    print("Calling generate_response simulating partial selection (day but no hour)...")
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
        
        reply = response_dict.get("reply", "")
        # Validaciones de calidad:
        if "pago está confirmado" in reply or "pago confirmado" in reply:
            print("\n❌ FALLÓ: El bot repitió la confirmación de pago de forma redundante.")
        else:
            print("\n✅ PASÓ: No hay redundancia de confirmación de pago.")
            
        if "Martes 9 de junio" in reply and ("08:00" in reply or "8am" in reply or "8:00" in reply):
            print("✅ PASÓ: El bot reconoció el día y listó las horas disponibles de ese día.")
        else:
            print("❌ FALLÓ: El bot no reconoció el día o no listó las horas.")
            
    except Exception as e:
        print("Error:", e)

async def main():
    await test_call()

if __name__ == "__main__":
    asyncio.run(main())
