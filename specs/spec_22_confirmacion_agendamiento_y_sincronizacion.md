# Spec 22 — Confirmación de Agendamiento y Sincronización Post-Reserva

## Objetivo
Resolver el desfase de mensajes (condición de carrera) entre la respuesta de Gemini y la subrutina asíncrona de envío visual de Calendar, e introducir un paso de confirmación humana ("human in the loop") antes de insertar la cita en Google Calendar.

## Problema Actual (Desfase)
Actualmente, tan pronto el consultante proporciona su nombre y correo, Gemini ejecuta la herramienta `book_appointment()`. Esta herramienta:
1. Dispara en segundo plano `send_visual_agenda_protocol()` (que envía instantáneamente "Tu sesion ha sido agendada con exito", imágenes y enlaces, con delays cortos).
2. Devuelve un texto de éxito a Gemini.
Gemini entonces procesa ese texto y genera su propia respuesta ("Tu cita para la Auditoría... ha sido agendada... Hemos enviado un instructivo...").
Como Gemini tarda unos segundos en pensar y generar esta respuesta final, su mensaje llega DESPUÉS de que el sistema ya envió los enlaces, generando un desfase cognitivo y repetición de confirmaciones.

## Nuevo Flujo Deseado
1. El usuario elige día y hora.
2. Gemini solicita Nombre y Correo.
3. El usuario envía Nombre y Correo.
4. **NUEVO PASO:** Gemini presenta un resumen ("Confirmado para el [Fecha] a las [Hora]. Datos: [Nombre], [Correo]. ¿Son correctos?") y **espera** a que el usuario diga "Sí" o realice correcciones.
5. Una vez el usuario confirma explícitamente, Gemini invoca `book_appointment()`.
6. El sistema enruta la solicitud a Google Calendar y activa las instrucciones visuales.
7. Para evitar el desfase de la respuesta de Gemini con los mensajes asíncronos, Gemini generará un mensaje oculto (ej: `[AGENDA_COMPLETA]`) que el servidor backend interceptará y descartará de forma silenciosa para que únicamente se envíen los mensajes oficiales preprogramados en el sistema (imagen, calendar link, biometrics link).

## Plan de Implementación (Execute)

### Task 22.1 — Modificar el System Prompt en `gemini_client.py`
- Actualizar la `FASE 4 — AGENDAMIENTO`.
- Instruir a Gemini para que repita los datos capturados y pida confirmación afirmativa del usuario ANTES de llamar a `book_appointment`.
- Instruir a Gemini para que, tras invocar `book_appointment` con éxito, su campo de respuesta (`reply`) diga única y exactamente la cadena `[AGENDA_COMPLETA]` para delegar la comunicación final al sistema.

### Task 22.2 — Intercepción de Respuesta Silenciosa en `message_processor.py`
- En el bloque de fragmentación y envío (alrededor de la línea 305 en `_process_buffer`), detectar si la respuesta limpia (`reply_clean`) contiene la palabra clave `[AGENDA_COMPLETA]`.
- Si la detecta, hacer un `return` temprano para evitar que se envíe ese mensaje al consultante por WhatsApp, permitiendo que `send_visual_agenda_protocol` sea el único remitente ordenado.

### Task 22.3 — Validar Tiempos (Delays) en `calendar_client.py`
- Asegurarse de que el primer mensaje de la secuencia (`Tu sesion ha sido agendada con exito...`) funcione perfectamente como el punto de cierre de la reserva sin textos adicionales alrededor.

## Impacto
- Mejora drástica de la experiencia del usuario (cero desfases, cero mensajes cruzados).
- Seguridad adicional al requerir validación explícita del correo electrónico y nombre antes de interactuar con la API de Google.
