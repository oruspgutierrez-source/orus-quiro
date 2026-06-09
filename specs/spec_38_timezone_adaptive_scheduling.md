# Spec 38: Sistema de Agendamiento Adaptativo por Zona Horaria e Interceptor Determinista

Este documento especifica la arquitectura del nuevo motor de agendamiento para el bot de Orus Quiro. El objetivo principal es internacionalizar el embudo, permitiendo que personas de diferentes países (como España y LATAM) agenden en su hora local de forma 100% infalible, delegando el flujo de reserva a un interceptor determinista en el backend en lugar de confiar en el razonamiento del modelo de lenguaje.

---

## 1. Modificaciones al Esquema de Base de Datos (Supabase)

Para persistir la localización del usuario y evitar llamadas repetidas a la API de Google Calendar en cada interacción, se deben añadir las siguientes columnas a la tabla `orus_users`:

```sql
-- Agregar columnas de localización y zona horaria
ALTER TABLE orus_users ADD COLUMN IF NOT EXISTS country VARCHAR(100);
ALTER TABLE orus_users ADD COLUMN IF NOT EXISTS timezone VARCHAR(100) DEFAULT 'America/Bogota';

-- Agregar columna para cachear slots del calendario en formato JSON
-- Formato: { "2026-06-12": [10, 11, 15, 16], "2026-06-15": [9, 10] }
ALTER TABLE orus_users ADD COLUMN IF NOT EXISTS cached_slots JSONB DEFAULT '{}'::jsonb;
```

---

## 2. Motor de Localización (Timezone Engine)

### 2.1 Confirmación Conversacional y Registro de País
Al recibir la confirmación de pago del webhook de Stripe:
1.  Se establece `payment_status = 'paid'`.
2.  El bot envía de forma inmediata el mensaje de saludo inicial pospago:
    > *"¡Muchas gracias por tu pago! Para mostrarte la agenda de citas en tu zona horaria local, confírmame por favor en qué país te encuentras actualmente."*
3.  El usuario responderá libremente en el chat. Un interceptor determinista (ej. buscando concordancias como "españa", "colombia", "méxico", "mexico", "chile", "peru", "ecuador", "argentina") registrará el país en `orus_users.country` y guardará la correspondiente zona horaria IANA en `orus_users.timezone`:

```python
COUNTRY_TIMEZONE_MAP = {
    "españa": "Europe/Madrid",
    "espana": "Europe/Madrid",
    "colombia": "America/Bogota",
    "méxico": "America/Mexico_City",
    "mexico": "America/Mexico_City",
    "perú": "America/Lima",
    "peru": "America/Lima",
    "ecuador": "America/Guayaquil",
    "chile": "America/Santiago",
    "argentina": "America/Argentina/Buenos_Aires",
    "uruguay": "America/Montevideo",
    "venezuela": "America/Caracas",
    "bolivia": "America/La_Paz",
}
```

4.  Una vez registrada la zona horaria, el sistema calcula los horarios disponibles del terapeuta en esa zona horaria y los almacena en `cached_slots` para presentárselos al usuario.

---

## 3. Algoritmo de Solapamiento y Definición de Horarios

El terapeuta Orus Peña atiende en la zona horaria **America/Sao_Paulo (UTC-3)** bajo el siguiente esquema:
*   **Días Laborales**: Lunes a Sábados.
*   **Horas de Atención**: 8:00 AM a 9:00 PM (21:00) hora de Brasil.
*   **Bloques de Descanso Excluidos (Hora de Inicio)**:
    *   `12:00` (Bloque de almuerzo: 12:00 PM - 1:00 PM).
    *   `14:00` (Bloque de descanso vespertino: 2:00 PM - 3:00 PM).
*   **Horarios Disponibles Teóricos (Hora de inicio en Brasil)**:
    `08:00`, `09:00`, `10:00`, `11:00`, `13:00`, `15:00`, `16:00`, `17:00`, `18:00`, `19:00`, `20:00`.

### Lógica de Conversión y Filtro por País
El motor de reservas tomará los slots teóricos libres del calendario de Google (en formato UTC) y los convertirá a la hora del cliente (`user_timezone`). Para asegurar una excelente experiencia de usuario, se aplicará el siguiente filtro adaptativo de visualización local:

*   **Filtro para España (`Europe/Madrid`)**: Se ocultarán las citas que en hora local de España resulten ser posteriores a las **10:00 PM** (para evitar reservas de madrugada), a menos que el cliente solicite explícitamente un espacio tardío.
*   **Filtro para México/Colombia (`America/Mexico_City`, `America/Bogota`)**: Se ocultarán las citas que en hora local resulten ser anteriores a las **7:00 AM** (para evitar citas de madrugada para el consultante).

---

## 4. Interceptor Determinista de Agendamiento (Bypass de LLM)

En `api/services/message_processor.py`, se implementará un validador de flujo antes de enviar el mensaje al LLM. Si `payment_status == 'paid'` y el usuario no tiene cita agendada (`appointment_date` es nulo):

### 4.1 Captura de Intención de Fecha y Hora (Regex Interceptor)
El interceptor intentará extraer el día y la hora de la respuesta del usuario mediante expresiones regulares y concordancia semántica (ej. buscar nombres de días "lunes", "martes", "viernes", "sábado" y números de hora "9 am", "15:00", "5 de la tarde").

*   **Caso A: El usuario menciona solo un Día (Sin Hora)**
    1.  Buscar el día en `cached_slots`.
    2.  Si existen horarios libres en `cached_slots` para ese día, formatear una lista amigable indicando la hora del cliente (por ejemplo, mañana/tarde/noche).
    3.  Responder directamente:
        > *"Para el [Día Seleccionado], estos son los horarios disponibles en tu hora local ([Huso Horario]):\n\n[Horarios Libres]\n\n¿Cuál de estos te conviene?"*
    4.  Finalizar el turno conversacional **sin llamar al LLM**.

*   **Caso B: El usuario menciona Día y Hora**
    1.  Verificar si la hora solicitada se encuentra libre en `cached_slots` para ese día (considerando tolerancia de +/- 30 minutos).
    2.  **Si está disponible:**
        *   Registrar la selección en la base de datos de manera temporal.
        *   Responder directamente iniciando la recolección de los datos de contacto:
            > *"Perfecto. Reservaremos provisionalmente el [Día] a las [Hora] (hora de [País]). Para completar la reserva en mi sistema, indícame por favor tu Nombre Completo."*
    3.  **Si no está disponible:**
        *   Responder directamente:
            > *"El horario [Hora] no está disponible para el [Día] en tu zona horaria. Para ese día tengo libres los siguientes horarios:\n\n[Horarios Libres]\n\nPor favor, selecciona uno de ellos."*
    4.  Finalizar el turno conversacional **sin llamar al LLM**.

*   **Caso C: Consultas Generales u Objeciones**
    *   Si no se detectan patrones de fecha o confirmación, el mensaje se envía a Gemini.
    *   Gemini responderá la duda del usuario, pero las reglas del sistema (System Instructions) le obligarán a adjuntar siempre un recordatorio con la llamada a la acción (CTA) de agendamiento y los días disponibles almacenados en caché.
