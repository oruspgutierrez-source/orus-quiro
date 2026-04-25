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



