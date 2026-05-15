# Spec 11: Capacidades Multimodales — Visión, Audio y Documentos

**Versión:** 1.0  
**Fecha:** 2026-05-14
**Estado:** ✅ COMPLETADO
**Dependencias:** Spec 03 (LLM Core) ✅, Spec 10 (Pipeline v3) ✅

---

## Objetivo

Dotar a Orus de la capacidad de recibir, interpretar y responder sobre contenido multimedia
enviado por los usuarios a través de WhatsApp: **fotografías** (lectura de palmas, capturas),
**notas de voz** (audio), y **documentos** (PDF, capturas de recetas, etc.).

Actualmente Orus solo procesa texto plano (`message.conversation` y `extendedTextMessage`).
Este spec extiende el pipeline para manejar los tipos `imageMessage`, `audioMessage`,
`documentMessage` y `videoMessage` que llegan desde Evolution API.

---

## Arquitectura Propuesta

```
WhatsApp (usuario envía foto/audio/doc)
          ↓
Evolution API (VPS) — webhook payload con mediaKey + mimetype
          ↓
POST /webhook → FastAPI
          ↓
¿Tiene media? → Descargar binario via Evolution GET /s3/getMedia
          ↓
Convertir a bytes → Enviar como Part multimodal a Gemini
          ↓
generate_content([media_bytes, texto_contexto])
          ↓
Respuesta JSON → Fragmentar (|||) → Enviar vía Evolution API
```

---

## Sub-specs de Implementación

### Sub-spec 11.1 — Extracción de Media del Webhook

**Archivo:** `api/routes/webhooks.py`  
**Objetivo:** Detectar y clasificar mensajes multimedia en el payload de Evolution API.

**Lógica:**
- El payload de Evolution API incluye el tipo de mensaje en `data.message`:
  - `imageMessage` → foto enviada
  - `audioMessage` → nota de voz o audio
  - `documentMessage` → PDF, DOC, etc.
  - `videoMessage` → video corto
- Cada tipo incluye metadatos: `mimetype`, `mediaKey`, `caption` (opcional).
- Se debe extraer el `messageId` (de `data.key.id`) para luego descargar el binario.

**Cambios:**
- Ampliar el bloque de extracción de texto (líneas 46-54 actuales) para detectar media.
- Si hay media, pasar al `buffer_message()` un objeto enriquecido en vez de solo texto.

---

### Sub-spec 11.2 — Descarga de Media desde Evolution API

**Archivo:** `api/services/wa_client.py`  
**Objetivo:** Implementar método `download_media()` que obtenga los bytes del archivo.

**Lógica:**
- Endpoint de Evolution API: `POST {api_url}/s3/getMedia/{instance_name}`
- Payload: `{"id": message_id, "type": media_type, "messageId": message_id}`
- Retorna el archivo en base64.
- Alternativa: Habilitar "Base64 en Webhook" desde la config de Evolution API
  para recibir el archivo directamente en el payload (evita una llamada HTTP extra).

**Cambios:**
- Nuevo método `WhatsAppClient.download_media(message_id, media_type) -> bytes`
- Decodificación base64 → bytes en memoria (sin guardar en disco).

---

### Sub-spec 11.3 — Integración Multimodal en Gemini Client

**Archivo:** `api/services/gemini_client.py`  
**Objetivo:** Extender `generate_response()` para aceptar contenido multimodal.

**Lógica:**
- El SDK `google-genai` soporta nativamente multimodal:
  ```python
  # CONCEPTO — No ejecutar
  from google.genai import types

  # Crear Part con bytes y mimetype
  media_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
  
  response = await client.aio.models.generate_content(
      model='gemini-2.5-flash',
      contents=[media_part, "Describe lo que ves en esta imagen de la palma de la mano"],
      config=config
  )
  ```
- Para archivos grandes (>20MB como videos), usar File API: `client.files.upload()`

**Cambios:**
- Nueva firma: `generate_response(prompt: str, media: list[dict] | None = None) -> dict`
- Cada item en `media` sería: `{"bytes": b"...", "mime_type": "image/jpeg"}`
- Construir `contents` como lista `[Part, Part, ..., texto]` antes de llamar a Gemini.

---

### Sub-spec 11.4 — Adaptación del Message Processor

**Archivo:** `api/services/message_processor.py`  
**Objetivo:** Extender el buffer para acumular tanto texto como media.

**Lógica:**
- Actualmente el buffer es `dict[str, list[str]]` (solo textos).
- Cambiarlo a `dict[str, list[dict]]` donde cada entry es:
  ```python
  # CONCEPTO
  {"type": "text", "content": "Hola, ¿qué ves en mi mano?"}
  {"type": "image", "bytes": b"...", "mime_type": "image/jpeg", "caption": "Mi mano derecha"}
  {"type": "audio", "bytes": b"...", "mime_type": "audio/ogg"}
  ```
- Al procesar el buffer, separar textos y medias para construir el prompt multimodal.

**Cambios:**
- `buffer_message()` acepta objeto enriquecido en vez de solo string.
- `_process_buffer()` construye `contents` multimodal para Gemini.

---

### Sub-spec 11.5 — Prompts Especializados por Tipo de Media

**Archivo:** `api/services/gemini_client.py` (system_rules)  
**Objetivo:** Instruir a Orus cómo responder según el tipo de contenido recibido.

**Lógica:**
- Si recibe **imagen de palma**: Activar modo quiromancia. Analizar líneas, montes, forma.
- Si recibe **nota de voz**: Transcribir y responder al contenido hablado.
- Si recibe **documento PDF**: Leer, resumir y responder preguntas sobre el contenido.
- Si recibe **imagen genérica**: Describir y contextualizar.

**Cambios:**
- Añadir instrucciones al `system_rules` para cada tipo de media.
- Gemini 2.5 Flash maneja la interpretación automáticamente — solo necesita contexto.

---

## Tipos de Media Soportados por Gemini

| Tipo | MIME Types | Límite Inline | Notas |
|------|-----------|--------------|-------|
| Imagen | image/jpeg, image/png, image/webp, image/gif | ~20MB | Soporta análisis detallado |
| Audio | audio/ogg, audio/mp3, audio/wav, audio/aac | ~20MB | Transcripción + análisis |
| Video | video/mp4, video/webm | Usar File API | Para videos > 20MB |
| Documento | application/pdf | ~20MB | Lectura y extracción de texto |

---

## Consideraciones Técnicas

1. **Memoria:** Los bytes de media se mantienen en memoria solo durante el procesamiento.
   No se persisten en disco. Después de enviar a Gemini, se descartan.
2. **Debounce:** Si el usuario envía foto + texto en ráfaga, ambos se acumulan en el
   buffer y se procesan juntos (contexto completo).
3. **Costo de tokens:** Las imágenes consumen más tokens (~258 tokens para una imagen estándar).
   Monitorear uso para evitar exceder cuotas.
4. **Base64 en Webhook:** Evaluar si conviene habilitar el flag "Base64 Webhook" en
   Evolution API para recibir el archivo directo vs. hacer una segunda llamada HTTP.

---

## Orden de Implementación Recomendado

1. **11.2** → Descarga de media (wa_client) — base independiente
2. **11.1** → Extracción del webhook — detección de tipos
3. **11.4** → Adaptación del buffer — soporte multimodal
4. **11.3** → Integración Gemini multimodal — el cerebro
5. **11.5** → Prompts especializados — el refinamiento

---

## Criterios de Aceptación

- [x] Orus recibe una foto de palma y responde con análisis de quiromancia.
- [x] Orus recibe una nota de voz y responde al contenido hablado.
- [x] Orus recibe un PDF y resume su contenido.
- [x] Media + texto en ráfaga se procesan como una sola intención.
- [x] No se guardan archivos en disco (solo bytes en memoria temporal).
