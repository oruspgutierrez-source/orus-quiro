# Spec 18 — Rediseño de Identidad Cognitiva: El Escultor

**Fecha:** 2026-05-23
**Referencia visual:** `guiabot.html`
**Estado:** En Ejecución

## Objetivo

Reemplazar la identidad actual de Orus (asistente místico de quiromancia védica) por el arquetipo clínico "El Escultor / Arquitecto de Sistemas Biosemióticos". El cambio afecta el tono, la terminología, los textos fijos de WhatsApp y las docstrings de las herramientas.

## Alcance

| Archivo | Cambio |
|---------|--------|
| `api/services/gemini_client.py` | System prompt + docstrings de tools |
| `api/routes/payments.py` | Mensaje de confirmación post-pago (línea 85-90) |
| `api/services/calendar_client.py` | Mensaje de confirmación post-agendamiento |

## Tasks

- **Task 1:** Actualizar `system_rules` en `gemini_client.py` — nueva identidad + terminología biosemiótica + prohibición de emojis + texto de acogida exacto de Fase 1.
- **Task 2:** Actualizar docstrings de `send_introductory_audio()` y `generate_payment_link()` en `gemini_client.py` para alinear al nuevo arquetipo.
- **Task 3:** Actualizar mensaje de confirmación post-pago en `payments.py` (línea 85-90) al guión de Fase 3.5.
- **Task 4:** Actualizar mensaje de confirmación post-agendamiento en `calendar_client.py` al guión de Fase 5.
