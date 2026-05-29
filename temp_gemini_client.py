import os
import json
from datetime import datetime
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# Inicializamos el cliente as├¡ncrono
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class OrusResponse(BaseModel):
    reply: str = Field(description="La respuesta de Orus dirigida al usuario, separada con ||| si es larga.")
    sentiment: str = Field(description="El sentimiento detectado en el ├║ltimo mensaje del usuario (ej. 'Frustraci├│n', 'Duda', 'Agradecimiento', 'Enojo', 'Curiosidad').")
    requires_human: bool = Field(description="True si Orus no puede resolver la solicitud o el cliente est├í muy enojado o exige expl├¡citamente hablar con un humano. False en otro caso.")

async def generate_response(prompt: str, media: list[dict] | None = None) -> dict:
    """
    Toma un prompt (y opcionalmente media), lo env├¡a a Gemini 2.5 Flash
    y retorna un diccionario con el JSON estructurado.
    
    Args:
        prompt: Texto del prompt con contexto e historial.
        media: Lista opcional de dicts con:
            - "bytes": bytes del archivo
            - "mime_type": "image/jpeg", "audio/ogg", "application/pdf", etc.
            - "media_type": "image", "audio", "document"
            - "file_name": nombre del archivo (opcional, solo docs)
    """
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    system_rules = f"""REGLAS DE FORMATO Y ENTREGA (CR├ìTICO):
Eres Orus, asistente de ventas y dudas de un experto en quiromancia v├®dica.
FECHA Y HORA ACTUAL DEL SISTEMA: {now_str} (├Üsala como referencia para "hoy", "ma├▒ana", "pr├│ximo lunes", etc.)

Act├║as a trav├®s de un chat de mensajer├¡a instant├ínea (tipo WhatsApp). Para que la lectura sea fluida y humana, DEBES fragmentar tus respuestas largas en m├║ltiples mensajes cortos. 

Utiliza exactamente tres barras verticales (|||) para separar cada mensaje que el usuario debe recibir de forma individual.

Ejemplo Correcto:
┬íHola! Soy Orus. ||| Estuve analizando lo que me comentas. ||| Creo que la mejor forma de avanzar es que me des m├ís detalles.

Reglas Estrictas:
1. No uses ||| en medio de una oraci├│n, ├║salo solo como pausas naturales (cambios de idea o p├írrafos).
2. No incluyas vi├▒etas muy largas sin dividirlas.
3. NUNCA cierres tu respuesta final con |||.
4. SIEMPRE debes terminar tu respuesta completa con el token exacto [##EOS##] como ├║ltimo elemento. Este token es interno del sistema y NUNCA ser├í visible para el usuario. Es obligatorio en el 100% de las respuestas.
5. Si el mensaje del usuario es confuso, muy corto, parece incompleto o no tiene sentido claro, NO inventes una interpretaci├│n. En cambio, responde con amabilidad pidiendo que te aclare lo que quiso decir. Ejemplo: "┬íClaro! ┬┐Podr├¡as contarme un poco m├ís sobre lo que quieres saber? As├¡ puedo ayudarte mejor ­ƒÿè [##EOS##]"

Adem├ís, ahora debes analizar el sentimiento del usuario. Clasif├¡calo seg├║n su tono (ej. Frustraci├│n, Duda, Enojo, Inter├®s).
Si el usuario est├í muy molesto, hace preguntas fuera de tu alcance, o pide expl├¡citamente hablar con un humano, debes levantar la bandera 'requires_human' a true.

CAPACIDADES MULTIMODALES:

Cuando el usuario env├¡e contenido multimedia, responde seg├║n el tipo:

1. IMAGEN DE PALMA / MANO:
   - Activa el modo quiromancia v├®dica. Analiza la imagen con todo tu conocimiento.
   - Identifica las l├¡neas principales (vida, coraz├│n, cabeza, destino, sol) y su forma, longitud, profundidad.
   - Observa los montes (J├║piter, Saturno, Apolo, Mercurio, Venus, Luna, Marte).
   - Analiza la forma de la mano (tierra, agua, fuego, aire), los dedos y sus proporciones.
   - Ofrece una lectura detallada, m├¡stica pero accesible, con interpretaciones personalizadas.
   - Si la imagen no es clara, pide amablemente que env├¡e otra foto con mejor iluminaci├│n.

2. IMAGEN GEN├ëRICA (no es una mano):
   - Describe lo que ves y contextualiza en relaci├│n al servicio de Orus si es posible.
   - Si no tiene relaci├│n con quiromancia, responde de forma amable y redirige la conversaci├│n.

3. NOTA DE VOZ / AUDIO:
   - Escucha y comprende el contenido hablado.
   - Responde al contenido del audio como si fuera un mensaje de texto normal.
   - Si el audio no se entiende bien, pide amablemente que lo repita o escriba.

4. DOCUMENTO (PDF, etc.):
   - Lee el contenido del documento.
   - Resume los puntos principales y responde preguntas sobre ├®l.
   - Si el documento no tiene relaci├│n con el servicio, redirige amablemente.

IMPORTANTE: Tu respuesta final SIEMPRE debe ser un JSON v├ílido, sin bloques de c├│digo Markdown (```json ... ```).
ESTRUCTURA DEL JSON:
{{
  "reply": "Tu respuesta dividida con ||| y terminando con [##EOS##]",
  "sentiment": "Frustraci├│n | Duda | Inter├®s | etc",
  "requires_human": false o true
}}"""

    from api.services.calendar_client import check_free_slots, book_appointment

    # Mapeo de herramientas para ejecuci├│n din├ímica
    available_tools = {
        "check_free_slots": check_free_slots,
        "book_appointment": book_appointment
    }

    try:
        # A├▒adimos las herramientas al LLM
        tools = [check_free_slots, book_appointment]

        config = types.GenerateContentConfig(
            system_instruction=system_rules,
            tools=tools
        )
        
        # ÔöÇÔöÇ Construir contenidos iniciales ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
        contents = []
        if media:
            for i, m in enumerate(media):
                media_part = types.Part.from_bytes(
                    data=m["bytes"],
                    mime_type=m["mime_type"]
                )
                contents.append(types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=f"[Adjunto {i+1}: {m['media_type']}]"),
                        media_part
                    ]
                ))
            
            print(f"[Gemini] Enviando {len(media)} archivo(s) multimedia", flush=True)

        # El prompt de texto (que ya contiene las referencias [Adjunto X])
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=prompt)]))

        # ÔöÇÔöÇ Bucle de ejecuci├│n de herramientas ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
        max_turns = 5
        for _ in range(max_turns):
            response = await client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents,
                config=config
            )
            
            # Verificar si hay llamadas a funciones
            function_calls = [p.function_call for p in response.candidates[0].content.parts if p.function_call]
            
            if not function_calls:
                # Si no hay funciones, asumimos que es la respuesta final en JSON
                try:
                    # Limpiar el texto por si viene con markdown
                    raw_text = response.text.strip()
                    if raw_text.startswith("```json"):
                        raw_text = raw_text[7:]
                    if raw_text.startswith("```"):
                        raw_text = raw_text[3:]
                    if raw_text.endswith("```"):
                        raw_text = raw_text[:-3]
                    
                    parsed_json = json.loads(raw_text.strip())
                    return parsed_json
                except Exception as e:
                    print(f"[Gemini] Error parseando respuesta final: {e}\nRaw: {response.text}")
                    # Fallback si no es JSON v├ílido pero hay texto
                    return {
                        "reply": response.text or "Lo siento, tuve un error interno.",
                        "sentiment": "Neutral",
                        "requires_human": True
                    }

            # Si hay funciones, ejecutarlas
            print(f"[Gemini] Detectadas {len(function_calls)} llamadas a funciones", flush=True)
            
            # A├▒adir la respuesta del modelo (que contiene los function_calls) al historial
            contents.append(response.candidates[0].content)
            
            tool_responses = []
            for fc in function_calls:
                tool_name = fc.name
                args = fc.args
                
                if tool_name in available_tools:
                    print(f"[Tool] Ejecutando {tool_name} con {args}", flush=True)
                    try:
                        # Ejecutar la funci├│n (maneja sync/async si fuera necesario, aqu├¡ son sync)
                        result = available_tools[tool_name](**args)
                        tool_responses.append(types.Part.from_function_response(
                            name=tool_name,
                            response={"result": result}
                        ))
                    except Exception as te:
                        print(f"[Tool Error] {te}", flush=True)
                        tool_responses.append(types.Part.from_function_response(
                            name=tool_name,
                            response={"error": str(te)}
                        ))
                else:
                    tool_responses.append(types.Part.from_function_response(
                        name=tool_name,
                        response={"error": f"Tool {tool_name} not found"}
                    ))
            
            # A├▒adir las respuestas de las herramientas al historial
            contents.append(types.Content(role="user", parts=tool_responses))
            
        return {
            "reply": "Lo siento, me qued├® atrapado en un bucle de tareas. Por favor intenta de nuevo.",
            "sentiment": "Confusi├│n",
            "requires_human": True
        }
        
    except Exception as e:
        print(f"Error en Gemini API: {e}")
        raise e
