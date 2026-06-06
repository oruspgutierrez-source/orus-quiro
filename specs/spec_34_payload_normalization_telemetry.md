# Spec 34: Telemetría de Alta Resiliencia y Normalización de Payloads (Evolution API)

**Estado:** En Progreso
**Fecha:** Junio 2026

---

## 1. Errores Confirmados en Logs de Producción (2026-06-06)

### Error A — `INVALID_ARGUMENT` en Gemini
**Log observado:**
```
Error en Gemini API: 400 INVALID_ARGUMENT.
'Function calling with a response mime type: application/json is unsupported'
```
**Causa:** En el commit `070ec07` se inyectó `response_mime_type="application/json"` en `GenerateContentConfig` junto con `tools=[...]`. La API de Gemini NO permite usar `response_mime_type` cuando se tienen `tools` activos (function calling). Son mutuamente excluyentes según la documentación oficial de Google GenAI SDK.
**Referencia:** https://ai.google.dev/gemini-api/docs/function-calling

**Tarea A:** Eliminar `response_mime_type` de `GenerateContentConfig` en `gemini_client.py`. Mantener los `safety_settings` con `BLOCK_NONE` (eso sí es compatible con tools).

---

### Error B — LID sin resolver (`@lid`)
**Log observado:**
```
remoteJid=37598781259882@lid
[Webhook] ADVERTENCIA: No se pudo resolver el LID 37598781259882@lid
[Buffer] 37598781259882@lid: +1 msg (total=1)
```
**Causa:** La variable `WPP_LID_MODE=false` no está siendo respetada por Evolution API para este número específico. El método `resolve_lid` en `wa_client.py` intenta resolver por `pushName` o `profilePicUrl`, pero al ser un contacto sin foto de perfil o pushName conocido, la resolución falla. El mensaje se procesa igual, pero el `sender_id` queda como LID, lo que puede causar que el bot responda a un ID que WhatsApp no pueda enrutar.
**Estado:** Abierto. El mensaje llega al buffer y a Gemini (con el error A ya bloqueaba), pero el sender_id es incorrecto.

**Tarea B (futura, tras resolver A):** Mejorar `resolve_lid` para intentar resolución via endpoint `/chat/findContacts` de Evolution API antes del fallback, y loggear en `orus_logs` cuando un LID queda sin resolver.

---

## 2. Plan de Acción por Tareas

### TAREA A — Quitar `response_mime_type` de Gemini (BLOQUEANTE)
- **Archivo:** `api/services/gemini_client.py`
- **Línea objetivo:** `response_mime_type="application/json"` dentro de `GenerateContentConfig`
- **Acción:** Eliminar esa línea. Los `safety_settings` se mantienen.
- **Criterio de éxito:** Los logs deben mostrar `[Gemini]` respondiendo sin `INVALID_ARGUMENT`.

### TAREA B — Mejorar resolución de LID (Post-estabilización)
- **Archivo:** `api/services/wa_client.py`
- **Acción:** Agregar llamada al endpoint `GET /chat/findContacts/{instance}?where[id]=<lid>` de Evolution API como primera estrategia de resolución.
- **Criterio de éxito:** El log debe mostrar el LID resuelto a un JID tipo `551199...@s.whatsapp.net`.

### TAREA C — Dashboard de Alertas (Futura)
- Sección "System Health" en el Dashboard React consultando `orus_logs` para eventos `CRITICAL_PAYLOAD_ANOMALY` y `EVOLUTION_CONNECTION_UPDATE`.

---

## 3. Historial de Cambios
| Commit | Descripción | Estado |
|--------|-------------|--------|
| 5e5719b | Hotfix list-payload + telemetría Telegram | ✅ OK |
| 070ec07 | Safety BLOCK_NONE + `response_mime_type` | ❌ Rompió Gemini |
| 965a3ba | Docs: Spec 33 actualizado | ✅ OK |
| f26dd2d | Normalizador + try/except global | ✅ OK (pero indentación mala) |
| 4a183f7 | Fix: indentación corregida | ✅ OK |
| Pendiente | Eliminar `response_mime_type` | 🔧 En progreso |
