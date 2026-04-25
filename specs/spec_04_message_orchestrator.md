# Spec 04: Message Orchestrator & Debounce System

## Objetivo
Conectar el Webhook de Meta (POST) con el servicio de Gemini, implementando un sistema de agrupamiento de mensajes (Debounce/Buffer) para manejar el comportamiento humano de enviar múltiples mensajes cortos en WhatsApp/Instagram.

## Componentes Requeridos
1.  **Gestor de Cola (Buffer):** Crear un módulo `api/services/orchestrator.py`. Este debe contener una estructura en memoria (ej. un diccionario de Python) que almacene los mensajes entrantes agrupados por el `sender_id` (número de teléfono o ID de usuario de Meta).
2.  **Lógica de Debounce:** Implementar una tarea asíncrona (usando `asyncio.sleep` o `BackgroundTasks` de FastAPI). Cuando entra un mensaje de un `sender_id`:
    * Si no hay un temporizador activo para ese usuario, se inicia uno de 7 segundos.
    * Si ya hay un temporizador, se añade el nuevo mensaje al bloque de texto existente.
    * Al expirar los 7 segundos, el texto concatenado se envía a `gemini_client.generate_response()`.
3.  **Actualización del Webhook:** Modificar el endpoint `POST /webhook` en `api/routes/webhooks.py` para que:
    * Extraiga el `sender_id` y el texto del mensaje del payload JSON de Meta.
    * Envíe estos datos al `orchestrator.py` en segundo plano.
    * Siga retornando HTTP 200 OK inmediatamente a Meta (esto es crucial).

## Criterios de Aceptación
* El endpoint POST no se bloquea esperando a Gemini; retorna 200 OK al instante.
* Si un usuario envía 3 mensajes en un lapso de 5 segundos, el sistema los concatena y hace **una sola** llamada a Gemini.
* (Por ahora, la respuesta de Gemini solo debe imprimirse en la consola/terminal, ya que la API de envío de Meta será el Spec 05).
