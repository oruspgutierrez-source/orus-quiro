import os
import asyncio
from dotenv import load_dotenv
load_dotenv()
from google import genai
from google.genai import types
from api.services.calendar_client import check_free_slots, book_appointment

async def run_calendar_test():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    # Simular una conversación con la API de Chats de Gemini 
    print("Iniciando chat con Gemini (Simulación de Function Calling)...")
    chat = client.aio.chats.create(
        model='gemini-2.5-flash',
        config=types.GenerateContentConfig(
            system_instruction="Eres Orus, un asistente de quiromancia que agenda citas. Hoy es 2026-04-25. Usa las herramientas de calendario para ver disponibilidad y agendar.",
            tools=[check_free_slots, book_appointment],
            temperature=0.7
        )
    )

    msg1 = "Hola Orus, me encantaría una lectura profunda. ¿Tienes algún espacio libre para mañana por la tarde?"
    print(f"\n[Cliente]: {msg1}")
    
    response = await chat.send_message(msg1)
    
    # Procesar Function Calling
    while response.function_calls:
        function_responses = []
        for fc in response.function_calls:
            print(f"\n[Orus/Gemini] -> ¡Decidió usar la herramienta!: {fc.name} con args: {fc.args}")
            if fc.name == "check_free_slots":
                res = check_free_slots(**fc.args)
            elif fc.name == "book_appointment":
                res = book_appointment(**fc.args)
            else:
                res = "Función desconocida"
            
            function_responses.append(
                types.Part.from_function_response(name=fc.name, response={"result": res})
            )
            
        print(f"[Sistema] Devolviendo resultado de la BD/API al LLM...")
        response = await chat.send_message(function_responses)
        
    print(f"\n[Orus]: {response.text}")

    msg2 = "¡Perfecto! Resérvame mañana a las 15:00, por favor. Mi nombre es Carlos. Mi teléfono es 1234567890."
    print(f"\n[Cliente]: {msg2}")
    
    response = await chat.send_message(msg2)
    
    while response.function_calls:
        function_responses = []
        for fc in response.function_calls:
            print(f"\n[Orus/Gemini] -> ¡Decidió usar la herramienta!: {fc.name} con args: {fc.args}")
            if fc.name == "check_free_slots":
                res = check_free_slots(**fc.args)
            elif fc.name == "book_appointment":
                res = book_appointment(**fc.args)
            else:
                res = "Función desconocida"
            
            function_responses.append(
                types.Part.from_function_response(name=fc.name, response={"result": res})
            )
            
        print(f"[Sistema] Devolviendo resultado de la BD/API al LLM...")
        response = await chat.send_message(function_responses)
        
    print(f"\n[Orus]: {response.text}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(run_calendar_test())
