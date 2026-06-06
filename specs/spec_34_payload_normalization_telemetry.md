# Spec 34: Telemetría de Alta Resiliencia y Normalización de Payloads (Evolution API)

**Estado:** Planeado
**Fecha:** Junio 2026

## 1. Problema: Mutaciones de Payload en Webhooks
Durante eventos de reinicio, actualizaciones menores de Evolution API, o cambios en la configuración de la instancia (ej. de WhatsApp Business a Personal, o activación de variables como `WPP_LID_MODE`), la estructura del paquete de datos (payload) que Evolution API envía a nuestro Webhook puede sufrir mutaciones.

**Estructuras observadas:**
1. **Objeto Directo:** `{"data": {"key": {"remoteJid": "..."}, "message": {...}}}`
2. **Lista Empaquetada (Actual):** `{"data": [{"key": {"remoteJid": "..."}, "message": {...}}]}`
3. **Wrapper de Eventos:** `{"event": "messages.upsert", "data": ...}`

Si el backend espera la estructura 1 y recibe la estructura 2, se produce un colapso (`Error 500: AttributeError`), perdiendo el mensaje del cliente en el vacío.

## 2. Plan de Acción y Solución

Para que el sistema sea inmune a estas variaciones y tengamos visibilidad inmediata en el Dashboard, implementaremos tres capas de blindaje:

### Capa 1: Normalizador de Payloads (Extractor Recursivo)
En lugar de buscar rutas exactas (ej. `payload["data"][0]["key"]`), crearemos una función inteligente llamada `normalize_evolution_payload(payload)` que:
- Detecte si el objeto es una lista o un diccionario de forma segura.
- Realice una búsqueda recursiva de los nodos críticos: `key`, `message`, `pushName`, `messageTimestamp`.
- Devuelva un objeto estandarizado a nuestro `message_processor.py`, sin importar dónde o cómo escondió Evolution API los datos.

### Capa 2: Sandbox de Respaldo y Alarma (Telegram + Supabase)
Si la Capa 1 encuentra un payload completamente irreconocible (ej. cambiaron el nombre de todas las variables):
1. **No crashea (No Error 500).** Atrapa el error con un `try/except` global.
2. Extrae las claves (keys) del payload desconocido para entender su topología.
3. Lo guarda intacto en Supabase (`orus_logs`) bajo una nueva severidad: `CRITICAL_PAYLOAD_ANOMALY`.
4. Dispara instantáneamente una alarma a nuestro Telegram Bot: *"🚨 Alerta de Mutación de Payload. Estructura recibida: [key1, key2]. Revisa el Dashboard."*

### Capa 3: Interfaz de Alertas en el Dashboard
El panel de control (Dashboard React) deberá incluir una sección visible llamada "System Health" o "Alertas de Infraestructura" que consulte la tabla `orus_logs` buscando eventos de `CRITICAL_PAYLOAD_ANOMALY` o fallos de `connection.update`. Así, si algo cambia, lo veremos antes de que un cliente note que el bot no responde.

## 3. Implementación a Realizar
- Modificar `api/routes/webhooks.py` aislando el parsing en un método `extract_message_data(payload)`.
- Envolver `receive_webhook` en un `try...except Exception as e` absoluto.
- Conectar este `except` con `supabase_client.log_error()` y `telegram_client.send_telegram_alert()`.

Con este ecosistema, cualquier futura mutación de la API no será un error silencioso, sino un evento controlado, registrado y reportado de inmediato.
