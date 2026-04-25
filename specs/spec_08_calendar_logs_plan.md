# Spec 08: Integración Modular (Calendar, Logs y Métricas)

Este documento contiene el plan de arquitectura para extender las capacidades del ecosistema Orus, preparado bajo el protocolo **REPORT_ONLY**. No se ejecutará código hasta la aprobación explícita.

---

## 1. Evolución de Base de Datos (Supabase)

### 1.1 Actualización de la Tabla `orus_users`
Para soportar el ciclo de ventas y agendamiento, se ampliará el esquema actual mediante:
```sql
-- DDL Propuesto (No ejecutar en fase de R&D)
ALTER TABLE orus_users 
ADD COLUMN payment_status VARCHAR(20) DEFAULT 'pendiente',
ADD COLUMN appointment_date TIMESTAMP WITH TIME ZONE,
ADD COLUMN total_spent NUMERIC(10,2) DEFAULT 0.00;
```
*Impacto:* Permite que el Dashboard visualice clientes de alto valor e identifique rápidamente quiénes tienen citas próximas.

### 1.2 Nueva Tabla: `orus_logs` (Registro de Errores)
Diseñada para telemetría profunda. Reemplazará los simples `print()` del servidor por un registro centralizado.
```sql
-- DDL Propuesto (No ejecutar en fase de R&D)
CREATE TABLE orus_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```
*Impacto:* En el código, se integrará un manejador global de excepciones en FastAPI (o dentro de los bloques `try/except` de `orchestrator.py` y `webhooks.py`) para hacer un `INSERT` a esta tabla.

---

## 2. Integración de Google Calendar (Function Calling)

Para dotar a Orus de la capacidad de agendar, la estrategia no es hacer que el código revise fechas rígidamente, sino otorgarle "Herramientas" (Tools) al propio LLM.

### 2.1 Herramientas (Tools) de Gemini
Utilizaremos el soporte nativo de Google GenAI para declarar funciones que Orus podrá invocar:
1. `check_free_slots(start_date, end_date)`: Consulta a la API de Calendar y le devuelve a Orus los espacios disponibles en texto plano.
2. `book_appointment(phone_number, date_time, name)`: Escribe un evento en Google Calendar usando la cuenta de servicio del quiromante.

### 2.2 Flujo de Datos
- **Paso 1:** Cliente pide "Quiero una cita el viernes".
- **Paso 2:** Gemini decide invocar `check_free_slots`.
- **Paso 3:** FastAPI intercepta la petición, llama a la API de Google Calendar usando las credenciales (`credentials.json`), obtiene los horarios y se los inyecta de vuelta al prompt.
- **Paso 4:** Gemini formula su respuesta ("Tengo libre el viernes a las 10am o 4pm. ¿Cuál prefieres?").
- **Paso 5:** Si el cliente acepta, Gemini llama a `book_appointment`. FastAPI registra la cita en Calendar y actualiza `appointment_date` en Supabase.

### 2.3 Requisitos Técnicos
- Instalar `google-api-python-client` y `google-auth`.
- Generar una Service Account de Google Cloud y descargar el JSON de credenciales de Calendar.

---

## 3. Lógica de Métricas (Dashboard API)

Se agregará un nuevo endpoint al enrutador `dashboard.py`.

### 3.1 Endpoint de Cálculo
`GET /api/metrics/bot_vs_human`

### 3.2 Lógica Interna
En lugar de iterar objetos en Python, se aprovechará el motor de PostgreSQL (Supabase) para hacer un cálculo veloz:
```python
# Pseudo-código de backend
response = supabase.table('orus_users').select('session_mode').execute()
# Agrupamos cuántos tienen 'AI' y cuántos 'HUMAN'
# Devolvemos un JSON:
{
    "total_users": 150,
    "ai_managed": 120,
    "human_managed": 30,
    "human_intervention_rate": "20.0%"
}
```
Esto permitirá al Frontend renderizar gráficas de torta (Pie Charts) instantáneas para monitorear la saturación humana.
