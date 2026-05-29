import requests
import asyncio
from dotenv import load_dotenv
load_dotenv()
from api.services.gemini_client import generate_response

async def test_metrics():
    print("--- 📊 Probando Endpoints de Métricas ---")
    base_url = "http://127.0.0.1:8000/api/metrics"
    endpoints = [
        "/bot_vs_human",
        "/conversion",
        "/appointments_weekly",
        "/users_retention",
        "/error_rate"
    ]
    
    for ep in endpoints:
        try:
            res = requests.get(base_url + ep)
            print(f"[{res.status_code}] {ep}: {res.json()}")
        except Exception as e:
            print(f"[ERROR] {ep}: {str(e)}")

async def test_gemini_scheduling():
    print("\n--- 🤖 Probando Gemini Function Calling (Agendamiento) ---")
    user_phone = "5491112345678"
    user_name = "Prueba Test"
    # Modificamos un poco el prompt para que caiga en check_free_slots o book_appointment
    prompt = "Si perfecto"
    print(f"Prompt del usuario: '{prompt}'")
    
    history = [
        {"role": "user", "text": "Me gustaría el martes de la semana que viene a las 10 de la mañana mi número es 5537998869018 orus peña Gutiérrez"},
        {"role": "model", "text": "¡Excelente! Estoy agendando tu cita para el martes 19 a las 10:00 AM. Por favor, confírmame que tu nombre completo es Orus Peña Gutiérrez y tu número de teléfono es 5537998869018 para que la reserva quede perfecta."}
    ]
    
    try:
        response = await generate_response(prompt, history=history)
        print(f"Respuesta de Gemini:\n{response}")
    except Exception as e:
        print(f"[ERROR] Gemini: {str(e)}")

async def main():
    await test_metrics()
    await test_gemini_scheduling()

if __name__ == "__main__":
    asyncio.run(main())
