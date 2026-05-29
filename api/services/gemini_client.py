import os
import json
from datetime import datetime
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# Inicializamos el cliente asíncrono
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class OrusResponse(BaseModel):
    reply: str = Field(description="La respuesta de Orus dirigida al usuario, separada con ||| si es larga y SIEMPRE terminando con [##EOS##].")
    sentiment: str = Field(description="El sentimiento detectado en el último mensaje del usuario (ej. 'Frustración', 'Duda', 'Agradecimiento', 'Enojo', 'Curiosidad').")
    requires_human: bool = Field(description="True si Orus no puede resolver la solicitud o el cliente está muy enojado o exige explícitamente hablar con un humano. False en otro caso.")

async def send_introductory_audio(to_number: str) -> str:
    """
    Envía el audio introductorio pregrabado de 3 minutos de duración al consultante
    para explicar detalladamente el proceso de Auditoría Biosemiótica: cómo se analiza
    el hardware biológico del consultante y cómo se estructura la sesión de diagnóstico.
    Debe ser invocada ÚNICAMENTE cuando el usuario responda afirmativamente a la pregunta
    activadora de Fase 1 (¿Te gustaría que te explique cómo funciona el proceso de diagnóstico?).
    
    Args:
        to_number: El número de teléfono JID del destinatario (ej. '559999999999@s.whatsapp.net').
        
    Returns:
        Un mensaje de confirmación del despacho de la nota de voz.
    """
    from api.services.wa_client import wa_client
    audio_path = "resources/media/audios/explicacion_proceso.ogg"
    text = "Perfecto. Te comparto este audio de 3 minutos. Aqui, el especialista detalla exactamente que analizamos en tu hardware biologico y como estructuraremos tu sesion. Escuchalo con atencion; estare aqui para resolver cualquier duda tecnica o para iniciar tu proceso cuando estes listo."
    print(f"[Tool send_introductory_audio] Disparando envío asíncrono de texto y audio a {to_number}", flush=True)
    await wa_client.send_text_then_audio(to_number, text, audio_path, text_delay=1200, gap_seconds=2.0)
    return "El audio explicativo de 3 minutos ha sido enviado exitosamente al WhatsApp del usuario."

async def generate_payment_link(
    to_number: str, 
    email: str | None = None, 
    name: str | None = None, 
    currency: str = "USD", 
    amount: float = 49.00
) -> str:
    """
    Genera dinámicamente un enlace de pago seguro en Stripe para el servicio de Auditoría Biosemiótica (49 USD).
    Debe ser invocada ÚNICAMENTE cuando el usuario demuestre intención de compra clara tras haber escuchado
    el audio explicativo (Fase 2) y confirme que desea iniciar su proceso de diagnóstico.
    
    Args:
        to_number: El número de teléfono JID del destinatario (ej. '559999999999@s.whatsapp.net').
        email: Correo electrónico opcional del cliente (si ya lo proporcionó o está disponible).
        name: Nombre completo opcional del cliente (si ya lo proporcionó o está disponible).
        currency: Divisa de cobro ISO en mayúsculas (ej. 'USD', 'EUR', 'BRL'). Por defecto 'USD'.
        amount: Monto flotante a cobrar. Por defecto 49.00.
        
    Returns:
        La URL del enlace de pago de Stripe generado para que se la entregues al usuario.
    """
    from api.services.payment_gateway import create_stripe_checkout_session
    print(f"[Tool generate_payment_link] Generando enlace de Stripe para {to_number}, Monto={amount} {currency}", flush=True)
    try:
        payment_url = await create_stripe_checkout_session(
            jid=to_number,
            email=email,
            name=name,
            currency=currency,
            amount=amount
        )
        return payment_url
    except Exception as e:
        print(f"[Tool generate_payment_link] Error creando sesión: {e}", flush=True)
        return f"Error al generar el enlace de pago: {str(e)}"

async def generate_response(prompt: str, media: list[dict] | None = None, history: list[dict] | None = None) -> dict:
    """
    Toma un prompt (y opcionalmente media e historial), lo envía a Gemini 2.5 Flash
    y retorna un diccionario estructurado (JSON nativo).
    """
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    system_rules = f"""Eres Orus, el sistema de atención clínica del taller de Auditoría Biosemiótica. Tu arquetipo es El Escultor: un arquitecto de sistemas que trabaja con el hardware biológico humano. Eres clínico, directo, profesional y de alta gama. Cero misticismo. Cero esoterismo.
FECHA Y HORA ACTUAL DEL SISTEMA: {now_str}

IDENTIDAD Y TONO (CRÍTICO — NUNCA VIOLAR):
1. NUNCA uses emojis de ningún tipo. Están totalmente prohibidos.
2. NUNCA uses términos como "mágico", "destino", "vedas", "namasté", "quiromancia" ni ningún lenguaje místico o espiritual.
3. Tu lenguaje es el de un especialista clínico de alto nivel: "auditoría biosemiótica", "hardware biológico", "mapa neurobiológico", "diagnóstico", "protocolo", "sesión de calibración".
4. Ante textos incomprensibles o fuera de contexto, NO alucines ni ofrezcas consuelo. Responde con autoridad pidiendo aclaraciones y redirigiendo al proceso de Auditoría Biosemiótica. Si el usuario se frustra, activa `requires_human = true`.

PRODUCTO: Auditoría Biosemiótica (49 USD)
QUÉ ES: Análisis cruzado del hardware biológico (líneas, montes, dermatoglifos de la mano) con comportamiento conductual del consultante.
FASES DE LA SESIÓN:
1. La Calibración: Sesión inicial de mapeo de estado emocional y objetivos.
2. La Revelación: Análisis profundo cruzado.
3. El Protocolo: Documento maestro de Re-Ingeniería personal.
DIFERENCIADOR: No es adivinación. Es decodificación biosemiótica con metodología clínica.

ESTADO_ACTUAL del consultante (puede ser: ACOGIDA | INTERESADO | AUDIO_ENVIADO | COMPRA_INTENTO | PAGADO | AGENDADO)

FLUJO CONVERSACIONAL (MÁQUINA DE ESTADOS):
SOLO puedes avanzar de fase si la condición de entrada es explícita. Si el usuario responde ambiguamente, reafirma la misma fase y espera.

FASE 1 — ACOGIDA:
- CONDICIÓN_DE_ENTRADA: Primer mensaje del consultante.
- ACCIÓN_REQUERIDA: Debes enviar OBLIGATORIAMENTE este texto en tu primera interacción: "Bienvenido al taller. Entiendo que buscas respuestas. Nuestro enfoque no se basa en adivinación, sino en una auditoría biosemiótica profunda: cruzamos tu comportamiento actual con el mapa neurobiológico impreso en tus manos. ¿Te gustaría que te explique a detalle cómo funciona este proceso de diagnóstico?"
- CONDICIÓN_DE_AVANCE: El usuario responde afirmativamente.

FASE 2 — DESPACHO DE AUDIO:
- CONDICIÓN_DE_ENTRADA: Usuario dice sí a la pregunta de la Fase 1.
- ACCIÓN_REQUERIDA: Activa 'send_introductory_audio' para enviar el audio explicativo. Inmediatamente después de una invocación exitosa, tu respuesta (`reply`) DEBE ser exactamente: `[AUDIO_ENVIADO]`. No agregues otro texto.
- CONDICIÓN_DE_AVANCE: Usuario escucha el audio y muestra intención de compra o hace preguntas.

FASE 3 — CIERRE Y COBRO:
- CONDICIÓN_DE_ENTRADA: Usuario demuestra intención de compra tras el audio.
- FASE 3A — INTENCIÓN IMPLÍCITA (pregunta por precio/consulta): Detalla las 3 fases (La Calibración, La Revelación, El Protocolo) en un mensaje corto. Al terminar, pregunta: "¿Deseas iniciar tu proceso? Puedo enviarte el acceso seguro ahora."
- FASE 3B — INTENCIÓN EXPLÍCITA (dice "quiero comprar/iniciar/sí"): Activa INMEDIATAMENTE 'generate_payment_link' sin más texto previo. El link se entrega en una línea. Inmediatamente después de una invocación exitosa, tu respuesta (`reply`) DEBE ser exactamente: `[COBRO_ENVIADO]`. No agregues otro texto.
- MANEJO DE OBJECIONES: Si duda, reafirma una sola vez el valor diferenciador ("No es adivinación, es decodificación"). Si rechaza de forma clara, activa requires_human = true. Si hace otra pregunta, responde y vuelve a ofrecer el proceso al final.

FASE 4 — AGENDAMIENTO:
- CONDICIÓN_DE_ENTRADA: Post-pago confirmado, el sistema inyecta disponibilidad.
- ACCIÓN_REQUERIDA: Presenta los horarios estructurados y pide elección. 
- RESOLUCIÓN DE FECHAS (CRÍTICO): 
  - La disponibilidad que recibirás ya está calculada para los PRÓXIMOS 5 DÍAS HÁBILES del año actual.
  - Si el consultante dice "el jueves" o "jueves a las 9", asume que se refiere al jueves DENTRO del rango ya presentado.
  - Si dice "9 am", asume el primer día disponible que tenga ese horario.
  - NUNCA le pidas que escriba la fecha en formato ISO.
  - Construye el ISO 8601 internamente (YYYY-MM-DDThh:mm:00-03:00) cuando tengas día y hora.
- CONFIRMACIÓN DE DATOS (CRÍTICO):
  - Cuando tengas fecha/hora, solicita Nombre y Correo.
  - Una vez proporcionados, DEBES mostrar un resumen (Ej: "Confirmado para el [Fecha] a las [Hora]. Datos: [Nombre], [Correo]. ¿Son correctos?") y preguntarle si son correctos.
  - Si hay errores, pide las correcciones.
  - SOLO cuando el usuario confirme explícitamente que los datos son correctos, invoca 'book_appointment'.
- PREVENCIÓN DE DESFASE: Al invocar 'book_appointment' con éxito, el sistema enviará la confirmación y guías automáticamente en segundo plano. En ese turno, tu respuesta (`reply`) DEBE ser exactamente la palabra clave secreta: `[AGENDA_COMPLETA]`. No agregues despedidas ni ningún otro texto.

PREGUNTAS FRECUENTES Y DESVÍOS:
- "¿Qué es la quiromancia?" → Respuesta técnica breve + redirección a audio explicativo.
- "¿Cuánto cuesta?" → La sesión de diagnóstico tiene un valor de 49 USD. ¿Te gustaría que te envíe el audio explicativo sobre cómo funciona?
- "¿Cómo funciona?" → Oferta del audio explicativo.
- Cualquier pregunta fuera de contexto → Reafirma el valor y redirige al flujo principal.
- CIERRE OBLIGATORIO: Siempre cierra tu respuesta en desvíos con una pregunta de retorno al flujo (ej. "¿Te gustaría que te envíe el audio explicativo?").

REGLAS DE FORMATO Y ENTREGA (CRÍTICO):
1. Actúas a través de WhatsApp. Fragmenta respuestas largas usando exactamente tres barras verticales (|||) como separador entre mensajes.
2. NUNCA uses ||| en medio de una oración. NUNCA cierres con |||.
3. SIEMPRE termina tu respuesta completa con el token exacto [##EOS##].
4. Si el mensaje del usuario es ambiguo, pide aclaraciones de forma directa y sobria.

CAPACIDADES MULTIMODALES:
1. IMAGEN DE PALMA / MANO: Analiza las señales biosemióticas impresas en la mano (líneas, montes, forma) de manera técnica y estructurada. Si no es clara, solicita otra con instrucciones de iluminación.
2. NOTA DE VOZ: Escucha y responde al contenido hablado con el mismo tono clínico.

IMPORTANTE: Tu respuesta final SIEMPRE debe ser un JSON válido, sin bloques de código Markdown (```json ... ```).
ESTRUCTURA DEL JSON:
{{
  "reply": "Tu respuesta dividida con ||| y terminando con [##EOS##]",
  "sentiment": "Frustración | Duda | Interés | Curiosidad | etc",
  "requires_human": false
}}
"""

    from api.services.calendar_client import check_free_slots, book_appointment

    available_tools = {
        "check_free_slots": check_free_slots,
        "book_appointment": book_appointment,
        "send_introductory_audio": send_introductory_audio,
        "generate_payment_link": generate_payment_link
    }

    try:
        tools = [check_free_slots, book_appointment, send_introductory_audio, generate_payment_link]

        config = types.GenerateContentConfig(
            system_instruction=system_rules,
            tools=tools
        )
        
        contents = []
        if history:
            for msg in history:
                if contents and contents[-1].role == msg["role"]:
                    contents[-1].parts.append(types.Part.from_text(text=f"\n{msg['text']}"))
                else:
                    contents.append(types.Content(role=msg["role"], parts=[types.Part.from_text(text=msg["text"])]))

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

        if contents and contents[-1].role == "user":
            contents[-1].parts.append(types.Part.from_text(text=f"\n{prompt}"))
        else:
            contents.append(types.Content(role="user", parts=[types.Part.from_text(text=prompt)]))

        max_turns = 5
        for _ in range(max_turns):
            response = await client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents,
                config=config
            )
            
            parts = response.candidates[0].content.parts
            function_calls = [p.function_call for p in parts if p.function_call] if parts else []
            
            if not function_calls:
                raw_text = response.text.strip() if response.text else ""
                
                # [Task 23.1] Blindaje antierosivo para capturar strings vacíos post-herramienta
                if not raw_text:
                    if len(contents) > 0 and contents[-1].parts and getattr(contents[-1].parts[0], 'function_response', None):
                        last_tool_name = contents[-1].parts[0].function_response.name
                        print(f"[Gemini] Respuesta vacía tras herramienta '{last_tool_name}'. Aplicando blindaje de fallback.", flush=True)
                        fallback_token = "[SILENT_FALLBACK]"
                        if last_tool_name == "send_introductory_audio":
                            fallback_token = "[AUDIO_ENVIADO]"
                        elif last_tool_name == "generate_payment_link":
                            fallback_token = "[COBRO_ENVIADO]"
                        elif last_tool_name == "book_appointment":
                            fallback_token = "[AGENDA_COMPLETA]"
                        
                        return {
                            "reply": f"{fallback_token} [##EOS##]",
                            "sentiment": "Neutral",
                            "requires_human": False
                        }
                
                # Limpiar el texto por si viene con markdown
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.startswith("```"):
                    raw_text = raw_text[3:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                
                # Extraer JSON con regex para evitar basura al final (ej. [##EOS##] suelto)
                import re
                match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                if match:
                    raw_text = match.group(0)
                
                try:
                    parsed_json = json.loads(raw_text.strip())
                    if not parsed_json.get("reply", "").endswith("[##EOS##]"):
                        parsed_json["reply"] = parsed_json.get("reply", "") + " [##EOS##]"
                    return parsed_json
                except Exception as e:
                    print(f"[Gemini] Error parseando respuesta final: {e}\nRaw: {raw_text}")
                    # Si el LLM devolvió texto libre (ignoro el JSON), lo envolvemos manualmente
                    if raw_text and not raw_text.startswith("{"):
                        safe_reply = raw_text.strip()
                        if not safe_reply.endswith("[##EOS##]"):
                            safe_reply += " [##EOS##]"
                        print("[Gemini] Fallback: Envolviendo texto libre en JSON manualmente.", flush=True)
                        return {
                            "reply": safe_reply,
                            "sentiment": "Neutral",
                            "requires_human": False
                        }
                    
                    return {
                        "reply": "Lo siento, tuve un error interno procesando la respuesta. [##EOS##]",
                        "sentiment": "Neutral",
                        "requires_human": True
                    }

            print(f"[Gemini] Detectadas {len(function_calls)} llamadas a funciones", flush=True)
            contents.append(response.candidates[0].content)
            
            tool_responses = []
            for fc in function_calls:
                tool_name = fc.name
                args = fc.args
                
                if tool_name in available_tools:
                    print(f"[Tool] Ejecutando {tool_name} con {args}", flush=True)
                    try:
                        func = available_tools[tool_name]
                        import inspect
                        if inspect.iscoroutinefunction(func):
                            result = await func(**args)
                        else:
                            result = func(**args)
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
            
            contents.append(types.Content(role="user", parts=tool_responses))
            
        return {
            "reply": "Lo siento, me quedé atrapado en un bucle de tareas. Por favor intenta de nuevo. [##EOS##]",
            "sentiment": "Confusión",
            "requires_human": True
        }
        
    except Exception as e:
        safe_err = str(e).encode('ascii', 'replace').decode('ascii')
        print(f"Error en Gemini API: {safe_err}", flush=True)
        raise e
