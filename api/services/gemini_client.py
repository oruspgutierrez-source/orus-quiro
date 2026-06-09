import os
import json
import base64
from datetime import datetime
import httpx
from pydantic import BaseModel, Field

# Configuración de OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")

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

# Declaración de herramientas en formato OpenAI
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "send_introductory_audio",
            "description": "Envía el audio introductorio de 3 minutos sobre el proceso de Auditoría Biosemiótica. Invocar ÚNICAMENTE cuando el usuario dice SÍ a la pregunta explicativa de Fase 1.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to_number": {
                        "type": "string",
                        "description": "Número de teléfono JID completo (ej. '559999999999@s.whatsapp.net')."
                    }
                },
                "required": ["to_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_payment_link",
            "description": "Genera y envía un enlace de pago de Stripe al usuario. Invocar cuando el usuario demuestra intención de compra clara.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to_number": {
                        "type": "string",
                        "description": "Número de teléfono JID completo."
                    },
                    "email": {
                        "type": "string",
                        "description": "Email opcional del cliente si está disponible."
                    },
                    "name": {
                        "type": "string",
                        "description": "Nombre opcional del cliente."
                    },
                    "currency": {
                        "type": "string",
                        "description": "Divisa de cobro ISO (ej. 'USD', 'BRL'). Por defecto 'USD'."
                    },
                    "amount": {
                        "type": "number",
                        "description": "Monto. Por defecto 49.00."
                    }
                },
                "required": ["to_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_free_slots",
            "description": "Consulta los horarios disponibles en el calendario para un rango de fechas dado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Fecha de inicio en formato YYYY-MM-DD"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Fecha de fin en formato YYYY-MM-DD"
                    }
                },
                "required": ["start_date", "end_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Agenda una cita en el Google Calendar del profesional una vez que los datos del cliente han sido confirmados.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone_number": {
                        "type": "string",
                        "description": "Número de teléfono del cliente."
                    },
                    "date_time": {
                        "type": "string",
                        "description": "Fecha y hora en formato ISO 8601 (ej: '2026-05-20T10:00:00-03:00')."
                    },
                    "name": {
                        "type": "string",
                        "description": "Nombre completo del cliente."
                    },
                    "email": {
                        "type": "string",
                        "description": "Correo electrónico del cliente."
                    }
                },
                "required": ["phone_number", "date_time", "name", "email"]
            }
        }
    }
]

async def generate_response(
    prompt: str, 
    media: list[dict] | None = None, 
    history: list[dict] | None = None,
    payment_status: str = 'pending',
    appointment_date: str | None = None,
    session_mode: str = 'AI'
) -> dict:
    """
    Toma un prompt, media e historial, los traduce al formato de OpenRouter / OpenAI,
    y ejecuta el bucle de razonamiento y herramientas de forma asíncrona.
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    estado_actual = "FASE 1 — ACOGIDA"
    if payment_status == "paid":
        if appointment_date:
            estado_actual = f"AGENDADO (Cita agendada para: {appointment_date})"
        else:
            estado_actual = "FASE 4 — AGENDAMIENTO"
    else:
        if session_mode == 'PHASE_1_ACOGIDA':
            estado_actual = "FASE 1 — ACOGIDA"
        elif session_mode == 'PHASE_2_AUDIO':
            estado_actual = "FASE 3 — CIERRE Y COBRO (El audio ya fue enviado de forma exitosa. No debes volver a proponerlo ni enviarlo. Ahora debes resolver sus dudas y cerrarle preguntando si desea el enlace seguro de pago de Stripe para iniciar su proceso)"
        elif session_mode == 'PHASE_3_COBRO':
            estado_actual = "FASE 3 — CIERRE Y COBRO (El enlace de pago ya fue enviado de forma exitosa. Resuelve sus dudas técnicas o de pago y guíalo a completar su pago para poder habilitar la agenda)"
            
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
  - PASO 1: Cuando el usuario haya definido completamente una fecha y hora específicas (ej. "Martes 9 de junio a las 10:00 AM"), confírmala y solicita su Nombre completo y Correo electrónico. ESPERA SU RESPUESTA. No avances al paso 2. NUNCA llames a 'book_appointment' todavía ni uses placeholders como '[Pendiente]'.
  - PASO 2: UNA VEZ que el usuario haya escrito su nombre y correo, muestra el resumen exacto: "Confirmemos tus datos: Cita para el [Fecha] a las [Hora], Nombre: [Nombre], Correo: [Correo]. ¿Son correctos estos datos?" ESPERA SU RESPUESTA.
  - PASO 3: SOLO cuando el usuario confirme explícitamente que los datos son correctos (ej: "sí", "son correctos"), invoca la herramienta 'book_appointment'. Si hay errores, pide las correcciones y vuelve al PASO 2. NUNCA llames a la herramienta antes de esta confirmación explícita del usuario.
- PREVENCIÓN DE DESFASE: Al invocar 'book_appointment' con éxito, el sistema enviará la confirmación en segundo plano. En ese turno, tu respuesta (`reply`) DEBE ser exactamente: `[AGENDA_COMPLETA]`. No agregues otro texto.

PREGUNTAS FRECUENTES Y DESVÍOS (RESPONDE CON AUTORIDAD, LUEGO REDIRIGE):
- "¿Qué es la quiromancia?" → "La quiromancia popular es interpretación subjetiva. Aquí trabajamos con otra cosa: analizamos la morfología dérmica y los dermatoglifos como registros objetivos del sistema nervioso, en línea con el Hasta Samudrika Shastra pero interpretados desde las ciencias del comportamiento. No es adivinación, es decodificación. ¿Te comparto el audio explicativo?"
- "¿Cuánto cuesta?" → "El proceso tiene un valor de 49 USD. ¿Te gustaría conocer en detalle qué incluye antes de decidir?"
- "¿Cómo funciona?" → Ofrece el audio directamente.
- "¿Qué estudios tiene Orus?" → Activa el bloque QUIÊN ES ORUS PEÑA y redirige al audio.
- "¿Están en Brasil?" → "Sí, operamos desde Brasil. Las sesiones son en línea, el acceso es global."
- Preguntas sobre neuroanatomía, comportamiento humano o Hasta Samudrika Shastra → Responde con síntesis técnica concisa que demuestre autoridad, luego: "Ese es el marco que aplicamos en la Auditoría. El audio de 3 minutos detalla cómo se articula en la práctica. ¿Lo escuchas ahora?"
- "¿Qué es el Hasta Samudrika Shastra?" → "Es el sistema clásico védico de análisis de la mano — uno de los más rigurosos en cuanto a correspondencia entre morfología física y patrón conductual. En el taller lo usamos como base, reinterpretado a través del lenguaje de la neurociencia moderna. ¿Te comparto el audio donde Orus detalla la metodología completa?"
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

    # Traducir historial a formato de OpenRouter/OpenAI (todo en texto plano)
    messages = [{"role": "system", "content": system_rules}]
    
    if history:
        for msg in history:
            msg_text = msg["text"]
            role = "assistant" if msg["role"] == "model" else "user"
            
            # Si el texto ya viene formateado en JSON por alguna razón, extraemos el reply
            if msg_text.strip().startswith("{"):
                try:
                    parsed = json.loads(msg_text)
                    msg_text = parsed.get("reply", msg_text)
                except Exception:
                    pass
                
            messages.append({"role": role, "content": msg_text})

    # Traducir multimedia adjunto
    user_content_parts = []
    if media:
        # Si el modelo soporta multimedia (ej: Gemini), enviamos los archivos
        is_multimodal = "gemini" in OPENROUTER_MODEL.lower() or "claude" in OPENROUTER_MODEL.lower()
        
        for i, m in enumerate(media):
            media_type = m["media_type"]
            mime = m["mime_type"]
            b64_data = base64.b64encode(m["bytes"]).decode("utf-8")
            
            if is_multimodal:
                if "image" in mime or media_type == "image":
                    user_content_parts.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{b64_data}"
                        }
                    })
                elif "audio" in mime or media_type == "audio":
                    # Nota de voz / Audio
                    ext = "mp3" if "mp3" in mime else ("ogg" if "ogg" in mime else "wav")
                    user_content_parts.append({
                        "type": "input_audio",
                        "input_audio": {
                            "data": b64_data,
                            "format": ext
                        }
                    })
            else:
                # Si es un modelo de texto únicamente (ej: DeepSeek), agregamos un marcador descriptivo en texto
                desc = f"[Adjunto {i+1}: {media_type.upper()} recibido por WhatsApp]"
                user_content_parts.append({"type": "text", "text": desc})

    # Agregar el prompt final
    user_content_parts.append({"type": "text", "text": prompt})
    messages.append({"role": "user", "content": user_content_parts})

    # Bucle de llamadas a herramientas (max 5 turnos)
    max_turns = 5
    last_executed_tool = None
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://api.orusquiroterapia.online",
        "X-Title": "Orus Quiroterapia Bot",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=60.0) as http_client:
        for turn in range(max_turns):
            payload = {
                "model": OPENROUTER_MODEL,
                "messages": messages,
                "tools": OPENAI_TOOLS,
                "tool_choice": "auto",
                "max_tokens": 1000
            }
            
            # Forzar formato JSON en modelos compatibles
            if "deepseek" in OPENROUTER_MODEL.lower() or "gpt" in OPENROUTER_MODEL.lower():
                payload["response_format"] = {"type": "json_object"}
                
            print(f"[OpenRouter] Enviando solicitud a {OPENROUTER_MODEL} (Turno {turn + 1})...", flush=True)
            
            # Bucle de reintento ante respuestas truncadas
            attempts = 2
            content = ""
            tool_calls = []
            
            for attempt in range(attempts):
                r = await http_client.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
                
                if r.status_code != 200:
                    err_text = r.text
                    print(f"[OpenRouter Error] Status {r.status_code}: {err_text}", flush=True)
                    raise Exception(f"OpenRouter API error: {err_text}")
                    
                res_data = r.json()
                choice = res_data["choices"][0]
                message_res = choice["message"]
                content = message_res.get("content") or ""
                tool_calls = message_res.get("tool_calls") or []
                
                # Si hay llamadas a herramientas, omitimos validación de truncamiento y salimos
                if tool_calls:
                    break
                    
                # Validar si el JSON final está truncado
                raw_text = content.strip()
                is_truncated = False
                
                # Criterio de truncamiento: comienza con { o tiene marcas de JSON pero no cierra con }
                if raw_text.startswith("{") and not raw_text.endswith("}"):
                    is_truncated = True
                elif not raw_text.startswith("{") and not raw_text.endswith("}"):
                    if '"reply":' in raw_text or '"sentiment":' in raw_text:
                        is_truncated = True
                        
                if is_truncated and attempt < attempts - 1:
                    print(f"[OpenRouter Warning] Respuesta truncada detectada (Intento {attempt + 1}/{attempts}). Reintentando con alerta de concisión...", flush=True)
                    print(f"[OpenRouter DEBUG Truncado] Content: {raw_text}", flush=True)
                    
                    # Inyectar instrucción de concisión en el último mensaje de usuario
                    for msg in reversed(payload["messages"]):
                        if msg["role"] == "user":
                            if isinstance(msg["content"], list):
                                for part in msg["content"]:
                                    if part.get("type") == "text":
                                        part["text"] += "\n\n[SISTEMA - ALERTA]: Tu respuesta anterior fue cortada por el límite de caracteres. Por favor, genera la respuesta de nuevo, sé mucho más conciso para asegurar que quepa completa y con formato JSON válido."
                            else:
                                msg["content"] += "\n\n[SISTEMA - ALERTA]: Tu respuesta anterior fue cortada por el límite de caracteres. Por favor, genera la respuesta de nuevo, sé mucho más conciso para asegurar que quepa completa y con formato JSON válido."
                            break
                    # Volver a llamar en la siguiente iteración
                    continue
                else:
                    break
            
            print(f"[OpenRouter DEBUG] Content: {content}", flush=True)
            if tool_calls:
                print(f"[OpenRouter DEBUG] Tool calls: {tool_calls}", flush=True)
                
            # Si no hay llamadas a herramientas, procesamos el texto final
            if not tool_calls:
                raw_text = content.strip()
                
                # Blindaje antierosivo
                if not raw_text:
                    fallback_token = "[SILENT_FALLBACK]"
                    if last_executed_tool:
                        print(f"[OpenRouter] Respuesta vacía tras herramienta '{last_executed_tool}'. Aplicando blindaje.", flush=True)
                        if last_executed_tool == "send_introductory_audio":
                            fallback_token = "[AUDIO_ENVIADO]"
                        elif last_executed_tool == "generate_payment_link":
                            fallback_token = "[COBRO_ENVIADO]"
                        elif last_executed_tool == "book_appointment":
                            fallback_token = "[AGENDA_COMPLETA]"
                    else:
                        print("[OpenRouter] Respuesta vacía sin herramienta ejecutada. SILENT_FALLBACK.", flush=True)

                    return {
                        "reply": f"{fallback_token} [##EOS##]",
                        "sentiment": "Neutral",
                        "requires_human": False
                    }
                
                # Limpiar Markdown
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                    parsed_json = None
                try:
                    parsed_json = json.loads(raw_text.strip())
                except Exception as json_err:
                    print(f"[OpenRouter] JSON estándar falló ({json_err}). Intentando parseador robusto...", flush=True)
                    # Intentar extraer campos manualmente
                    reply_content = None
                    sentiment_content = "Neutral"
                    requires_human_content = True
                    
                    # Buscar reply
                    reply_start_marker = '"reply":'
                    if reply_start_marker not in raw_text:
                        reply_start_marker = "'reply':"
                        
                    if reply_start_marker in raw_text:
                        idx = raw_text.find(reply_start_marker)
                        val_start = raw_text.find('"', idx + len(reply_start_marker))
                        if val_start == -1:
                            val_start = raw_text.find("'", idx + len(reply_start_marker))
                        if val_start != -1:
                            sent_marker_pos = -1
                            for marker in ['"sentiment"', "'sentiment'", '"requires_human"', "'requires_human'"]:
                                pos = raw_text.rfind(marker)
                                if pos > val_start:
                                    sent_marker_pos = pos
                                    break
                            
                            if sent_marker_pos != -1:
                                sub = raw_text[val_start+1:sent_marker_pos].strip()
                                if sub.endswith(','):
                                    sub = sub[:-1].strip()
                                if sub.endswith('"') or sub.endswith("'"):
                                    sub = sub[:-1]
                                reply_content = sub
                            else:
                                sub = raw_text[val_start+1:].strip()
                                if sub.endswith('}'):
                                    sub = sub[:-1].strip()
                                if sub.endswith('"') or sub.endswith("'"):
                                    sub = sub[:-1]
                                reply_content = sub

                    # Buscar sentiment
                    for marker in ['"sentiment"', "'sentiment'"]:
                        if marker in raw_text:
                            idx = raw_text.find(marker)
                            val_start = raw_text.find('"', idx + len(marker))
                            if val_start == -1:
                                val_start = raw_text.find("'", idx + len(marker))
                            if val_start != -1:
                                quote_char = raw_text[val_start]
                                next_comma = raw_text.find(',', val_start)
                                next_brace = raw_text.find('}', val_start)
                                limit = min(next_comma if next_comma != -1 else len(raw_text), next_brace if next_brace != -1 else len(raw_text))
                                val_end = raw_text.find(quote_char, val_start + 1, limit)
                                if val_end != -1:
                                    sentiment_content = raw_text[val_start+1:val_end]
                                else:
                                    sentiment_content = raw_text[val_start+1:limit].strip().replace('"', '').replace("'", "")

                    # Buscar requires_human
                    for marker in ['"requires_human"', "'requires_human'"]:
                        if marker in raw_text:
                            idx = raw_text.find(marker)
                            colon_idx = raw_text.find(':', idx)
                            if colon_idx != -1:
                                sub = raw_text[colon_idx+1:].strip().lower()
                                if 'true' in sub:
                                    requires_human_content = True
                                elif 'false' in sub:
                                    requires_human_content = False

                    if reply_content is not None:
                        parsed_json = {
                            "reply": reply_content,
                            "sentiment": sentiment_content,
                            "requires_human": requires_human_content
                        }
                    else:
                        if not raw_text.startswith("{"):
                            cleaned_reply = raw_text.strip()
                            for marker in [', "sentiment"', ",'sentiment'", ', "requires_human"', ",'requires_human'"]:
                                pos = cleaned_reply.rfind(marker)
                                if pos != -1:
                                    cleaned_reply = cleaned_reply[:pos].strip()
                            if cleaned_reply.endswith('"') or cleaned_reply.endswith("'"):
                                cleaned_reply = cleaned_reply[:-1]
                            parsed_json = {
                                "reply": cleaned_reply,
                                "sentiment": sentiment_content,
                                "requires_human": requires_human_content
                            }
                    if parsed_json is not None:
                        parsed_json["requires_human"] = True

                try:
                    if parsed_json is None:
                        raise Exception("No se pudo estructurar ni reparar la respuesta.")

                    if not parsed_json.get("reply", "").endswith("[##EOS##]"):
                        parsed_json["reply"] = parsed_json.get("reply", "") + " [##EOS##]"
                    
                    # Ejecutar safety net
                    import re
                    jid_match = re.search(r'JID=([^\]\s]+)', prompt)
                    to_number = jid_match.group(1) if jid_match else None
                    if to_number:
                        reply_str = parsed_json.get("reply", "")
                        if "[AUDIO_ENVIADO]" in reply_str and last_executed_tool != "send_introductory_audio":
                            print(f"[Safety Net] LLM omitió llamada a send_introductory_audio pero devolvió [AUDIO_ENVIADO]. Ejecutando herramienta programáticamente.", flush=True)
                            try:
                                await send_introductory_audio(to_number)
                                last_executed_tool = "send_introductory_audio"
                            except Exception as ex:
                                print(f"[Safety Net Error] Al ejecutar send_introductory_audio: {ex}", flush=True)
                        elif "[COBRO_ENVIADO]" in reply_str and last_executed_tool != "generate_payment_link":
                            print(f"[Safety Net] LLM omitió llamada a generate_payment_link pero devolvió [COBRO_ENVIADO]. Ejecutando herramienta programáticamente.", flush=True)
                            try:
                                await generate_payment_link(to_number)
                                last_executed_tool = "generate_payment_link"
                            except Exception as ex:
                                print(f"[Safety Net Error] Al ejecutar generate_payment_link: {ex}", flush=True)

                    return parsed_json
                except Exception as e:
                    print(f"[OpenRouter] Error final procesando/reparando JSON: {e}\nRaw: {raw_text}", flush=True)
                    return {
                        "reply": "Lo siento, tuve un error interno procesando la respuesta. [##EOS##]",
                        "sentiment": "Neutral",
                        "requires_human": True
                    }

            # Procesar llamadas a herramientas
            print(f"[OpenRouter] Procesando {len(tool_calls)} llamadas a herramientas...", flush=True)
            
            # OpenAI requiere que agreguemos la respuesta del asistente que incluye los tool_calls
            messages.append(message_res)
            
            for tc in tool_calls:
                tc_id = tc["id"]
                tool_name = tc["function"]["name"]
                args_str = tc["function"]["arguments"]
                
                try:
                    args = json.loads(args_str)
                except Exception:
                    args = {}
                    
                if tool_name in available_tools:
                    print(f"[Tool] Ejecutando {tool_name} con {args}", flush=True)
                    last_executed_tool = tool_name
                    try:
                        func = available_tools[tool_name]
                        import inspect
                        if inspect.iscoroutinefunction(func):
                            result = await func(**args)
                        else:
                            result = func(**args)
                    except Exception as te:
                        print(f"[Tool Error] {te}", flush=True)
                        result = f"Error: {str(te)}"
                else:
                    result = f"Error: Tool {tool_name} not found"
                
                # Agregar la respuesta del tool al historial
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "name": tool_name,
                    "content": str(result)
                })
                
        return {
            "reply": "Lo siento, me quedé atrapado en un bucle de tareas de OpenRouter. [##EOS##]",
            "sentiment": "Confusión",
            "requires_human": True
        }
