# Registro de Backend

## Fecha: 2026-06-01
- **Error detectado:** El comando de arranque de Uvicorn vía `Start-Process` no lanzó errores visibles de inmediato, por lo que se reportó éxito de arranque falsamente. Sin embargo, el entorno no tenía las librerías instaladas (`uvicorn`, `fastapi`, etc.), lo que impidió que el servidor levantara internamente causando que el bot no respondiera los mensajes.
- **Corrección:** Se ejecutó `pip install -r requirements.txt` para instalar todas las dependencias necesarias. Una vez finalizado el proceso de instalación con código de salida 0, se volvió a lanzar `uvicorn main:app` asegurando que el servidor esté verdaderamente operativo escuchando en el puerto 8000.
- **Error detectado 2:** ngrok no estaba iniciando debido a la falta de un Authtoken en este equipo, arrojando el error `ERR_NGROK_4018` al intentar usar el dominio estático `annually-murmuring-reuse.ngrok-free.dev`. Como el proceso se lanzaba en segundo plano (`Start-Process`), el error era invisible.
- **Corrección requerida:** El usuario necesita ejecutar `.\ngrok config add-authtoken <TOKEN>` en esta máquina para que el túnel pueda establecerse y enlazar con el webhook de Evolution API.
- **Error detectado 3:** El dominio estático `annually-murmuring-reuse.ngrok-free.dev` está reservado por otra cuenta de ngrok, impidiendo iniciar el túnel para el usuario actual.
- **Corrección:** Se configuró el Authtoken provisto por el usuario y se levantó ngrok usando una URL dinámica aleatoria. Se ejecutó `register_webhook.py` para sincronizar automáticamente el nuevo endpoint con Evolution API de forma exitosa.
- **Error detectado 4:** Gemini devolvía `[SILENT_FALLBACK]` ocasionalmente tras ejecutar un tool, porque el detector escaneaba `contents` en busca del tool, pero el historial de Gemini ya lo había limpiado.
- **Corrección:** En `gemini_client.py`, se implementó un tracker explícito `last_executed_tool` que se registra *antes* de ejecutar cualquier herramienta, asegurando que el detector de fallbacks siempre tenga el estado correcto.
- **Error detectado 5:** En la fase de agendamiento (Fase 4), el bot intentaba pedir los datos (nombre/email) y al mismo tiempo mostrar el resumen ("¿Son correctos?") en un solo mensaje.
- **Corrección:** Se dividió la Fase 4 del System Prompt en tres pasos estrictamente secuenciales (Paso 1: pedir datos y esperar, Paso 2: mostrar resumen y esperar, Paso 3: agendar) usando la instrucción imperativa `ESPERA SU RESPUESTA`.
- **Error detectado 6:** El webhook reactivo pasivo `pg_net` de Supabase (Spec 16) no enviaba el mensaje de WhatsApp a pesar de que la App React cargaba las fotos. Se diagnosticó que la App React guardaba un ID genérico (`usuario_web_...`) en lugar del número de WhatsApp en la tabla `evaluaciones_completas`.
- **Corrección:** Se modificó `calendar_client.py` para enviar la URL de Vercel concatenada con el parámetro `?phone={clean_phone}`, permitiéndole al Frontend de React capturar el teléfono real y guardarlo en la columna `wa_id` de Supabase.

## Fecha: 2026-06-03
- **Acción:** Despliegue en Producción (EasyPanel) con URL `api.orusquiroterapia.online` y conexión segura HTTPS (Traefik). Los webhooks en Evolution API y Stripe se actualizaron para apuntar a la nueva API segura, resolviendo errores de mixed-content en el frontend (Vercel).
- **Error detectado 7:** Vercel cancelaba los builds del Dashboard de React porque accidentalmente se hizo commit de la carpeta `node_modules` en `dashboard-orus`.
- **Corrección:** Se eliminó del historial de git con `git rm -r --cached` y se forzó un redespliegue de Vercel (Production) vía CLI que logró conectar exitosamente `DashboardView.jsx` a Supabase para leer la data en vivo.
- **Error detectado 8:** El pipeline de Gemini crasheaba internamente (`Error crítico en pipeline: No module named 'googleapiclient'`) desde el contenedor de VPS, lo que se traducía en falta total de respuesta en WhatsApp.
- **Corrección:** El archivo `requirements.txt` modificado con los módulos de Google Calendar no había sido subido a GitHub (fuente que usa EasyPanel). Se hizo commit y push del archivo `requirements.txt` y se re-desplegó exitosamente en EasyPanel.

## Fecha: 2026-06-06
- **Error detectado 9 (Routing LID en WhatsApp):** Las respuestas enviadas desde notificaciones/mensajes del dashboard a usuarios que iniciaron el chat desde anuncios/botones utilizaban el identificador cifrado `@lid`. Como Evolution API requiere el JID real (`@s.whatsapp.net`) para despachar de forma proactiva, las respuestas de WhatsApp fallaban y no llegaban al celular del destinatario, a pesar de figurar en el Dashboard.
- **Corrección:** Se implementó un flujo de resolución en `wa_client.py` y `webhooks.py` que consulta la base de datos de Supabase o llama a la Evolution API (`/contact/findContacts`) para buscar el JID real a partir del LID cifrado antes de procesar el webhook y almacenar al usuario.
- **Error detectado 10 (Mensajes duplicados):** Los mensajes se procesaban por duplicado o triplicado cuando provenían de dispositivos móviles reales. Esto ocurría porque `Dockerfile` iniciaba `uvicorn` con `--workers 4`, dividiendo las peticiones entre 4 procesos independientes que no compartían la memoria local (`_seen_messages`, `_debounce_timers` y `_message_buffers`).
- **Corrección:** Se redujo el número de workers en `Dockerfile` a `--workers 1` para unificar el espacio de memoria y garantizar la efectividad del debounce y deduplicación nativos del backend.

## Fecha: 2026-06-09
- **Error detectado 11 (Columnas de Timezone faltantes en Supabase):** Tras desplegar la actualización de agendamiento multi-zona horaria, el bot comenzó a responder únicamente con el mensaje genérico de bienvenida. Al revisar los logs de producción en la VPS (`docker logs`), se identificó la excepción: `Error en validación de usuario: {'message': 'column orus_users.country does not exist', 'code': '42703'}`. Debido a esto, `user_uuid` quedaba en `None` y la máquina de estados fallaba, cayendo permanentemente en la fase inicial de bienvenida de la IA sin poder transicionar o registrar mensajes.
- **Corrección:** Se debe ejecutar la migración SQL descrita en `migrations/add_timezone_columns.sql` en el panel de control de Supabase (SQL Editor) para aprovisionar las columnas `country`, `timezone`, `cached_slots` y `pending_appointment` en la tabla `orus_users`.
  - *Explicación del comportamiento:* El sistema no intenta poblar el país ni la zona horaria al inicio (inician en `NULL` en la base de datos). Sin embargo, la consulta `SELECT` inicial en `message_processor.py` solicita estos campos para verificar el estado de usuarios recurrentes. Si las columnas físicas no existen en la base de datos, PostgreSQL rechaza toda la consulta `SELECT` con error 42703, haciendo fallar el procesamiento del mensaje completo. Al crear la columna con valor por defecto `NULL`, la consulta se ejecuta con éxito desde el inicio y el país solo se registrará cuando el usuario responda la pregunta post-pago.

## Fecha: 2026-06-10
- **Error detectado 12 (Mensaje de WhatsApp finaliza con salto de línea literal \\n):** En los mensajes enviados al usuario al finalizar el flujo de agendamiento, se observaba que al final del mensaje se concatenaba literalmente el string `\n` (barra invertida y 'n') en el dispositivo móvil. Esto ocurría porque:
  1. La respuesta del LLM (OpenRouter) contenía comillas triples/backticks markdown (```json ... ```) envolviendo el objeto JSON.
  2. Debido a esto, `json.loads` tradicional de Python fallaba y el backend utilizaba el *parseador robusto* basado en búsqueda de substrings en crudo (`raw_text`).
  3. El parseador robusto extraía el campo `reply` con los caracteres de escape literales `\n` y `\"` sin deserializarlos (quedando como caracteres reales de barra invertida en el string Python). Al limpiar el token `[##EOS##]`, este escape se enviaba de manera literal a WhatsApp.
- **Corrección:**
  1. Se optimizó la limpieza de Markdown en `gemini_client.py` extrayendo el contenido desde el primer `{` hasta el último `}` de forma robusta antes de intentar `json.loads`. Esto garantiza que `json.loads` sea exitoso en casi el 100% de los casos y decodifique los caracteres de escape correctamente.
  2. Se actualizó el parseador robusto en `gemini_client.py` para reemplazar explícitamente secuencias literales como `\\n` por saltos de línea reales (`\n`) y `\\"` por comillas dobles (`"`) en caso de caída en el parseador manual.
  3. Se añadió un blindaje preventivo en `message_processor.py` que limpia y reemplaza cualquier secuencia de escape literal (`\\n` o `\\"`) en el texto depurado (`reply_clean`) antes de fragmentarlo y enviarlo por WhatsApp.
  4. Se subieron los cambios a GitHub y se verificó el depliegue exitoso en la VPS por SSH, comprobando que el nuevo contenedor backend se levantó correctamente.

- **Error detectado 13 (Visualización cruda de tags internos y escapes en el Dashboard):** Los mensajes en el chat de administración del Dashboard de React (`InboxChatView.jsx`) mostraban la data en bruto guardada en la base de datos de Supabase. Esto exponía tags internos del sistema como `[##EOS##]`, prefijos del buffer del usuario (ej: `[Mensaje de texto independiente]:`, `[Audio transcript]:`) y secuencias de escape literales como `\n` en lugar de saltos de línea renderizados.
- **Corrección:**
  1. Se implementó la función helper `cleanMessageContent(content)` en `InboxChatView.jsx` encargada de:
     - Remover globalmente la marca de fin de conversación `[##EOS##]`.
     - Traducir secuencias de escape literales `\\n` a saltos de línea nativos de JavaScript (`\n`) y `\\"` a comillas dobles (`"`).
     - Eliminar cualquier etiqueta de prefijo con corchetes al principio del mensaje (ej: `[Mensaje de texto independiente]:`) usando el regex `/^\[[^\]]+\]:\s*/`.
  2. Se actualizó la función `renderMessageContent(content)` para aplicar el helper de limpieza a `content` previo a la separación y renderizado de links, imágenes, audios y saltos de línea en el contenedor con estilo `whitespace-pre-wrap`.
  3. Se corrió localmente `npm run build` en el directorio de `dashboard-orus` logrando compilar con éxito y verificar la integridad sintáctica del frontend.

- **Error detectado 14 (Bloqueo de RLS en Supabase para el registro biométrico):** Al finalizar la subida de imágenes en la Web App biométrica (Vercel), la llamada para actualizar `fotos_completadas` a `true` mediante `.update({ fotos_completadas: true }).eq('id', globalRecordId)` devolvía un array vacío `[]` con status HTTP 200 sin aplicar cambios. Esto ocurría porque Row-Level Security (RLS) estaba activo en la tabla `evaluaciones_completas` sin ninguna política que autorizara la operación de `UPDATE` al rol público `anon`, haciendo que Postgrest filtrara silenciosamente la fila e impidiera disparar el trigger del webhook.
- **Corrección:** Se preparó la migración SQL en `spec_43_fix_rls_biometrics.md` para crear la política RLS que permite operaciones `UPDATE` al rol `anon`:
  ```sql
  CREATE POLICY "Permitir update a usuarios anónimos" 
  ON public.evaluaciones_completas 
  FOR UPDATE 
  TO anon 
  USING (true) 
  WITH CHECK (true);
  ```

## Fecha: 2026-06-11
- **Acción 1:** Reemplazo del audio explicativo del proceso (`explicacion_proceso.ogg`) por el nuevo archivo `audio final` provisto por el usuario.
- **Detalle técnico:** Se transcodificó el archivo MP3 a formato OGG Opus optimizado para WhatsApp (mono, canal único, bitrate de 32k) usando una utilidad local que descarga ffmpeg de manera estática y segura. Se reemplazó el archivo directamente en `resources/media/audios/explicacion_proceso.ogg` para que el backend lo sirva de forma automática en la fase correspondiente.
- **Acción 2:** Corrección del texto del mensaje final enviado al usuario tras completar la carga biométrica en `api/routes/webhooks.py`.
- **Detalle técnico:** Se cambió la frase "nuestra charla de Revelación" por "nuestra charla de mapeo" en la variable `msg_text` dentro de la ruta `biometrics_completed` (`/api/biometrics/completed`).
