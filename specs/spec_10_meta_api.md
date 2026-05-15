# Spec 10: Integración de Envío Real a Meta (API de WhatsApp)

> **Estado:** ⚠️ SUPERADO — El proyecto migró de Meta Cloud API a Evolution API (ver `spec_10_unofficial_api_integration.md` y `spec_10_pipeline_v2.md`).

## 1. Objetivo
Reemplazar la actual simulación de envío de mensajes (basada en `print()` dentro del cliente de Meta) por una integración real con la API Cloud de WhatsApp de Meta, utilizando las credenciales provistas, para completar el ciclo real de salida de los mensajes hacia los usuarios.

## 2. Arquitectura y Componentes Involucrados
- **`api/clients/meta_client.py`**: Actualmente se simula el envío con un log de consola. Se actualizará la función responsable de enviar mensajes de texto y/o contenido multimedia (si aplica) utilizando la librería `httpx`.
- **`.env`**: Debe contar con las variables correctas (ej: `META_ACCESS_TOKEN`, `META_PHONE_NUMBER_ID`, `META_API_VERSION`).
- **Orquestador de Mensajes (`spec_04`) & Meta Outbound (`spec_05`)**: Estos seguirán encargándose del particionado (chunking) y el encolamiento, pero al final del proceso invocarán al cliente real en lugar del simulado.

## 3. Consideraciones de Seguridad
- **Protección de Tokens**: El Token de Acceso Permanente o Temporal de Meta jamás debe registrarse en los logs de la base de datos (evitar leaks en `orus_logs`).
- **Manejo de Errores (Error Handling)**: Interceptar excepciones HTTP de `httpx` (ej. 400 por número inválido, 401 por token expirado) y registrarlas de manera segura en `orus_logs` usando el `logger` central, devolviendo información útil al ecosistema para no detener el sistema si el webhook sigue llegando.
- **Validación de Credenciales**: Asegurarse de que el número telefónico del destinatario cumpla con los estándares internacionales exigidos por la API de Meta.

## 4. Plan de Implementación (Break & Plan)
1. **Paso 1: Validación de Entorno**: 
   - Confirmar en el código que `os.getenv` recoja correctamente los tokens desde el archivo `.env`.
2. **Paso 2: Refactorización de `meta_client.py`**:
   - Eliminar el código del `print()` mock.
   - Implementar `httpx.AsyncClient` para enviar un POST al endpoint oficial `https://graph.facebook.com/{version}/{phone_number_id}/messages`.
   - Incorporar headers apropiados (`Authorization: Bearer ...` y `Content-Type: application/json`).
   - Construir el payload JSON con la estructura que pide Meta (`messaging_product`, `recipient_type`, `to`, `type`, `text`).
3. **Paso 3: Bloques `try/except`**:
   - Ajustar el manejo de errores para loguear status HTTP y body de respuesta en caso de fallo, interactuando con `orus_logs`.
4. **Paso 4: Pruebas Unitarias o Controladas**:
   - Ejecutar un script de prueba que despache un mensaje "Hello World" controlado hacia un número propio para comprobar que la API devuelve HTTP 200 y el mensaje llega al WhatsApp destino.

## 5. Salida Esperada
El backend dejará de imprimir las salidas del agente por consola y las despachará exitosamente hacia el dispositivo móvil del usuario receptor, permitiendo probar la conversación end-to-end de manera fluida.
