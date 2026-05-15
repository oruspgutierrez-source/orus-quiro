# Spec 10: Pipeline de Mensajes v2 → v3

**Versión:** 2.0  
**Fecha original:** 2026-05-05  
**Última actualización:** 2026-05-12  
**Estado:** ✅ SUPERADO — Reemplazado por Pipeline v3 (asyncio nativo)

---

## Contexto Histórico (v2 — ARQ + Redis)

La v2 resolvía la fragmentación de respuestas con un sistema de 5 mecanismos basado en
ARQ Worker + Redis (epochs, locks, next_buffer, timestamps). Funcionó parcialmente pero
introdujo **race conditions** y **complejidad innecesaria** para una instancia single-server.

### Problemas detectados en v2:
- Los `processing_lock`, `epoch`, y `next_buffer` creaban condiciones de carrera en Redis.
- El Worker ARQ añadía una dependencia de infraestructura pesada (proceso separado).
- Los fragmentos zombie seguían apareciendo en escenarios de alta velocidad de escritura.
- **Resultado:** El bot respondía múltiples veces a una sola intención del usuario.

---

## Pipeline v3 — asyncio Nativo (Implementación Actual)

**Fecha de implementación:** 2026-05-12  
**Patrón:** Sliding Window Cancel-and-Restart (equivalente al nodo "Wait" de n8n)

```
WhatsApp → Evolution API (VPS)
               ↓
          Webhook POST → FastAPI (receive_webhook)
               ↓
          Deduplicación por message_id (in-memory)
               ↓
          buffer_message(sender_id, text)
               ↓
          _message_buffers[sender_id].append(text)
               ↓
          ¿Timer activo? → cancel() → nuevo timer
               ↓
          asyncio.sleep(10s) — ventana de silencio
               ↓ (sin cancelación = usuario dejó de escribir)
          Des-registrar timer de _debounce_timers
               ↓
          _process_buffer() — NO cancelable
               ↓
          LID Resolver → Firewall → Rate Limit → Sanitización
               ↓
          Gemini LLM → Fragmentar (|||) → Enviar vía Evolution API
```

### Archivos del Pipeline v3:

| Archivo | Responsabilidad |
|---|---|
| `api/routes/webhooks.py` | Recepción, dedup, extracción de texto, llamada a `buffer_message()` |
| `api/services/message_processor.py` | Debounce (sliding window), buffer en memoria, pipeline completo |
| `api/services/gemini_client.py` | LLM con EOS token y fragmentación `|||` |
| `api/services/wa_client.py` | Cliente Evolution API (envío + resolución LID) |
| `api/services/security.py` | Firewall, Rate Limiter, Sanitización |

### Dependencias eliminadas:
- ❌ `arq` — Worker distribuido (ya no se usa)
- ❌ `redis` — Estado compartido (ya no se usa)
- ❌ `api/workers/arq_worker.py` — Eliminado (2026-05-12)

### Bug crítico corregido (v3.1):
- **Problema:** `task.cancel()` mataba el procesamiento de Gemini a mitad de camino
  cuando un nuevo mensaje llegaba durante la fase de envío.
- **Solución:** Separar `_debounce_then_process` en dos fases:
  - **Fase 1 (cancelable):** `asyncio.sleep(DEBOUNCE_WAIT)`
  - **Fase 2 (NO cancelable):** `_process_buffer()` — se des-registra del dict antes de procesar.
- **Resultado:** Mensajes nuevos durante el procesamiento crean su propio timer limpio.

---

## Notas de Continuidad

- El sistema requiere **solo** `uvicorn main:app --port 8000` (sin worker adicional).
- El debounce es de **10 segundos** de silencio antes de procesar.
- Si el proyecto escala a múltiples instancias, migrar el debounce a Redis Keyspace Notifications.
- El ngrok tiene dominio fijo: `annually-murmuring-reuse.ngrok-free.dev`
