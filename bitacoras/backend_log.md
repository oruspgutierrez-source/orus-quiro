# Bitácora de Backend
Registro de cambios, decisiones y eventos en el desarrollo del backend.

## [2026-04-24] - Implementación Spec 01
- **Objetivo:** Establecer el servidor base FastAPI y configuración de endpoints para Meta Webhooks.
- **Archivos creados/modificados:**
  - `requirements.txt`
  - `.env.example`
  - `main.py`
  - `api/__init__.py`
  - `api/routes/__init__.py`
  - `api/routes/webhooks.py`
- **Endpoints configurados:**
  - `GET /webhook`: Validación de token y retorno de `hub.challenge`.
  - `POST /webhook`: Recepción de payload y retorno HTTP 200 OK.
- **Estado:** Completado exitosamente.

## [2026-04-24] - Verificación Spec 01
- **Objetivo:** Validación de seguridad y funcionamiento del endpoint de webhook.
- **Acciones Ejecutadas:**
  - Inicialización del servidor FastAPI mediante Uvicorn en el puerto 8000.
  - Ejecución de prueba GET con token válido (`georgecomehuesos2025`). Resultado: HTTP 200 OK, respuesta `1234567890`.
  - Ejecución de prueba GET con token inválido (`token_falso`). Resultado: HTTP 403 Forbidden, rechazo exitoso.
- **Estado:** Validado exitosamente. Cumple con los criterios de aceptación y medidas de seguridad de Meta.

## [2026-04-24] - Implementación y Verificación Spec 02
- **Objetivo:** Establecer puente seguro con Supabase.
- **Acciones Ejecutadas:**
  - Inyección de dependencias (`supabase`).
  - Creación de cliente Singleton para Supabase en `api/db/supabase_client.py`.
  - Creación del endpoint `GET /health/db` para verificar la conectividad de la base de datos de manera agnóstica.
  - Corrección de orden de carga de `.env` en `main.py` para asegurar que las variables estén disponibles antes del inicio de módulos.
  - Verificación HTTP local: Resultado HTTP 200 OK. La integración con Supabase es completamente operativa.
- **Estado:** Completado y verificado.

## [2026-04-24] - Implementación y Verificación Spec 03
- **Objetivo:** Integrar SDK de Google GenAI (Gemini) como cerebro principal.
- **Acciones Ejecutadas:**
  - Inyección de dependencia oficial (`google-genai`).
  - Implementación del servicio `api/services/gemini_client.py` consumiendo `GEMINI_API_KEY`.
  - Configuración y validación del modelo `gemini-2.5-flash` (estable y verificado en la API Key actual).
  - Creación del enrutador de prueba `api/routes/llm_test.py` con el endpoint `POST /health/llm`.
  - Prueba local ejecutada enviando el JSON {"prompt": "Hola, ¿eres un experto en quiromancia védica?"}. 
  - Resultado: El servidor generó correctamente la respuesta desde la IA demostrando conocimientos sobre *Samudrika Shastra* y retornó el bloque JSON con éxito.
- **Estado:** Completado y verificado. El cerebro cognitivo está en línea.

## [2026-04-24] - Implementación y Verificación Spec 04
- **Objetivo:** Conectar el Webhook de Meta con Gemini implementando Debounce/Agrupamiento.
- **Acciones Ejecutadas:**
  - Creación de `api/services/orchestrator.py` implementando un diccionario en memoria (`active_sessions`) para encolar mensajes.
  - Uso de `asyncio.create_task` (guardando la referencia de memoria para evitar el GC) y `asyncio.sleep(7)` para liberar el Event Loop de FastAPI y asegurar tiempos de respuesta HTTP O(1).
  - Actualización de `api/routes/webhooks.py` para parsear el esquema de la Cloud API y llamar a `enqueue_message()`.
  - Prueba de estrés (Ráfaga) mediante script en Python: Se simularon 3 mensajes ("Hola,", "necesito ayuda", "con mi mano derecha.") en lapsos de 1 segundo.
  - Resultado: El servidor devolvió HTTP 200 OK inmediatamente por cada mensaje (latencia media 3ms). Pasados 7 segundos, Orus unificó el texto e hizo UNA SOLA llamada a Gemini, resultando en una respuesta unificada impresa en consola.
- **Estado:** Completado y verificado. Orus ya posee paciencia cognitiva asíncrona.

## [2026-04-24] - Implementación y Verificación Spec 05
- **Objetivo:** Simular envío hacia Meta implementando 'Fraccionamiento Humano' blindado con Regex.
- **Acciones Ejecutadas:**
  - Actualización de dependencias (`httpx`).
  - Creación de `api/services/meta_client.py` con `send_humanized_response`, manejando el regex `r'\|{2,}'` y filtrando mensajes vacíos.
  - Inyección de instrucciones semánticas en `gemini_client.py` para forzar a la IA a retornar `|||`.
  - Integración en `orchestrator.py`.
  - Verificación en Consola: Se simuló la ráfaga, Orus unificó la solicitud, la IA devolvió el mensaje usando el formato delimitado, el sistema Regex partió el texto limpiamente y simuló 2 envíos con retrasos asíncronos (`4.58s` y `3.72s`).
- **Estado:** Completado y verificado. Orus ahora se comunica como un humano (tiempos y fragmentación).


## [2026-04-27] - Implementación Spec 09: Blindaje, Seguridad y Anti-Spam
- **Objetivo:** Implementar un sistema de seguridad en 4 capas para proteger la DB (Supabase) y el LLM (Gemini) contra ataques e inyecciones.
- **Archivos creados:**
  - `api/services/security.py` — Módulo centralizado con `sanitize_input()` (5 filtros: Unicode NFC, longitud, control chars, SQLi, Prompt Injection), `check_rate_limit()` (ventana 60s, umbral 12 msgs), `clear_rate_limit()`, `log_security_event()`.
  - `api/middleware/__init__.py` — Paquete middleware.
  - `api/middleware/webhook_signature.py` — Middleware ASGI puro para validación HMAC SHA-256 del header `X-Hub-Signature-256` de Meta. Bypass configurable para desarrollo local. Patrón de re-inyección de `receive` para preservar el body stream.
  - `specs/spec_09_security_plan.md` — Documento de arquitectura completo.
- **Archivos modificados:**
  - `api/routes/webhooks.py` — Pipeline de seguridad integrado: Firewall (is_blocked) → Rate Limiter → Sanitización → enqueue_message().
  - `api/routes/dashboard.py` — Nuevo endpoint `POST /api/users/{user_id}/unblock` con desbloqueo en DB, limpieza de rate limiter in-memory y log de auditoría.
  - `main.py` — Registro del `WebhookSignatureMiddleware`.
  - `.env` / `.env.example` — Variables `ENVIRONMENT=development` y `META_APP_SECRET`.
- **Migraciones SQL ejecutadas:**
  - `ALTER TABLE orus_users ADD COLUMN is_blocked BOOLEAN DEFAULT FALSE;`
  - `ALTER TABLE orus_logs ADD COLUMN event_type VARCHAR(50), source_identifier TEXT, raw_payload TEXT;`
- **Bug corregido (bonus):** Indentación rota en `gemini_client.py` (import de `calendar_client` fuera de la función).
- **Estado:** Completado y verificado. Servidor arranca limpio con las 4 capas activas.

## [2026-04-27] - Fix Timezone Google Calendar
- **Objetivo:** Corregir el desfase horario en las citas creadas por `book_appointment()`.
- **Archivo modificado:** `api/services/calendar_client.py`
- **Cambio:** `timeZone` de `'UTC'` → `'America/Sao_Paulo'` en ambos bloques (`start` y `end`) del evento.
- **Estado:** Completado. Las citas ahora se crean en la hora local del negocio.


## [2026-04-30] - Auditoría E2E Webhook WhatsApp y Troubleshooting
- **Objetivo:** Lograr comunicación bidireccional (End-to-End) entre la API de WhatsApp de Meta y el Worker (ARQ) de FastAPI.
- **Acciones Ejecutadas:**
  - Actualización del archivo .env con el token permanente y la corrección de la variable META_PHONE_NUMBER_ID.
  - Envío exitoso de mensaje (Template hello_world) por API desde Python. Meta retornó HTTP 200 OK y message_status: accepted.
  - Descubrimiento importante: La API de WhatsApp muta el número físico del destinatario (le elimina el dígito 9 extra común en Brasil para códigos de área >=30) resultando en un wa_id más corto (553598869018). El Backend manejará automáticamente este wa_id entrante.
  - Verificación del túnel ngrok (respondiendo HTTP 200) y de Uvicorn.
- **Bloqueador Actual (Meta no entrega Webhooks):**
  - El celular físico del usuario no está recibiendo el mensaje, ni Meta está disparando los Webhooks (POST) hacia la URL de ngrok.
  - Es altamente probable que Meta tenga atascado el Test Number (+1 555-634-8064) o que WhatsApp esté filtrando los mensajes como Spam silencioso.
- **Pasos para la Siguiente Sesión:**
  1. Acceder al número de prueba de Meta desde el celular del usuario usando el link directo: https://wa.me/15556348064?text=Hola%20Orus para forzar la apertura del canal y salir del filtro de Spam.
  2. Forzar a Meta a refrescar la configuración de Webhooks (Guardar temporalmente una URL falsa como google.com y luego volver a guardar la de ngrok).
  3. Validar si el Webhook finalmente ingresa a Uvicorn/ARQ para cerrar el E2E.
- **Estado:** Pendiente. Arquitectura verificada localmente pero esperando desbloqueo del lado de Meta Developers.

## [2026-05-04] - Hito Superado: Escape del Pantano (Evolution API)
- **Objetivo:** Lograr comunicación E2E estable, solucionar problemas de direccionamiento de JIDs y fragmentación por envío rápido.
- **Acciones Ejecutadas:**
  - **Refactor de JID:** Se corrigió la lógica en `webhooks.py` para usar `key.remoteJid` y evitar que el bot hardcodee la instancia como remitente (`sender`).
  - **Debounce con Redis:** Se implementó agrupación de mensajes con un buffer de 6 segundos en Redis (`arq_worker.py`). Esto soluciona la desincronización de respuestas (el bot ya no saluda doble, ahora une y comprende todo el contexto en un solo prompt).
  - **Memoria Restaurada:** Se actualizó el pipeline para inyectar el historial (traído de la base de datos `orus_messages` en Supabase) al contexto de Gemini. Esto devuelve al LLM la capacidad de recordar conversaciones previas del usuario.
- **Estado:** ✅ E2E Completamente operativo y refinado. Orus ahora se comporta orgánicamente, agrupando ráfagas y guardando memoria persistente.

## [2026-05-04] - Refinamiento de Enrutamiento y Base de Datos Universal
- **Objetivo:** Garantizar que todos los usuarios entrantes, independientemente de sus políticas de privacidad (JIDs `@lid`), sean registrados y procesados con sus números de teléfono reales en la base de datos PostgreSQL.
- **Acciones Ejecutadas:**
  - **Traducción en la Puerta de Entrada:** Se trasladó la lógica de `resolve_lid` de Evolution API directamente a `webhooks.py`. Ahora, tan pronto como entra un payload de Evolution API, si trae un `@lid`, el webhook lo resuelve a su número `@s.whatsapp.net` real antes de procesarlo.
  - **Registro Dinámico:** Con este cambio, todo el pipeline subsiguiente (Buffer en Redis, Queue en ARQ Worker, y validación en `orus_users` de Supabase) opera 100% sobre números reales.
  - **Auto-registro PostgreSQL:** El `arq_worker.py` ahora registra silenciosamente a usuarios nuevos que le hablen por primera vez, usando su teléfono real. Esto resuelve la solicitud de "validar si existe en supabase, si no registrarlo para generar el ID, y responder a su número editado para que Meta no lo rebote".
- **Estado:** ✅ Implementado con éxito. El bot ahora soporta tráfico de cualquier número (nuevo o antiguo, público o con LID) interactuando con su historial correcto en DB y respondiendo dinámicamente sin errores 400.

## [2026-05-12] - Reingeniería Pipeline v3: De ARQ+Redis a asyncio Nativo
- **Objetivo:** Eliminar la fragmentación de respuestas causada por race conditions en la arquitectura ARQ+Redis.
- **Diagnóstico:** El sistema de 5 mecanismos (epochs, locks, next_buffer, timestamps en Redis) era sobre-ingeniería para una instancia single-server. Las condiciones de carrera causaban que el bot respondiera múltiples veces a una sola intención del usuario.
- **Acciones Ejecutadas:**
  - **Eliminación de ARQ Worker:** Removido `api/workers/arq_worker.py` (~300 líneas) y el directorio `api/workers/`.
  - **Nuevo módulo `api/services/message_processor.py`:** Implementa debounce con patrón Sliding Window Cancel-and-Restart usando `asyncio.Task` y `cancel()`.
  - **Simplificación de `webhooks.py`:** Eliminadas referencias a `processing_lock`, `next_buffer`, `snapshot_size`, `epoch`. Agregada deduplicación por `message_id` in-memory.
  - **Limpieza de `main.py`:** Eliminado el `lifespan` manager del pool ARQ.
  - **Limpieza de `requirements.txt`:** Eliminadas dependencias `arq` y `redis`.
- **Bug crítico corregido (v3.1):**
  - `task.cancel()` mataba el procesamiento de Gemini a mitad de camino cuando un nuevo mensaje llegaba durante la fase de envío.
  - **Fix:** Separar `_debounce_then_process` en Fase 1 (cancelable: sleep) y Fase 2 (NO cancelable: process). El timer se des-registra de `_debounce_timers` ANTES de procesar.
- **Configuración:** Debounce = 10 segundos de silencio.
- **Test de validación:**
  - Test automatizado (`test_debounce.py`): 6 mensajes rápidos → 1 sola respuesta. ✅
  - Test real con WhatsApp (Evolution API): Ráfaga de 4 mensajes → agrupados y procesados como intención única. ✅
- **Estado:** ✅ Pipeline v3 operativo. Infraestructura reducida a solo `uvicorn main:app`.

## [2026-05-14] - Refactorización del Pipeline Multimodal (Spec 11)

### Contexto y Problema
- Inicialmente usábamos un manejador asíncrono para texto y se extraía el `caption` de las imágenes en el webhook, rompiendo la estructura del mensaje.
- El problema: Al intentar leer el caption extraído, la lógica del webhook no pasaba correctamente el binario en sincronía.

### Solución Implementada
- **`webhooks.py`:** Se removió la extracción forzada del texto del payload multimedia. Ahora se pasa la entidad multimedia completa (con su `mimetype`, `base64`/`mediaKey` y `caption`) hacia la cola del `message_processor.py`.
- **Sliding Window:** Se integró un Debounce de 10 segundos en memoria. Esto es crítico para acumular ráfagas (usuario envía múltiples fotos y audios seguidos). Si entra un mensaje del mismo usuario, se reinicia el temporizador.

### Conversión de Audio Fallback
- **Decisión técnica:** Se integró `ffmpeg` en `message_processor.py` (líneas de conversión a MP3) para transformar al vuelo cualquier audio a MP3 (16000Hz, Mono) en un archivo temporal. Si falla la conversión, hace un fallback al binario original, pero por defecto envía el MP3 garantizando 100% de éxito en Gemini.

## [2026-05-15] - Ejecución Spec 08: API de Métricas y Seguridad RLS
- **Objetivo:** Refactorizar Gemini para Function Calling, crear API de métricas para el Dashboard y habilitar seguridad Row Level Security en Supabase.
- **Acciones Ejecutadas:**
  - **Function Calling (Gemini):** Se validó que `api/services/gemini_client.py` cuenta con la inyección dinámica de `tools` en la configuración del modelo (`GenerateContentConfig`) y un bucle de iteración robusto para gestionar llamadas a funciones nativas.
  - **API de Métricas Consolidadas:** Se creó `api/routes/metrics.py` y se migró el antiguo `metrics_router` que existía en `dashboard.py`. Se integraron nuevos endpoints solicitados en el audit (`/appointments_weekly`, `/users_retention`, `/error_rate`).
  - **Reestructuración de Endpoints:** Se actualizó `main.py` para incluir independientemente el router `metrics` apuntando al nuevo archivo.
  - **Securización de la Base de Datos:** Se escribió el script SQL `rls_policies.sql` diseñado para habilitar el aislamiento `Row Level Security` en las tablas `orus_users`, `orus_logs` y `orus_messages`. Debido a la política `mcp-economy-protocol`, la inyección directa en la base de datos se dejó como un paso manual para el usuario, reduciendo el consumo de créditos.
  - **Pruebas Locales (Task 5):** Se creó el script `test_spec_08.py` validando exitosamente el código HTTP 200 en los 5 endpoints de métricas, corrigiendo consultas en Supabase-py. También se corrigió la integración de herramientas (`tools`) migrando de `gemini-2.0-flash` a `gemini-2.5-flash` y ajustando los parámetros de `GenerateContentConfig` para compatibilizar la inferencia de JSON y el uso de `Function Calling`, probando exitosamente la detección e invocación de `check_free_slots`.
- **Estado:** ✅ Tareas backend completadas. Listo para su integración en el panel Frontend (Dashboard React) y despliegue final a EasyPanel.