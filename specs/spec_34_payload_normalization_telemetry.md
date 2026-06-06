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

### TAREA B — Mejorar resolución de LID (BLOQUEANTE — produce sender_id incorrecto en Supabase)
- **Archivo:** `api/services/wa_client.py` → método `resolve_lid`
- **Problema actual:** El método llama a `/chat/findContacts` y busca coincidencias de `pushName` o `profilePicUrl`. Si el contacto no tiene esos datos, devuelve el LID sin cambios. Supabase termina registrando al usuario con `phone_number = 37598781259882@lid`.
- **Investigación realizada:**
  - Según la documentación oficial de Evolution API v2 y casos confirmados en GitHub/Reddit, el endpoint `POST /profile/fetchProfile/{instance}` acepta un `remoteJid` (incluyendo el `@lid`) y devuelve el perfil del contacto con el número de teléfono real.
  - Alternativa: `POST /chat/findContacts/{instance}` con `where: {id: "<lid>"}` filtra directamente por ese LID y puede devolver el JID real si Evolution API lo tiene en caché.
  - La clave del payload que contiene el número real varía: puede ser `wuid`, `id`, `remoteJid`, o `phone`. Hay que loggear la respuesta real para confirmarlo en producción.
- **Estrategia de implementación (3 capas de fallback):**
  1. **Capa 1:** Consultar `/chat/findContacts` con `where: {id: lid}` — si devuelve un contacto con JID real, usarlo.
  2. **Capa 2:** Consultar `/profile/fetchProfile` con el LID — extraer número del campo `wuid` o `phone`.
  3. **Capa 3 (fallback):** Si ambos fallan, loggear en `orus_logs` con evento `LID_UNRESOLVED` y continuar con el LID (para no bloquear el flujo). La respuesta llegará al LID (WhatsApp la enruta internamente), aunque Supabase quedará con registro LID.
- **Criterio de éxito:** El log debe mostrar `[LID RESOLVER] <lid> resuelto a 5491199...@s.whatsapp.net` y Supabase debe registrar el número real.

### TAREA B2 — Corrección del mapeo LID incorrecto (CRÍTICO)
**Fecha detectada:** 2026-06-06
**Log observado:**
```
37598781259882@lid → 5511943231001@s.whatsapp.net  (primer intento)
37598781259882@lid → 553799282726@s.whatsapp.net   (intentos posteriores)
Número real del usuario: 553598869018
```
**Causa raíz confirmada:** El endpoint `/chat/findContacts` con `where:{id: lid}` no filtra por el LID real del contacto. Devuelve la lista completa de contactos o el primer contacto con `@s.whatsapp.net` disponible — completamente aleatorio e incorrecto. El LID `37598781259882@lid` pertenece al número real `553598869018` pero el resolver toma el número de otro contacto de la agenda del bot.

**Solución correcta:** El campo `pushName` del LID está disponible en el evento `contacts.update` que Evolution API envía justo después del `messages.upsert`. Sin embargo, la mejor solución sin depender de eventos externos es **no usar `/chat/findContacts` para mapear LIDs** — ese endpoint solo es útil para buscar por nombre, no para resolución LID→JID.

**La verdadera fuente del número real** en Evolution API es el evento `contacts.update` que llega dentro del mismo webhook con el campo `phoneNumber` o un JID sin sufijo `@lid`. 

**Implementación correcta (Tarea B2):**
- En el webhook, interceptar el evento `contacts.update` y construir una tabla de mapeo `LID → JID real` en memoria (o en Supabase).
- Al recibir `messages.upsert` con `@lid`, consultar esa tabla antes de llamar a la API de Evolution.
- Si no está en la tabla, NO intentar resolver via `/chat/findContacts` (produce resultados incorrectos). Usar el LID directamente — WhatsApp lo enruta correctamente para envío aunque para el registro en Supabase quede como LID.


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
| aecc09f | fix(tarea-A): Eliminar response_mime_type | ✅ OK — Gemini responde |
| Pendiente | Tarea B: Mejorar resolve_lid con 3 capas | 🔧 En progreso |

