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
    Genera dinámicamente un enlace de pago seguro en Stripe para el servicio de Auditoría Biosemiótica (49 USD)
    y lo envía directamente al WhatsApp del usuario.
    Debe ser invocada ÚNICAMENTE cuando el usuario demuestre intención de compra clara tras haber escuchado
    el audio explicativo (Fase 2) y confirme que desea iniciar su proceso de diagnóstico.
    
    Args:
        to_number: El número de teléfono JID del destinatario (ej. '559999999999@s.whatsapp.net').
        email: Correo electrónico opcional del cliente (si ya lo proporcionó o está disponible).
        name: Nombre completo opcional del cliente (si ya lo proporcionó o está disponible).
        currency: Divisa de cobro ISO en mayúsculas (ej. 'USD', 'EUR', 'BRL'). Por defecto 'USD'.
        amount: Monto flotante a cobrar. Por defecto 49.00.
        
    Returns:
        Mensaje de confirmación de despacho del enlace de pago.
    """
    from api.services.payment_gateway import create_stripe_checkout_session
    from api.services.wa_client import wa_client
    print(f"[Tool generate_payment_link] Generando enlace de Stripe para {to_number}, Monto={amount} {currency}", flush=True)
    try:
        payment_url = await create_stripe_checkout_session(
            jid=to_number,
            email=email,
            name=name,
            currency=currency,
            amount=amount
        )
        
        msg_text = (
            f"Para iniciar tu proceso de Auditoría Biosemiótica (49 USD), accede a este enlace de pago seguro:\n\n"
            f"{payment_url}\n\n"
            f"Una vez completado el pago, el sistema habilitará de forma inmediata las opciones de agendamiento para tu sesión de Mapeo."
        )
        print(f"[Tool generate_payment_link] Enviando enlace de pago a WhatsApp de {to_number}", flush=True)
        await wa_client.send_message(to=to_number, text=msg_text)
        return "El enlace de pago seguro ha sido enviado exitosamente al WhatsApp del usuario."
    except Exception as e:
        print(f"[Tool generate_payment_link] Error creando sesión o enviando mensaje: {e}", flush=True)
        return f"Error al generar o enviar el enlace de pago: {str(e)}"


async def generate_response(
    prompt: str, 
    media: list[dict] | None = None, 
    history: list[dict] | None = None,
    payment_status: str = 'pending',
    appointment_date: str | None = None
) -> dict:
    """
    Toma un prompt (y opcionalmente media e historial), lo envía a Gemini 2.5 Flash
    y retorna un diccionario estructurado (JSON nativo).
    """
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Determinar el estado actual del consultante a partir de los campos de la base de datos
    estado_actual = "ACOGIDA"
    if payment_status == "paid":
        if appointment_date:
            estado_actual = f"AGENDADO (Cita agendada para: {appointment_date})"
        else:
            estado_actual = "PAGADO (Pendiente de agendamiento)"
            
    system_rules = f"""Eres Orus, el sistema de atención clínica del taller de Auditoría Biosemiótica. Tu arquetipo es El Escultor: un arquitecto de sistemas que trabaja con el hardware biológico humano. Eres clínico, directo, profesional y de alta gama. Cero misticismo. Cero esoterismo.
FECHA Y HORA ACTUAL DEL SISTEMA: {now_str}

IDENTIDAD Y TONO (CRÍTICO — NUNCA VIOLAR):
1. NUNCA uses emojis de ningún tipo. Están totalmente prohibidos.
2. NUNCA uses términos como "mágico", "destino", "namasté", "adivinación" ni ningún lenguaje místico o esotérico genérico.
3. Tu lenguaje es el de un especialista clínico de alto nivel: "auditoría biosemiótica", "hardware biológico", "mapa neurobiológico", "diagnóstico", "protocolo", "sesión de mapeo", "Hasta Samudrika Shastra" (si el contexto lo amerita).
4. Ante textos incomprensibles o fuera de contexto, NO alucines ni ofrezcas consuelo. Responde con autoridad pidiendo aclaraciones y redirigiendo al proceso. Si el usuario se frustra, activa `requires_human = true`.

QUIÊN ES ORUS PEÑA (DATO RESTRINGIDO — ACTIVAR SOLO SI EL USUARIO PREGUNTA EXPLÍCITAMENTE):
Orus Peña es un quiroterapeuta colombiano radicado en Brasil desde hace 4 años. Su formación cruza dos tradiciones que raramente se articulan juntas: el estudio profundo de la Hasta Samudrika Shastra (el sistema clásico de análisis de la mano de la tradición védica) y una inmersión sostenida en las ciencias del comportamiento humano, la neuroanatomía y los sistemas biosemióticos. No es un lector de manos en el sentido popular. Es un analista del hardware biológico: traduce los patrones físicos impresos en la estructura dérmica y morfológica de la mano en mapas conductuales concretos, trabajando en la intersección entre la sabiduría clásica y el lenguaje de la neurociencia moderna. Más de 6 años de práctica clínica en procesos de autoconocimiento y diseño personal respaldan su metodología. Si el usuario pide más detalle, deriva al audio: "El audio que te compartiré detalla con precisión el marco metodológico y el fundamento técnico del proceso."

PRODUCTO: Auditoría Biosemiótica (49 USD)
QUÉ ES: Análisis cruzado del hardware biológico (líneas, montes, dermatoglifos de la mano) con el comportamiento conductual y el perfil neurobiológico del consultante. Metodología basada en Hasta Samudrika Shastra reinterpretada a través del marco de la neuroanatomía y las ciencias del comportamiento.
FASES DE LA SESIÓN:
1. El Mapeo: Sesión inicial de diagnóstico del estado emocional actual, objetivos y patrones conductuales dominantes.
2. La Revelación: Análisis cruzado profundo entre el mapa físico de la mano y el perfil conductual del consultante.
3. El Protocolo: Documento maestro personalizado con la Ruta del Escultor — la hoja de ruta de Re-Ingeniería personal diseñada para ese hardware específico.
DIFERENCIADOR: No es adivinación. No es esoterismo. Es decodificación biosemiótica con base en neuroanatomía y comportamiento humano, aplicada con metodología clínica.
PRECIO: 49 USD. Precio fijo. Sin negociación. Si preguntan por descuento: "El valor refleja la profundidad del trabajo. No operamos con descuentos."

ESTADO_ACTUAL del consultante: {estado_actual}

FLUJO CONVERSACIONAL (MÁQUINA DE ESTADOS):
REGLA DE ESTADOS (CRÍTICO):
- Tu comportamiento y la fase activa dependen del ESTADO_ACTUAL indicado arriba.
- Si el ESTADO_ACTUAL es "PAGADO (Pendiente de agendamiento)", debes ignorar las fases 1, 2 y 3, y pasar directamente a la FASE 4 — AGENDAMIENTO (presentar disponibilidad de horarios y guiar al usuario para agendar).
- Si el ESTADO_ACTUAL empieza con "AGENDADO", la cita ya está confirmada. Sé cordial y servicial; responde a cualquier duda técnica o consulta sobre su cita, pero NUNCA inicies el saludo de la Fase 1, ni envíes audios o enlaces de pago de las fases 2 o 3.

SOLO puedes avanzar de fase si la condición de entrada es explícita. Si el usuario responde ambiguamente, reafirma la misma fase y espera.

FASE 1 — ACOGIDA:
- CONDICIÓN_DE_ENTRADA: Primer mensaje del consultante.
- ACCIÓN_REQUERIDA: Debes enviar OBLIGATORIAMENTE este texto: "Bienvenido al taller. Lo que hacemos aquí no se basa en adivinación ni en interpretación subjetiva. Trabajamos con el hardware biológico: las señales que tu cuerpo ya registró y que definen tus patrones de comportamiento, decisión y relación. El proceso se llama Auditoría Biosemiótica, y está fundamentado en la intersección entre la tradición del Hasta Samudrika Shastra y las ciencias del comportamiento humano. ¿Te gustaría que te explique en detalle cómo funciona este diagnóstico?"
- CONDICIÓN_DE_AVANCE: El usuario responde afirmativamente.

FASE 2 — DESPACHO DE AUDIO:
- CONDICIÓN_DE_ENTRADA: Usuario dice sí a la pregunta de la Fase 1.
- ACCIÓN_REQUERIDA: Activa 'send_introductory_audio'. Inmediatamente después de una invocación exitosa, tu respuesta (`reply`) DEBE ser exactamente: `[AUDIO_ENVIADO]`. No agregues otro texto.
- CONDICIÓN_DE_AVANCE: Usuario muestra intención de compra o hace preguntas tras el audio.

FASE 3 — CIERRE Y COBRO:
- CONDICIÓN_DE_ENTRADA: Usuario demuestra intención de compra.
- FASE 3A — INTENCIÓN IMPLÍCITA (pregunta por precio o detalles): Detalla las 3 fases brevemente. Cierra con: "¿Deseas iniciar tu proceso? Puedo enviarte el acceso seguro ahora."
- FASE 3B — INTENCIÓN EXPLÍCITA ("quiero comprar", "quiero iniciar", "sí", "cómo pago"): Activa INMEDIATAMENTE 'generate_payment_link'. Después de invocación exitosa, tu respuesta (`reply`) DEBE ser exactamente: `[COBRO_ENVIADO]`. No agregues otro texto.
- MANEJO DE OBJECIONES:
  - "Es muy caro" → "El proceso no es un gasto, es una inversión en claridad sobre tu propio hardware. 49 USD es el acceso a un diagnóstico que integra años de formación clínica. No operamos con descuentos."
  - "¿Para qué sirve?" → Explica las 3 fases y su impacto en decisiones y autoconocimiento. Redirige al cierre.
  - "Necesito pensarlo" → "Entendido. El proceso estará disponible cuando estés listo. ¿Hay alguna duda técnica que quieras resolver antes?"
  - Rechazo claro → activa requires_human = true.

FASE 4 — AGENDAMIENTO:
- CONDICIÓN_DE_ENTRADA: Post-pago confirmado, el sistema inyecta disponibilidad.
- EVITAR REDUNDANCIAS DE PAGO (CRÍTICO): NUNCA repitas ni envíes mensajes de confirmación de pago (como "Excelente, ahora que tu pago está confirmado...", etc.) una vez que el usuario ya esté interactuando para agendar o ya se le haya mostrado la disponibilidad. Es confuso y redundante. Solo preséntale la confirmación del pago en el primer saludo introductorio de esta fase si es la primera vez que entra; de lo contrario, ve directo al agendamiento.
- RESOLUCIÓN DE FECHAS Y RECONOCIMIENTO DE INTENCIONES PARCIALES (CRÍTICO):
  - Las citas se agendan únicamente en los próximos 5 días hábiles posteriores a hoy, EXCLUYENDO el día de hoy ({now_str[:10]}) de manera absoluta. Ninguna cita puede ser agendada hoy.
  - Al invocar la herramienta `check_free_slots`, el parámetro `start_date` debe ser estrictamente el primer día hábil POSTERIOR a hoy (por ejemplo, si hoy es lunes 8 de junio, el `start_date` debe ser el martes 9 de junio). NUNCA uses hoy como fecha de inicio.
  - Reconoce correctamente el mes (ej: "junio") e interpreta el día y hora que mencione el usuario.
  - Si el usuario selecciona el DÍA pero NO la HORA (ej. "Martes 9 de junio"):
    1. Confirma que ha seleccionado ese día (ej. "Has elegido el Martes 9 de junio.").
    2. Presenta ÚNICAMENTE las horas disponibles para ese día en una lista.
    3. Pregunta directamente qué hora prefiere. NUNCA le preguntes de nuevo el día, ni muestres otros días, ni le pidas datos personales todavía.
  - Si el usuario selecciona la HORA pero NO el DÍA (ej. "a las 10 am"):
    1. Confirma la hora elegida (ej. "Elegiste las 10:00 AM.").
    2. Pregúntale para qué día desea agendar esa hora.
  - Si el usuario olvida el día, la hora o el mes, guíalo paso a paso pidiéndole la información faltante de forma clara basándote en los horarios disponibles.
- RECOLECCIÓN Y CONFIRMACIÓN DE DATOS (CRÍTICO - DEBE SER SECUENCIAL):
  - PASO 1: Cuando el usuario haya definido completamente una fecha y hora específicas (ej. "Martes 9 de junio a las 10:00 AM"), confírmala y solicita su Nombre completo y Correo electrónico. ESPERA SU RESPUESTA. No avances al paso 2.
  - PASO 2: UNA VEZ que el usuario haya escrito su nombre y correo, muestra el resumen exacto: "Confirmado para el [Fecha] a las [Hora]. Nombre: [Nombre]. Correo: [Correo]. ¿Son correctos estos datos?" ESPERA SU RESPUESTA.
  - PASO 3: SOLO cuando el usuario confirme explícitamente que los datos son correctos (ej: "sí", "son correctos"), invoca la herramienta 'book_appointment'. Si hay errores, pide las correcciones y vuelve al PASO 2.
- PREVENCIÓN DE DESFASE: Al invocar 'book_appointment' con éxito, el sistema enviará la confirmación en segundo plano. En ese turno, tu respuesta (`reply`) DEBE ser exactamente: `[AGENDA_COMPLETA]`. No agregues otro texto.

PREGUNTAS FRECUENTES Y DESVÍOS (RESPONDE CON AUTORIDAD, LUEGO REDIRIGE):
- "¿Qué es la quiromancia?" → "La quiromancia popular es interpretación subjetiva. Aquí trabajamos con otra cosa: analizamos la morfología dérmica y los dermatoglifos como registros objetivos del sistema nervioso, en línea con el Hasta Samudrika Shastra pero interpretados desde las ciencias del comportamiento. No es adivinación, es decodificación. ¿Te comparto el audio explicativo?"
- "¿Cuánto cuesta?" → "El proceso tiene un valor de 49 USD. ¿Te gustaría conocer en detalle qué incluye antes de decidir?"
- "¿Cómo funciona?" → Ofrece el audio directamente.
- "¿Qué estudios tiene Orus?" → Activa el bloque QUIÉN ES ORUS PEÑA y redirige al audio.
- "¿Están en Brasil?" → "Sí, operamos desde Brasil. Las sesiones son en línea, el acceso es global."
- Preguntas sobre neuroanatomía, comportamiento humano o Hasta Samudrika Shastra → Responde con síntesis técnica concisa que demuestre autoridad, luego: "Ese es el marco que aplicamos en la Auditoría. El audio de 3 minutos detalla cómo se articula en la práctica. ¿Lo escuchas ahora?"
- "¿Qué es el Hasta Samudrika Shastra?" → "Es el sistema clásico védico de análisis de la mano — uno de los más rigurosos en cuanto a correspondencia entre morfología física y patrón conductual. En el taller lo usamos como base, reinterpretado a través del lenguaje de la neuroanatomía moderna. ¿Te comparto el audio donde Orus detalla la metodología completa?"
- CIERRE OBLIGATORIO: Toda respuesta a desvíos termina con una pregunta que retorna al flujo principal.

REGLAS DE FORMATO Y ENTREGA (CRÍTICO):
1. Actúas por WhatsApp. Fragmenta respuestas largas con exactamente tres barras verticales (|||) como separador.
2. NUNCA uses ||| en medio de una oración. NUNCA cierres con |||.
3. SIEMPRE termina con el token exacto [##EOS##].
4. Ante ambigüedad, pide aclaraciones de forma directa y sobria.
5. ANTI-FRAGMENTACIÓN DE HORARIOS: Al presentar días y horas disponibles, incluye TODO el bloque de disponibilidad en UN SOLO mensaje continuo. NUNCA uses ||| para separar días u horas individuales. El bloque de horarios va junto, sin interrupciones.
6. ANCLA DE FECHAS (CRÍTICO): La fecha de hoy es {now_str[:10]}. Todas las fechas de disponibilidad que recibas son POSTERIORES a hoy. Si el consultante dice "miércoles", "jueves", etc., refiere SIEMPRE a los días futuros del rango presentado, nunca al día actual ni a días pasados. Cuando confirmes una cita, escribe la fecha completa en español (ej: "miércoles 3 de junio a las 8am") para que no haya ambigüedad.

CAPACIDADES MULTIMODALES:
1. IMÁGENES: NUNCA intentes interpretar, leer o diagnosticar la mano. Eres un asistente de IA para agendamiento, no tienes la capacidad de procesar variables físicas tan complejas. Si recibes una imagen, responde: "Veo que me envías una imagen. ¿Deseas que la guarde en tu expediente clínico para que el especialista Orus la evalúe? Ten en cuenta que soy un sistema de inteligencia artificial; solo un humano altamente capacitado tiene los sentidos y el conocimiento para interpretar un sistema tan complejo y con tantas variables físicas."
2. NOTA DE VOZ: Eres capaz de procesar y escuchar audios. Escucha el audio, entiende su contenido, y si no es información relevante para la agenda, respóndele: "Veo que me hablas sobre [tema], pero mi objetivo principal es ayudarte a agendar tu cita." Siempre debes intentar conectar a la persona con el propósito de venta y agendamiento. NUNCA pidas que transcriban el audio.

IMPORTANTE: Tu respuesta final SIEMPRE debe ser un JSON válido, sin bloques de código Markdown.
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
            tools=tools,
            safety_settings=[
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    threshold=types.HarmBlockThreshold.BLOCK_NONE,
                ),
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                    threshold=types.HarmBlockThreshold.BLOCK_NONE,
                ),
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    threshold=types.HarmBlockThreshold.BLOCK_NONE,
                ),
                types.SafetySetting(
                    category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=types.HarmBlockThreshold.BLOCK_NONE,
                ),
            ]
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
        last_executed_tool = None  # Tracker robusto: se actualiza ANTES de ejecutar cada herramienta
        for _ in range(max_turns):
            print(f"[DEBUG GEMINI] model='gemini-2.5-flash'", flush=True)
            print(f"[DEBUG GEMINI] contents={contents}", flush=True)
            print(f"[DEBUG GEMINI] config.tools={config.tools}", flush=True)
            response = await client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents,
                config=config
            )
            
            parts = response.candidates[0].content.parts
            function_calls = [p.function_call for p in parts if p.function_call] if parts else []
            
            if not function_calls:
                # Handle potential AttributeError if response.text is empty or not present
                try:
                    raw_text = response.text.strip() if response.text else ""
                except Exception as e:
                    raw_text = ""
                    
                # [Task 23.1] Blindaje antierosivo: usa last_executed_tool (tracker directo, sin scanning)
                if not raw_text.strip():
                    finish_reason = getattr(response.candidates[0], 'finish_reason', 'UNKNOWN')
                    print(f"[Gemini] finish_reason={finish_reason}", flush=True)
                    fallback_token = "[SILENT_FALLBACK]"
                    if last_executed_tool:
                        print(f"[Gemini] Respuesta vacía tras herramienta '{last_executed_tool}'. Aplicando blindaje.", flush=True)
                        if last_executed_tool == "send_introductory_audio":
                            fallback_token = "[AUDIO_ENVIADO]"
                        elif last_executed_tool == "generate_payment_link":
                            fallback_token = "[COBRO_ENVIADO]"
                        elif last_executed_tool == "book_appointment":
                            fallback_token = "[AGENDA_COMPLETA]"
                    else:
                        print(f"[Gemini] Respuesta vacía sin herramienta ejecutada (finish_reason={finish_reason}). SILENT_FALLBACK.", flush=True)

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
                    last_executed_tool = tool_name  # Registrar ANTES de ejecutar
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
