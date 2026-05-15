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
    prompt = "Hola, ¿tienen turnos disponibles para el próximo lunes por la mañana?"
    print(f"Prompt del usuario: '{prompt}'")
    
    try:
        response = await generate_response(prompt)
        print(f"Respuesta de Gemini:\n{response}")
    except Exception as e:
        print(f"[ERROR] Gemini: {str(e)}")

async def main():
    await test_metrics()
    await test_gemini_scheduling()

if __name__ == "__main__":
    asyncio.run(main())
