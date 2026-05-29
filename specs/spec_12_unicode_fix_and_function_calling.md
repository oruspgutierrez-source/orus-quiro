# Spec 12 — Fix de Unicode en Windows y Refuerzo de Function Calling

**Fecha:** 2026-05-19
**Estado:** 📋 Borrador — Pendiente de aprobación
**Autor:** Agente Antigravity
**Prioridad:** 🔴 Alta — Bloquea el flujo E2E de agendamiento

---

## 1. Contexto y Problema

Durante la prueba E2E del 19/05/2026, el usuario intentó agendar una cita desde su celular hablando con Orus vía WhatsApp. El bot **no respondió**. El análisis de los logs reveló dos bugs críticos en cadena:

### Bug #1 — UnicodeEncodeError en Windows (CRÍTICO)

**Archivo afectado:** `api/services/gemini_client.py` (línea 220)
**Causa raíz:**
- El bloque `except` general de `generate_response` imprimía en consola el objeto de excepción directamente: `print(f"Error en Gemini API: {e}")`.
- El SDK de Gemini, al procesar el `system_prompt` que contiene el emoji 😊, lanzaba una excepción cuyo mensaje incluía ese carácter.
- La terminal de Windows (PowerShell con encoding `cp1252`) no puede codificar emojis → segunda excepción → crash silencioso del pipeline completo.
- El mismo patrón existía en `api/services/wa_client.py` (bloque `except` de `send_message`).

**Efecto:** El pipeline se detenía en silencio después del LID resolver. El usuario no recibía ninguna respuesta.

**Nota de sesión:** El servidor fue reiniciado con `PYTHONUTF8=1` y se aplicaron dos parches de emergencia a `gemini_client.py` y `wa_client.py` para sanitizar los prints del bloque `except`. Estos cambios **no están registrados** en `backend_log.md`.

---

### Bug #2 — Gemini no responde en JSON estructurado (MODERADO)

**Archivo afectado:** `api/services/gemini_client.py` (system_prompt)
**Causa raíz:**
- Gemini 2.5 Flash respondió con texto libre conversacional en lugar del JSON estructurado `{reply, sentiment, requires_human}` que exige el sistema.
- El sistema de fallback (extracción regex) lo rescató y el mensaje llegó al usuario, pero la respuesta de Gemini NO invocó la herramienta `check_free_slots` para verificar disponibilidad real en Google Calendar. En cambio, preguntó al usuario por su nombre y teléfono manualmente, omitiendo el flujo de Function Calling.

**Efecto:** La cita no se agenda en Google Calendar. El bot improvisa una conversación en lugar de seguir el flujo oficial de agendamiento.

---

## 2. Archivos Impactados

| Archivo | Tipo de cambio | Razón |
|---|---|---|
| `api/services/gemini_client.py` | MODIFICAR | Sanitizar todos los prints con emojis. Reforzar instrucción de JSON en system_prompt. Agregar instrucción explícita de cuándo invocar Function Calling. |
| `api/services/wa_client.py` | MODIFICAR | Sanitizar el bloque `except` de `send_message` (parche de emergencia ya aplicado, debe consolidarse). |
| `bitacoras/backend_log.md` | ACTUALIZAR | Registrar los cambios de esta sesión que se aplicaron sin documentar. |
| `bitacoras/BITACORA_SESION.md` | ACTUALIZAR | Reflejar el estado actual del proyecto. |

---

## 3. Tasks Atómicos

### Task 1 — Auditoria y Consolidación de Parches de Emergencia
- **Qué:** Verificar el estado actual de `gemini_client.py` y `wa_client.py` para confirmar que los parches de emergencia de Unicode están correctamente aplicados y son estables.
- **Criterio de aceptación:** Ningún `print()` en ambos archivos imprime un objeto de excepción directamente. Todos los `str(e)` pasan por `.encode('ascii', 'replace').decode('ascii')`.

### Task 2 — Refuerzo del System Prompt para JSON Obligatorio
- **Qué:** Modificar el `system_rules` en `gemini_client.py` para hacer más explícita la instrucción de responder SIEMPRE en JSON. Se detectó que Gemini 2.5 Flash ignora esta instrucción en modo conversacional espontáneo.
- **Solución propuesta (CONCEPTO):** Añadir al final del `system_rules` una sección de "instrucción de cierre" que refuerce:
  ```
  // PSEUDOCODIGO
  INSTRUCCIÓN FINAL IRREVOCABLE:
  Tu respuesta SIEMPRE debe ser un objeto JSON válido.
  Si no hay nada más que responder, devuelve: {"reply": "...", "sentiment": "...", "requires_human": false}
  NUNCA respondas con texto libre fuera de un JSON.
  ```
- **Criterio de aceptación:** El parser `json.loads()` puede parsear la respuesta directamente sin necesidad del fallback regex en el 95%+ de los casos.

### Task 3 — Refuerzo del Flujo de Function Calling (Agendamiento)
- **Qué:** Modificar el `system_rules` para que Gemini entienda explícitamente cuándo DEBE invocar `check_free_slots` y `book_appointment` en lugar de improvisar una conversación.
- **Solución propuesta (CONCEPTO):**
  ```
  // PSEUDOCODIGO — Sección a añadir en system_rules
  FLUJO OBLIGATORIO DE AGENDAMIENTO:
  Cuando el usuario pida agendar/reservar/apartar una cita:
  1. NUNCA pidas nombre o teléfono primero.
  2. PRIMERO invoca check_free_slots() para mostrar los horarios disponibles.
  3. Una vez que el usuario elija un horario, invoca book_appointment() con los datos.
  4. Solo entonces confirma el agendamiento al usuario.
  ```
- **Criterio de aceptación:** Al enviar "quiero agendar una cita para mañana", Gemini invoca `check_free_slots` automáticamente sin preguntar datos adicionales primero.

### Task 4 — Registro en Bitácoras
- **Qué:** Actualizar `backend_log.md` con todos los cambios realizados en esta sesión (parches de emergencia de Unicode, reinicio del servidor con PYTHONUTF8, desactivación de RLS en Supabase) y actualizar `BITACORA_SESION.md` con el estado actual.
- **Criterio de aceptación:** Los tres registros de `backend_log.md` están completos y `BITACORA_SESION.md` refleja el estado real del servidor.

---

## 4. Orden de Ejecución

```
Task 1 → Task 2 → Task 3 → Task 4
```
Tasks 1, 2 y 3 son secuenciales (2 y 3 dependen de revisar el estado real del archivo en Task 1). Task 4 siempre al final.

---

## 5. Criterio de Éxito Global

1. El usuario envía "quiero agendar una cita para mañana" por WhatsApp.
2. Orus responde mostrando horarios disponibles (Function Calling activo).
3. El usuario elige un horario → Orus confirma el agendamiento en Google Calendar.
4. Todos los cambios están registrados en `backend_log.md`.

---

## 6. Riesgos Identificados

| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| Gemini 2.5 Flash ignora la instrucción de JSON incluso con refuerzo | Media | Evaluar si se requiere `response_mime_type="application/json"` en `GenerateContentConfig` — es incompatible con Function Calling en algunos modelos, requerirá prueba. |
| El RLS desactivado en Supabase deja la DB expuesta | Alta (entorno local) | Aceptable para desarrollo local. Debe reactivarse antes del despliegue en VPS. |
