# Spec 31: Multimodal Human Inbox (Recepción de Archivos en Dashboard)

## 1. Objetivo
Permitir que el administrador, a través del **Inbox Chat** en el Dashboard, pueda recibir y visualizar imágenes, audios y documentos enviados por los consultantes a través de WhatsApp, **específicamente cuando la sesión se encuentra en modo `HUMAN`**.

## 2. Contexto Actual
Actualmente, el bot es multimodal: recibe eventos de `imageMessage`, `audioMessage` y `documentMessage` desde la API de Evolution y es capaz de descargar los `bytes` de esos archivos para procesarlos con el LLM (Gemini 2.0 Flash) durante una conversación manejada por IA.

Sin embargo, cuando la sesión está en modo `HUMAN` (intervención manual):
- El sistema detecta el mensaje multimedia.
- Genera un texto plano como `[Adjunto 1: image sin texto]`.
- Guarda ese texto en `orus_messages` y descarta los bytes del archivo.
- Como resultado, el administrador en el Dashboard solo ve el aviso de que se envió un archivo, pero no puede verlo ni escucharlo.

## 3. Propuesta de Solución (Flujo Técnico)

Para lograr que los archivos multimedia lleguen al Dashboard sin perderse, se propone el siguiente flujo:

### 3.1. Creación de un Bucket de Almacenamiento
*   Se requerirá crear (si no existe) un nuevo bucket en Supabase Storage (por ejemplo, `inbox_media` o reutilizar alguno existente como `biometrics` pero en una carpeta separada). Este bucket deberá ser público para lectura, de modo que el Dashboard pueda renderizar los archivos mediante sus URLs.

### 3.2. Modificación del `message_processor.py`
Cuando se detecten elementos multimedia en la lista `media_list` y el `session_mode` sea `'HUMAN'`:
1.  Iterar sobre cada archivo de la lista.
2.  Generar un nombre único para el archivo (ej. usando UUIDs y la extensión correcta).
3.  Subir los bytes del archivo al bucket de Supabase usando el cliente de Supabase.
4.  Obtener la **URL pública** del archivo recién subido.
5.  Reemplazar las etiquetas crudas en el texto del mensaje (ej. `[Adjunto 1: image sin texto]`) por un formato estandarizado que el Dashboard pueda interpretar. Por ejemplo, utilizando Markdown:
    *   Imágenes: `![Imagen de usuario](https://ruta-del-bucket/imagen.jpg)`
    *   Audios: `[Audio Adjunto](https://ruta-del-bucket/audio.mp3)`
    *   Documentos: `[Documento Adjunto](https://ruta-del-bucket/doc.pdf)`

### 3.3. Modificación del Dashboard (`InboxChatView.jsx`)
Actualmente, los mensajes se renderizan como texto plano en el componente:
`<p className="whitespace-pre-wrap">{msg.content}</p>`

Se requerirá actualizar este componente para que reconozca los enlaces de imágenes o audios dentro del `content` y los renderice adecuadamente usando etiquetas HTML:
*   Para imágenes: Usar la etiqueta `<img src="..." />`.
*   Para audios: Usar la etiqueta `<audio controls src="..." />`.
*   Para otros archivos: Renderizar como un enlace cliqueable con un ícono de documento o clip (`<a href="..." target="_blank">Descargar Documento</a>`).

*Se puede usar una librería ligera como `react-markdown` o crear una función sencilla con expresiones regulares (`Regex`) que busque los formatos preestablecidos en el texto.*

## 4. Beneficios
*   **Visibilidad completa:** El administrador no tendrá puntos ciegos cuando asuma el control manual de la conversación.
*   **Flexibilidad:** El usuario final (consultante) podrá enviar comprobantes de pago, fotos de resultados o notas de voz si requiere explicar algo complejo al administrador.
*   **Eficiencia:** No se satura al LLM con invocaciones innecesarias de análisis de imágenes o audios cuando el usuario está explícitamente hablando con un humano.

## 5. Siguientes Pasos
1.  Configurar las políticas de seguridad (RLS) en el bucket de Supabase para permitir la subida desde el Backend y la lectura pública.
2.  Implementar la lógica de subida (Upload) en el bloque `if session_mode == 'HUMAN':` de `message_processor.py`.
3.  Implementar la capa de parseo en `InboxChatView.jsx` para convertir los URLs adjuntos en reproductores o visores web.

## 6. Estado Actual (05/06/2026) - COMPLETADO
La integración multimodal para el Inbox Chat se ha implementado y estabilizado exitosamente en producción:
- **Almacenamiento**: Creado el bucket `inbox_media` en Supabase con políticas de acceso público habilitadas.
- **Procesamiento y Frontend**: `message_processor.py` fue actualizado para interceptar medios (imágenes, audios, documentos) en sesiones `HUMAN`, almacenarlos y convertirlos a sintaxis Markdown en los mensajes. El dashboard (`InboxChatView.jsx`) parsea este Markdown para presentar los elementos UI correctos (visor de imagen, reproductor nativo `<audio>`, o botón de descarga).
- **Hardening / Fix de Evoltuion API (Error 403)**:
  - Se descubrió que la descarga asíncrona de Evolution API (`getBase64FromMediaMessage`) provocaba rechazos HTTP 403 por parte de los servidores de Meta (WhatsApp CDN) de manera esporádica (especialmente en imágenes reenviadas o cargadas desde WhatsApp Web).
  - **Solución implementada:** Se actualizó la configuración global del Webhook en Evolution API (archivos `register_prod_webhook.py` y relacionados) estableciendo `"webhookBase64": true`. Esto obliga a Evolution a enviar el Base64 *dentro del payload inicial*, anulando la necesidad de realizar peticiones adicionales y mitigando definitivamente los bloqueos 403.
  - El backend ahora extrae de inmediato el archivo desde el webhook y lo deposita en Supabase Storage sin fallos.
