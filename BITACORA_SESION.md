# BITACORA_SESION.md - Continuidad del Proyecto Orus Quiro

## Última Actualización
**Fecha y Hora:** 2026-04-25T14:39:00-03:00

## Estado Actual del Proyecto
El ecosistema Orus Quiro ha evolucionado de un chatbot simple a una plataforma operativa completa con memoria persistente, análisis de sentimiento, alertas de crisis, agendamiento automatizado por IA, y endpoints de métricas para un futuro Dashboard visual.

### Specs Completados (Fase de Ejecución Finalizada):
1. **Spec 01 (Core Backend):** FastAPI inicializado con validación de tokens de Webhook de Meta.
2. **Spec 02 (Conexión Supabase):** Cliente Singleton configurado y probado (`/health/db`).
3. **Spec 03 (Motor LLM Gemini):** Conexión al modelo `gemini-2.5-flash` usando el SDK `google-genai`.
4. **Spec 04 (Debounce & Orchestrator):** Sistema de agrupamiento asíncrono con `asyncio.create_task()`.
5. **Spec 05 (Meta Outbound - Blindado):** "Fraccionamiento Humano" mediante Regex con separador `|||`.
6. **Spec 06 (Memoria Persistente):** Tablas `orus_users` y `orus_messages` en Supabase. Historial de conversación almacenado y consultado por el orquestador.
7. **Spec 07 (Orus Command Center):** Dashboard API con endpoints para gestión de usuarios en modo HUMAN, historial, resolución de tickets y envío manual de mensajes. CORS habilitado. Alertas Telegram implementadas. Structured Outputs (JSON) en Gemini para sentimiento y handover.
8. **Spec 08 (Calendar, Logs & Métricas):**
   - **Google Calendar:** Integración real con Function Calling de Gemini. `check_free_slots` y `book_appointment` operativas contra `oruspgutierrez@gmail.com`.
   - **Métricas:** Endpoints `GET /api/metrics/bot_vs_human` y `GET /api/metrics/conversion`.
   - **Logs:** Tabla `orus_logs` con `severity`. Manejador global de excepciones en `main.py`.
   - **DB Expandida:** `orus_users` ampliada con `payment_status`, `appointment_date`, `total_spent`.

## Bugs Conocidos / Deuda Técnica
- **⚠️ Timezone en Google Calendar:** El payload de `book_appointment` usa `timeZone: 'UTC'`. Debe cambiarse a `America/Sao_Paulo` para que la hora local coincida con la del calendario del negocio. (Detectado en prueba del 2026-04-25).

## Siguiente Sesión (Punto de Partida)
**Objetivos Prioritarios:**
1. **Fix Timezone:** Corregir `calendar_client.py` para usar `America/Sao_Paulo`.
2. **Frontend Dashboard:** Diseñar la interfaz visual que consuma los endpoints de `/api/users/` y `/api/metrics/`.
3. **Envío Real a Meta:** Reemplazar los prints en consola por `httpx.post` a la API de WhatsApp.
4. **Ingesta Multimodal:** Soporte para recibir URLs de imágenes de manos.

## Comandos Útiles para Retomar
Para arrancar el servidor local:
`uvicorn main:app --port 8000`

Para probar la ráfaga de mensajes:
`python test_burst.py`

Para probar la integración de calendario:
`python test_calendar.py`

## Reglas Activas
- REPORT_ONLY para planes.
- Spec -> Break -> Plan -> Execute.
- "Thin Client, Fat Server"
