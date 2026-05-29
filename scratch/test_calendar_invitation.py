import os
import sys
# Asegurar que el directorio raíz está en el path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from dotenv import load_dotenv
load_dotenv()
from google import genai
from google.genai import types
from api.services.calendar_client import book_appointment, check_free_slots
from api.services.gemini_client import generate_response

async def test_direct_booking():
    """Prueba directa de la función book_appointment para verificar la integración con Google Calendar."""
    print("=== TEST 1: Prueba Directa de book_appointment ===")
    phone = "+5491122334455"
    date_time = "2026-05-20T10:00:00-03:00"
    name = "Carlos Perez (Prueba)"
    # Reemplazar con un correo de prueba si se desea recibir la invitación real
    email = "carlos.perez.test.orus@gmail.com"
    
    print(f"Ejecutando book_appointment con email: {email} y fecha: {date_time}...")
    try:
        res = book_appointment(phone_number=phone, date_time=date_time, name=name, email=email)
        print(f"Resultado devuelto por la función:\n{res}\n")
    except Exception as e:
        print(f"Error en book_appointment: {e}\n")

async def test_conversational_flow():
    """Prueba conversacional usando la lógica real de generate_response de Gemini."""
    print("=== TEST 2: Simulación del Flujo Conversacional ===")
    
    # 1. El cliente quiere agendar
    prompt1 = "Hola Orus, me gustaría agendar una cita de quiromancia para el próximo lunes"
    print(f"\n[Cliente]: {prompt1}")
    res1 = await generate_response(prompt=prompt1, history=[])
    reply1 = res1.get("reply", "")
    print(f"[Orus]: {reply1}")
    
    # Simular historial
    history = [
        {"role": "user", "text": prompt1},
        {"role": "model", "text": reply1}
    ]
    
    # 2. El cliente elige un horario
    prompt2 = "Quiero agendar para el lunes a las 10:00"
    print(f"\n[Cliente]: {prompt2}")
    res2 = await generate_response(prompt=prompt2, history=history)
    reply2 = res2.get("reply", "")
    print(f"[Orus]: {reply2}")
    
    history.extend([
        {"role": "user", "text": prompt2},
        {"role": "model", "text": reply2}
    ])
    
    # 3. El cliente da los datos (pero el correo tiene un error ortográfico intencional para probar la corrección)
    prompt3 = "Mis datos son: Nombre completo Carlos Perez, telefono +5491122334455, correo carloss.perez@gmail.con"
    print(f"\n[Cliente]: {prompt3}")
    res3 = await generate_response(prompt=prompt3, history=history)
    reply3 = res3.get("reply", "")
    print(f"[Orus]: {reply3}")
    
    history.extend([
        {"role": "user", "text": prompt3},
        {"role": "model", "text": reply3}
    ])
    
    # 4. El cliente corrige el correo
    prompt4 = "Perdón, escribí mal mi correo. Es carlos.perez@gmail.com"
    print(f"\n[Cliente]: {prompt4}")
    res4 = await generate_response(prompt=prompt4, history=history)
    reply4 = res4.get("reply", "")
    print(f"[Orus]: {reply4}")
    
    history.extend([
        {"role": "user", "text": prompt4},
        {"role": "model", "text": reply4}
    ])
    
    # 5. El cliente confirma que sí (Gemini debe llamar a book_appointment aquí)
    prompt5 = "Sí, ahora los datos son correctos"
    print(f"\n[Cliente]: {prompt5}")
    res5 = await generate_response(prompt=prompt5, history=history)
    reply5 = res5.get("reply", "")
    print(f"[Orus]: {reply5}")

if __name__ == "__main__":
    async def main():
        # Ejecutar prueba directa
        await test_direct_booking()
        # Ejecutar prueba conversacional interactiva
        await test_conversational_flow()
        
    asyncio.run(main())
