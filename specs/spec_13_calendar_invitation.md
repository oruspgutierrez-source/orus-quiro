# Spec 13 — Invitación de Google Calendar y Flujo de Confirmación de Datos

**Fecha:** 2026-05-19
**Estado:** 📋 Borrador — Pendiente de aprobación
**Autor:** Agente Antigravity
**Prioridad:** 🔴 Alta — Mejora de experiencia de usuario y flujo de datos

---

## 1. Contexto y Problema

Actualmente, cuando el usuario agenda una cita en el bot de Orus Quiro:
1. El bot le responde en el chat de WhatsApp enviando un enlace directo a Google Calendar (`htmlLink`).
2. El usuario debe abrir ese enlace para ver el evento en su propio calendario y guardarlo. Esto no es ideal, ya que interrumpe el flujo y depende de que el usuario tome acción manual en un navegador móvil.
3. No se solicita obligatoriamente el correo electrónico del cliente durante el proceso.
4. No existe una etapa de confirmación de datos previa al agendamiento final; la cita se crea de inmediato al elegir el horario, lo que puede causar errores en el nombre, teléfono o el horario si el usuario cambia de parecer en el último instante.

El usuario ha solicitado:
- **Eliminar el enlace HTML** de calendar en el chat de WhatsApp.
- **Pedir todos los datos al cliente obligatoriamente, incluyendo el correo electrónico** (`email`).
- **Implementar una fase de confirmación previa**: Tras recibir los datos, el bot enviará un resumen al usuario y le preguntará si están correctos.
- **Flujo de decisión en el chat**:
  - Si responde **sí** -> El bot procede a crear la cita (`book_appointment`) y enviar el mensaje de confirmación de éxito. Al crear la cita, Google Calendar enviará automáticamente la invitación formal al correo electrónico del cliente (añadiéndolo como `attendee`).
  - Si envía **correcciones** -> El bot edita los datos correspondientes, vuelve a mostrar el resumen actualizado y pregunta nuevamente si están correctos, repitiendo el proceso hasta recibir la confirmación afirmativa del cliente.

---

## 2. Archivos Impactados

| Archivo | Tipo de cambio | Razón |
|---|---|---|
| `api/services/calendar_client.py` | MODIFICAR | Añadir parámetro `email` a `book_appointment()`, configurar al cliente como `attendee` en el payload de Google Calendar con `sendUpdates='all'`, y cambiar el retorno por un mensaje amigable sin `htmlLink`. |
| `api/services/gemini_client.py` | MODIFICAR | Reestructurar la sección `FLUJO DE AGENDAMIENTO (OBLIGATORIO)` del `system_rules` para guiar a Gemini a través de la recolección de datos (incluyendo email obligatorio), la fase de confirmación interactiva, y el control de correcciones. |
| `bitacoras/backend_log.md` | ACTUALIZAR | Registrar los detalles y decisiones de implementación técnica de la API de Google Calendar y envío de invitaciones automáticas. |
| `bitacoras/agents_log.md` | ACTUALIZAR | Registrar cómo se modificó el system prompt para que el LLM sostenga el estado de confirmación e interprete correcciones antes de invocar la herramienta. |
| `bitacoras/BITACORA_SESION.md` | ACTUALIZAR | Reflejar la compleción del Spec 13 y el estado del pipeline. |

---

## 3. Tasks Atómicos

### Task 1 — Actualizar `book_appointment` en `calendar_client.py`
- **Qué:** Modificar la firma y la lógica interna de `book_appointment(phone_number: str, date_time: str, name: str)` para admitir un parámetro obligatorio `email: str`.
- **Implementación:**
  - En el cuerpo del evento enviado a Google Calendar, añadir el campo `attendees`:
    ```python
    'attendees': [{'email': email}]
    ```
  - En la llamada `.insert(calendarId=CALENDAR_ID, body=event)`, agregar el argumento `sendUpdates='all'` para forzar que Google envíe el correo electrónico de invitación formal con el archivo `.ics` de forma automática.
  - Modificar el string de retorno de `book_appointment`. En lugar de devolver `f"Cita agendada exitosamente: {event_res.get('htmlLink')}"`, retornar una confirmación amigable:
    ```python
    f"Cita agendada exitosamente para el {date_time} a nombre de {name}. Se ha enviado una invitacion formal al correo {email}."
    ```
- **Criterio de aceptación:** La firma de la función acepta `email`, crea el evento en Google Calendar con el attendee correspondiente, y no retorna la URL pública del evento en el chat.

### Task 2 — Reestructurar el system_rules en `gemini_client.py`
- **Qué:** Actualizar las reglas del sistema de Gemini para definir rigurosamente la secuencia de recopilación de datos y confirmación del agendamiento.
- **Implementación:**
  - Modificar la sección `FLUJO DE AGENDAMIENTO (OBLIGATORIO)` para instruir a Gemini en los siguientes pasos exactos:
    1. **Disponibilidad:** Invocar `check_free_slots()` ante cualquier solicitud de agendamiento y mostrar los horarios disponibles.
    2. **Recopilación:** Cuando el usuario elija un horario, solicitar de forma profesional:
       - Nombre completo
       - Teléfono (confirmar el que está usando o solicitar uno nuevo si aplica)
       - **Correo electrónico** (indicarle al usuario que es indispensable para enviarle su invitación de Google Calendar).
    3. **Resumen de confirmación:** Una vez que tengas todos los datos (nombre, teléfono, email, horario de la cita), **NUNCA** invoques `book_appointment()` de inmediato. Envía un mensaje estructurado resumiendo la información y pregunta directamente: "¿Son correctos estos datos?".
    4. **Aprobación (Sí):** Si el usuario responde afirmativamente ("sí", "es correcto", "dale", etc.), invoca la herramienta `book_appointment()` con los datos confirmados y responde de forma sobria y profesional.
    5. **Correcciones (No / Cambios):** Si el usuario proporciona alguna corrección (ej. "el correo es x@y.com", "es a las 10:00, no a las 11:00", "escribiste mal mi nombre"), edita los datos correspondientes en el flujo de conversación, presenta el resumen actualizado y vuelve a preguntar "¿Son correctos estos datos?", repitiendo este paso hasta obtener un "sí" definitivo.
- **Criterio de aceptación:** El system prompt instruye detalladamente la retención del estado de confirmación, la obligatoriedad del correo electrónico, y prohíbe explícitamente llamar a `book_appointment()` antes de la confirmación explícita del usuario.

### Task 3 — Validación y Pruebas Unitarias/Simuladas
- **Qué:** Crear un script de prueba rápida `test_calendar_invitation.py` en `scratch/` para verificar el envío de invitaciones y comprobar que la API de Google responde correctamente enviando el correo.
- **Criterio de aceptación:** Ejecución exitosa de la creación del evento con attendees reales y verificación de la recepción del correo de invitación.

### Task 4 — Registro de Trazabilidad y Bitácoras
- **Qué:** Documentar los cambios en `bitacoras/backend_log.md`, `bitacoras/agents_log.md` y `bitacoras/BITACORA_SESION.md`.
- **Criterio de aceptación:** Las bitácoras reflejan exactamente los commits, el diseño del prompt de dos fases con confirmación y el parámetro de attendees.

---

## 4. Orden de Ejecución

```
Task 1 (Calendar Backend) ──> Task 2 (Gemini Rules) ──> Task 3 (Test E2E / Simulación) ──> Task 4 (Logs & Bitácoras)
```

---

## 5. Criterio de Éxito Global

1. El usuario inicia el flujo de agendamiento.
2. El bot muestra los horarios disponibles tras llamar a `check_free_slots()`.
3. El usuario elige un horario, y el bot le solicita obligatoriamente Nombre, Teléfono y Correo Electrónico.
4. El bot presenta un resumen del agendamiento y pregunta si los datos son correctos.
5. Si el usuario corrige algo, el bot edita los datos y vuelve a resumir.
6. Si el usuario dice "sí", el bot ejecuta `book_appointment()` en segundo plano enviando el correo del cliente como `attendee` con `sendUpdates='all'`.
7. El bot responde con un mensaje amigable y profesional de confirmación sin enlaces crudos de calendar.
8. El cliente recibe la invitación de Google Calendar en su correo electrónico.
