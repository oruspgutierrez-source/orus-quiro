import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# Inicializamos el cliente asíncrono
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class OrusResponse(BaseModel):
    reply: str = Field(description="La respuesta de Orus dirigida al usuario, separada con ||| si es larga.")
    sentiment: str = Field(description="El sentimiento detectado en el último mensaje del usuario (ej. 'Frustración', 'Duda', 'Agradecimiento', 'Enojo', 'Curiosidad').")
    requires_human: bool = Field(description="True si Orus no puede resolver la solicitud o el cliente está muy enojado o exige explícitamente hablar con un humano. False en otro caso.")

async def generate_response(prompt: str) -> dict:
    """
    Toma un prompt, lo envía a Gemini 2.5 Flash y retorna un diccionario con el JSON estructurado.
    """
    
    system_rules = """REGLAS DE FORMATO Y ENTREGA (CRÍTICO):
Eres Orus, asistente de ventas y dudas de un experto en quiromancia védica.
Actúas a través de un chat de mensajería instantánea (tipo WhatsApp). Para que la lectura sea fluida y humana, DEBES fragmentar tus respuestas largas en múltiples mensajes cortos. 

Utiliza exactamente tres barras verticales (|||) para separar cada mensaje que el usuario debe recibir de forma individual.

Ejemplo Correcto:
¡Hola! Soy Orus. ||| Estuve analizando lo que me comentas. ||| Creo que la mejor forma de avanzar es que me des más detalles.

Reglas Estrictas:
1. No uses ||| en medio de una oración, úsalo solo como pausas naturales (cambios de idea o párrafos).
2. No incluyas viñetas muy largas sin dividirlas.
3. NUNCA cierres tu respuesta final con |||.

Además, ahora debes analizar el sentimiento del usuario. Clasifícalo según su tono (ej. Frustración, Duda, Enojo, Interés).
Si el usuario está muy molesto, hace preguntas fuera de tu alcance, o pide explícitamente hablar con un humano, debes levantar la bandera 'requires_human' a true."""

    try:
        response = await client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_rules,
                response_mime_type="application/json",
                response_schema=OrusResponse
            )
        )
        # response.text is a JSON string because of the response_schema
        parsed_json = json.loads(response.text)
        return parsed_json
    except Exception as e:
        print(f"Error en Gemini API: {e}")
        raise e
