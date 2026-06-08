# Bitácora de Sesión — Orus Quiro Bot

**Última actualización:** 2026-06-06 12:15 BRT
**Estado:** Servidores Operativos en Producción | Spec 33 Completado (Resolución LID & Deduplicación) [NOTA: El Dashboard está en la VPS/EasyPanel. Lo único en Vercel es la app Biométrica].

---

## 🎯 Spec 33 Activo: Resolución de Routing LID y Deduplicación de Mensajes

**Objetivos Estratégicos Acordados:**
1. **[X] Normalización de Linked IDs (@lid):** Diseñar un parser e integrador en `wa_client.py` y `webhooks.py` capaz de resolver un JID real de WhatsApp (`@s.whatsapp.net`) a partir del ID encriptado de enlace (`@lid`) consultando la base de datos de Supabase o consumiendo el endpoint `/contact/findContacts` de Evolution API.
2. **[X] Deduplicación y Consistencia de Memoria:** Reducir la cantidad de workers de Uvicorn en `Dockerfile` de 4 a 1 para asegurar que el espacio de memoria donde residen los temporizadores de debounce y el registro de mensajes vistos (`_seen_messages`) sea consistente, erradicando los envíos duplicados hacia los celulares de los usuarios.
3. **[X] Documentación del Flujo de Despliegue (EasyPanel Webhooks):** Registrar el flujo para desencadenar el despliegue automático del backend y el dashboard programáticamente desde SSH sin requerir la intervención manual del navegador.

---


## 🎯 PRÓXIMA SESIÓN: Protocolo de Hard-Reset Criptográfico y Refactorización del Routing (Spec 33)

**Problemas Críticos Pendientes:**
1. **Fallo de Encriptación de Meta ("Waiting for message"):** El celular del admin sigue en un loop de "Esperando mensaje" debido a corrupción de llaves / caché de Redis en Evolution API o copias de seguridad corruptas en Google Drive.
2. **Caos en el Routing `@lid`:** El parche del `@lid` implementado hoy falló en el caso de respuestas directas desde notificaciones/mensajes del dashboard. Un usuario (la novia) respondió y su mensaje entró al sistema con el ID cifrado `@lid`. El bot le respondió a ese ID cifrado, por lo que el mensaje se quedó en el Dashboard y jamás llegó a WhatsApp.

**Hoja de Ruta Acordada para la Siguiente Sesión:**
Antes de tocar código a ciegas o improvisar:
1. **Auditoría Documental:** Buscar e investigar la documentación oficial de Evolution API v2 respecto a `@lid` (Linked IDs) y el manejo de flujos híbridos (JID normal vs LID).
2. **Prueba y Error Estructurado:** Crear un entorno seguro para inyectar payloads reales capturados de los logs y diseñar un parser/resolver de LIDs que sea 100% infalible antes de pasarlo a producción.
3. **Hard-Reset Sincronizado:** 
   - *Cliente:* Eliminar chat, desconectar dispositivos, backup limpio. Desinstalar WhatsApp.
   - *Servidor:* Destruir instancia en EasyPanel, purgar Redis, limpiar logs.
   - *Reconexión:* Instalar limpio y emparejar bot desde cero.
4. **Alarma Anti-Amateur:** Establecer el sistema de telemetría para que detecte estos quiebres a nivel API y avise por Telegram en tiempo real.

---

## 🛠️ Trabajo Realizado (Sesión Actual — Spec 32: Handover Dinámico y Amnesia Controlada)

### 1. Intervención Unilateral (Takeover)
- Se implementó el endpoint `POST /api/users/{user_id}/takeover` en el backend para permitir al admin forzar el modo `HUMAN`.
- El Dashboard fue actualizado con el botón **"👨‍💻 Tomar Control"**.

### 2. Handback Contextual Inteligente
- Se agregó una interfaz desplegable (dropdown) al botón **"Devolver al Bot"** en `InboxChatView.jsx`. El administrador ahora puede proporcionar instrucciones invisibles para guiar el regreso del bot.
- El endpoint `/resolve` ahora acepta este texto y lo inserta en `orus_messages` con la etiqueta especial `[SYSTEM_NOTE]`.

### 3. Amnesia Controlada
- Se reescribió la lógica de consulta histórica del bot en `message_processor.py`. Si el iterador detecta una etiqueta `[SYSTEM_NOTE]`, inserta una instrucción interna para el LLM y **corta el historial**, volviendo invisible todo lo anterior al "takeover".

### 4. Directivas Multimodales del Agente
- Se corrigió el `gemini_client.py` para prohibir explícitamente al bot interpretar imágenes de manos (redireccionando su rol a asistente de recolección clínica).
- Se garantizó que procese notas de voz para dirigir hacia el embudo de ventas sin solicitar transcripciones.

---

## 🛠️ Trabajo Realizado (Sesión Actual — Spec 31: Multimodal Inbox & Corrección de Routing LID)

### 1. Corrección Crítica de Routing (@lid)
- **Extracción de Sender Real en Webhooks:** Se identificó que WhatsApp Cloud API/Evolution API v2 enmascara a ciertos usuarios provenientes de ads/botones con el sufijo `@lid`, lo cual causaba errores `400 Bad Request` al intentar enviarles mensajes proactivos (ej. desde el dashboard o durante handovers automáticos). Se modificó `api/routes/webhooks.py` para extraer el `sender` real (formato `@s.whatsapp.net`) desde la raíz del payload, puenteando completamente la restricción de LIDs.
- **Sincronización en Base de Datos:** Los registros de usuarios bloqueados bajo IDs de `@lid` fueron actualizados en Supabase con su JID real, normalizando la capacidad de enviar y recibir mensajes desde el Dashboard.

### 2. Visibilidad de Transición Handover
- **Registro de Interacciones Fantasma:** Se reestructuró la lógica de escalado a humanos en `api/services/message_processor.py`. Anteriormente, cuando el bot detectaba una intención de hablar con una persona (keywords como "humano", "persona") y entraba en modo `CONFIRMING_HANDOVER`, el prompt que le enviaba al usuario ("He detectado que deseas hablar con un humano...") no se almacenaba en `orus_messages`. Esto causaba confusión en el Dashboard. Ahora, todos los prompts transicionales generados por la máquina de estados se inyectan explícitamente en el historial del Dashboard.

### 3. Integración Inbox Multimodal (WhatsApp)
- **Pipeline Webhook-to-Base64:** Resolución de errores 403 de descarga estandarizando la ingesta de contenido multimodal (imágenes, audios). Las resoluciones de las imágenes se mantienen originales según las entrega WhatsApp; el backend no las comprime.
- **Renderizado en Admin Chat:** Las imágenes y audios enviados vía WhatsApp ahora se capturan de forma fiable en la base de datos y se renderizan en la interfaz de chat del administrador (Orus Dashboard).

### 4. Optimización Orus Dashboard UI & Backend
- **Gestión de Notas Clínicas (Google Calendar):** Sincronización backend en producción mediante variables de entorno para que la Bitácora recupere y muestre citas en tiempo real.
- **Fix de Eliminación Inmediata:** Modificado `CalendarView.jsx` para recuperar y asignar el UUID real de Supabase tras la creación optimista de notas.
- **Mejora UX en Lectura:** Implementado un Modal Flotante (Pop-Up oscuro centrado) con scroll propio para leer las notas sin interrupciones.

---

## 🛠️ Trabajo Realizado (Sesión Anterior — Spec 26: Migración VPS Dashboard)

### 1. Inicialización y Arranque de Servidores (Segundo Plano)
* **Backend Uvicorn:** Reactivado en el puerto `8000` con recarga automática activa (`--reload`).
* **ngrok:** Túnel levantado exitosamente en `https://annually-murmuring-reuse.ngrok-free.dev`.
* **Registro de Webhook Dinámico:** Ejecución exitosa de `register_webhook.py`, enlazando dinámicamente ngrok a la Evolution API con la escucha activa de `MESSAGES_UPSERT`. El pipeline interactivo de comunicaciones está **100% operativo**.

### 2. Diagnóstico y Planificación del Spec 23 (Blindaje e Intercepción)
* **Diagnóstico de Caídas de Contexto:** Se documentó que el bot presentaba fallas en el formateo conversacional (devolviendo texto vacío `Raw: ` y gatillando mensajes de error de sistema) tras la ejecución de herramientas asíncronas de despacho de audios.
* **Diseño del Spec 23:** Se redactó y consolidó formalmente el [spec_23_homologacion_flujo_y_blindaje_errores.md](file:///c:/Users/Pichau/Documents/proyectos%20antigravity/proyecto%20orus-quiro/specs/spec_23_homologacion_flujo_y_blindaje_errores.md).
* **Homologación Conversacional:** Diseñado el patrón de **Intercepción Silenciosa** mediante tokens de control (`[AUDIO_ENVIADO]`, `[COBRO_ENVIADO]`, `[SILENT_FALLBACK]`) para el backend (`message_processor.py`) y Gemini (`gemini_client.py`), evitando de forma absoluta la duplicación de textos redundantes enviados a WhatsApp en segundo plano.
* **Blindaje Antierosivo:** Diseñado el capturador preventivo de respuestas vacías del modelo en el formateador para inyectar fallbacks estructurados seguros sin interrumpir el flujo.
* **Continuidad Robusta:** Almacenado el Plan de Implementación (`implementation_plan.md`) y la lista de tareas atómicas (`task.md`) en los artefactos del cerebro actual de Antigravity para asegurar que cualquier agente de la versión 2.0 pueda retomar el proceso atómicamente si la sesión se interrumpe de forma inesperada.

---

## 🛠️ Trabajo Realizado (Sesión 2026-05-23 — Spec 18: Identidad Cognitiva El Escultor)

### Cambios Realizados
- **Task 1 — `gemini_client.py` (system_rules):** Se reemplazó la identidad mística del bot por el arquetipo clínico "El Escultor". Nuevas instrucciones: prohibición absoluta de emojis y terminología vedas/mágico/namasté, vocabulario biosemiótico oficial (auditoría biosemiótica, hardware biológico, mapa neurobiológico), texto de acogida Fase 1 hardcodeado, y flujo conversacional por fases explicitado en el prompt.
- **Task 2 — `gemini_client.py` (docstrings):** Docstrings de `send_introductory_audio()` y `generate_payment_link()` actualizadas. Eliminadas referencias a "quiromancia védica" y "proceso védico". Las condiciones de disparo de cada tool ahora están alineadas al nuevo flujo de fases.
- **Task 3 — `payments.py`:** Mensaje de confirmación post-pago actualizado al guión de Fase 3.5 del `guiabot.html`. Incluye ID de transacción, tono clínico y transición directa al agendamiento.
- **Task 4 — `calendar_client.py`:** Texto de guías de agenda y mensaje biométrico post-agendamiento actualizados al guión de Fase 5. Tono directo, sin informalidad, sin emojis.

### Referencia
- Spec documentado en: `specs/spec_18_identidad_cognitiva_escultor.md`
- Guía visual de referencia: `guiabot.html`

---


---

## 🛠️ Trabajo Realizado (Sesión 2026-05-20)

### 1. Inicialización y Automatización de Entorno (Completo)
- **Servidores en Segundo Plano:** Se levantaron con éxito el backend **Uvicorn** en `http://127.0.0.1:8000` (con variable `PYTHONUTF8=1` para blindar la terminal contra emojis) y el túnel **ngrok**.
- **Registro de Webhook Dinámico:** Se ejecutó con éxito el script `register_webhook.py`. Se detectó automáticamente la URL de ngrok (`https://annually-murmuring-reuse.ngrok-free.dev`) y se registró dinámicamente en el servidor de **Evolution API** (`https://217.196.61.72`) de producción, activando la escucha de `MESSAGES_UPSERT`. El flujo de comunicaciones está **100% operativo**.

### 2. Decisiones de Arquitectura y Refactor de Especificaciones
- **Stripe como Pasarela Exclusiva (Spec 15):** Tras la investigación de mercado y foros de creadores en Brasil, se oficializó el uso de **Stripe** como el único procesador de pagos internacional y nacional.
  - **Motivo de la decisión:** Mercado Pago en Brasil procesa de forma nativa en BRL (Reales), introduciendo enorme fricción al cliente internacional (cobros presentados en BRL, impuestos cambiarios extra) y altos índices de rechazo en su filtro de fraude. Stripe permite cobros en USD/EUR localizados al español, gestionando la conversión e ingreso de divisas de forma automatizada y legal ante el Banco Central de Brasil.
  - **Modificación:** Se actualizó [spec_15_pasarela_pago_webhooks.md](file:///c:/Users/Pichau/Documents/proyectos%20antigravity/proyecto%20orus-quiro/specs/spec_15_pasarela_pago_webhooks.md) para reflejar a Stripe como la única pasarela del alcance técnico, eliminando Mercado Pago.

### 3. Optimización de Arranque para la Siguiente Sesión
- **Modificación de INSTRUCCIONES_AGENTE.md:** Se rediseñó el protocolo de arranque rápido en [INSTRUCCIONES_AGENTE.md](file:///c:/Users/Pichau/Documents/proyectos%20antigravity/proyecto%20orus-quiro/INSTRUCCIONES_AGENTE.md) para que el próximo agente lea exclusivamente el **Plan de Implementación Maestro** activo de la sesión actual en el cerebro.

### 4. Importación y Verificación del Audio de Acogida Real (Spec 14)
- **Resolución:** Se localizó el audio master explicativo en `c:\Users\Pichau\Documents\boipeba\1223.MP3` (2 minutos y 49 segundos).
- **Conversión y Compresión:** Se empleó `ffmpeg` con códec `libopus` (Ogg Opus) limitando el bitrate a 24 kbps. Tamaño final: 528 KB.
- **Test E2E Directo:** Validado con éxito. Evolution API respondió `201 Created`, `seconds: 169`, `ptt: true`.

---

## 🛠️ Trabajo Realizado (Sesión 2026-05-21 — Fase 2)

### 1. Eliminación Definitiva de Visualización en Local
- Se removieron por completo las referencias y carpetas de visualización local (`invoice-designer/`). El renderizado de facturas opera exclusivamente con motor PDF nativo en `api/services/billing.py`.

### 2. Implementación de Guías de Agendamiento Visual (Spec 13)
- **Secuencia Asíncrona de Imágenes:** Implementada en `api/services/calendar_client.py` con la subrutina `send_visual_agenda_protocol`:
  1. **Imagen 1 (`1trespuntos.jpeg`):** Tres puntos en la esquina superior derecha.
  2. **Imagen 2 (`2copiaren.jpeg`):** Opción "Copiar en...".
  3. **Imagen 3 (`3micalendario.jpeg`):** Opción "Mi calendario".
- **Delays:** 2.0 segundos entre cada paso para garantizar orden de llegada correcto en WhatsApp.
- **Enlace Final:** `htmlLink` oficial de Google Calendar despachado al concluir las guías.

### 3. Pipeline de Pago Stripe → Agendamiento (Spec 15 → Spec 13)
- **Webhook de Stripe operativo:** El endpoint `/payments/webhook` valida firma criptográfica, actualiza Supabase (`payment_status = 'paid'`), envía alerta de Telegram y despacha la factura PDF premium por WhatsApp.
- **Step 5 — Trigger de Gemini Post-Pago:** Implementado en `payments.py` (líneas 108–164). Al finalizar el envío de la factura, se llama a `generate_response()` con un prompt de trigger interno para que Gemini active proactivamente el Spec 13.
- **Bug Crítico Resuelto:** `NameError: name 'link_generado' is not defined` en `gemini_client.py` — la f-string contenía `{link_generado}` sin escapar. Solucionado con `{{link_generado}}` en la línea 145.
- **Prueba de Pago Exitosa:** Pago simulado con tarjeta `4242...`, factura PDF generada y enviada por WhatsApp.

### 4. Registro de URL del Spec 16 — Web App de Datos Biométricos
- **URL registrada:** `https://ruta-del-escultor.vercel.app/`
- **Plataforma:** Vercel
- **Trigger de envío:** Inmediatamente DESPUÉS de ejecutar `book_appointment()` con éxito y enviar las guías visuales de Google Calendar.
- **Contexto:** El audio explicativo de 3 minutos (Spec 14) ya prepara al consultante para este paso. Orus enviará el link con un mensaje de cierre profesional.
- **Documentación actualizada:** [spec_16_webapp_datos_entrevista.md](file:///c:/Users/Pichau/Documents/proyectos%20antigravity/proyecto%20orus-quiro/specs/spec_16_webapp_datos_entrevista.md)

---

## 🚦 Estado de los Specs

| # | Spec | Estado | Notas |
|---|------|--------|-------|
| 08 | Calendar, Logs & Métricas | ✅ Completo | Totalmente operativo. |
| 11 | Multimodal Vision/Audio/Docs | ✅ Completo | Procesamiento de multimedia integrado. |
| 12 | Estabilización E2E / Unicode / Correcciones | ✅ Completo | Pipeline cognitivo robustecido. |
| 13 | Protocolo Visual de Agendamiento (Guías & WhatsApp) | ✅ Completo | Secuencia de 3 imágenes + enlace de Calendar. |
| 14 | Protocolo de Atención y Flujo de Audios | ✅ Completo | Notas de voz nativas con simulación de grabación 100% operativas. |
| 15 | Pasarela de Pago Stripe y Facturación | ✅ Completo | Stripe + invoice PDF + trigger Spec 13 post-pago implementado. |
| 16 | Web App Datos Biométricos | 🔗 URL Registrada | URL: `https://ruta-del-escultor.vercel.app/` — Pendiente integración de envío en `calendar_client.py` tras `book_appointment()`. |

---

## 🚀 Siguiente Misión (Para la Próxima Sesión)

### Objetivo Principal: Integrar el envío automático del link Spec 16 tras el agendamiento exitoso

1. **Encendido del Entorno:**
   - Levantar Uvicorn: `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
   - Levantar ngrok: `ngrok http 8000 --url=annually-murmuring-reuse.ngrok-free.dev`
   - Registrar webhook: `python register_webhook.py`

2. **Tarea de Código — `calendar_client.py`:**
   - Al final de la función `book_appointment()`, **después** de ejecutar `send_visual_agenda_protocol()` (las 3 imágenes + enlace de Calendar), agregar el envío del mensaje final con el link de la Web App:
     - Mensaje: *"Para completar el proceso, el siguiente paso es registrar tus datos biométricos en nuestro formulario seguro. Encontrarás ahí las instrucciones que ya te explicamos en el audio: https://ruta-del-escultor.vercel.app/"*
   - Respetar un delay asíncrono de ~3 segundos antes de este mensaje final para que llegue después de las guías.

3. **Tarea de Código — `gemini_client.py` (System Prompt):**
   - Agregar en las reglas del Spec 16 que, al finalizar el protocolo de agendamiento exitoso, Orus debe informar al consultante que recibirá el link para registrar sus datos biométricos.

4. **Validación E2E Completa (desde el celular):**
   - Secuencia: Acogida → Audio → Pago Stripe → Factura PDF → Agendamiento Interactivo → 3 Guías Visuales → Link Spec 16.

---

## 🛠️ Notas Técnicas, MCPs y Variables
- **Evolution API URL:** `https://217.196.61.72` (Bypass TLS activo: cabecera `"Host": "whatsapp.orusquiroterapia.online"`, `verify=False` / `ssl=False`).
- **Túnel ngrok actual:** `https://annually-murmuring-reuse.ngrok-free.dev`
- **Uvicorn local:** `http://127.0.0.1:8000`
- **Web App Biométrica (Spec 16):** `https://ruta-del-escultor.vercel.app/`
- **Cerebro Cognitivo:** Gemini 2.5 Flash.
- **Clave Webhook Stripe (TEST):** Vence ~4 horas desde las 19:49 BRT del 2026-05-21. Para la próxima sesión crear una nueva con `stripe listen --forward-to localhost:8000/payments/webhook`.

---

## 🛠️ Trabajo Realizado (Sesión 2026-05-20)

### 1. Inicialización y Automatización de Entorno (Completo)
- **Servidores en Segundo Plano:** Se levantaron con éxito el backend **Uvicorn** en `http://127.0.0.1:8000` (con variable `PYTHONUTF8=1` para blindar la terminal contra emojis) y el túnel **ngrok**.
- **Registro de Webhook Dinámico:** Se ejecutó con éxito el script `register_webhook.py`. Se detectó automáticamente la URL de ngrok (`https://annually-murmuring-reuse.ngrok-free.dev`) y se registró dinámicamente en el servidor de **Evolution API** (`https://217.196.61.72`) de producción, activando la escucha de `MESSAGES_UPSERT`. El flujo de comunicaciones está **100% operativo**.

### 2. Decisiones de Arquitectura y Refactor de Especificaciones
- **Stripe como Pasarela Exclusiva (Spec 15):** Tras la investigación de mercado y foros de creadores en Brasil, se oficializó el uso de **Stripe** como el único procesador de pagos internacional y nacional. 
  - **Motivo de la decisión:** Mercado Pago en Brasil procesa de forma nativa en BRL (Reales), introduciendo enorme fricción al cliente internacional (cobros presentados en BRL, impuestos cambiarios extra) y altos índices de rechazo en su filtro de fraude. Stripe permite cobros en USD/EUR localizados al español, gestionando la conversión e ingreso de divisas de forma automatizada y legal ante el Banco Central de Brasil.
  - **Modificación:** Se actualizó [spec_15_pasarela_pago_webhooks.md](file:///c:/Users/Pichau/Documents/proyectos%20antigravity/proyecto%20orus-quiro/specs/spec_15_pasarela_pago_webhooks.md) para reflejar a Stripe como la única pasarela del alcance técnico, eliminando Mercado Pago.
- **Creación de Plan de Implementación de la Sesión:** Se consolidó el archivo maestro de planeación [implementation_plan.md](file:///C:/Users/Pichau/.gemini/antigravity/brain/68a55262-1e33-4022-8331-3302cf5ec7e0/implementation_plan.md) en el directorio activo del cerebro de Antigravity.

### 3. Optimización de Arranque para la Siguiente Sesión
- **Modificación de INSTRUCCIONES_AGENTE.md:** Se rediseñó el protocolo de arranque rápido en [INSTRUCCIONES_AGENTE.md](file:///c:/Users/Pichau/Documents/proyectos%20antigravity/proyecto%20orus-quiro/INSTRUCCIONES_AGENTE.md) para que el próximo agente lea exclusivamente el **Plan de Implementación Maestro (implementation_plan.md)** activo de la sesión actual en el cerebro. Esto evita el consumo innecesario de créditos analizando múltiples archivos históricos o especificaciones crudas individuales al arrancar.

### 4. Importación y Verificación del Audio de Acogida Real (Spec 14)
- **Problema de origen:** El archivo de audio `.wav` del Escritorio exportado desde FL Studio medía solo 1.85 segundos, causando que el bot enviara un audio de 1 segundo inútil.
- **Resolución:** Se localizó el audio master explicativo en `c:\Users\Pichau\Documents\boipeba\1223.MP3` (2 minutos y 49 segundos).
- **Conversión y Compresión:** Se empleó `ffmpeg` con códec `libopus` (Ogg Opus) limitando el bitrate a 24 kbps de forma nativa. Esto redujo el tamaño a solo 528 KB para asegurar una transferencia ultrarrápida.
- **Test E2E Directo:** Validado con éxito rotundo. Evolution API respondió con código `201 Created`, reportando `seconds: 169` y el estado nativo de nota de voz `ptt: true`.

---

## 🚦 Estado de los Specs

| # | Spec | Estado | Notas |
|---|------|--------|-------|
| 08 | Calendar, Logs & Métricas | ✅ Completo | Totalmente operativo. |
| 11 | Multimodal Vision/Audio/Docs | ✅ Completo | Procesamiento de multimedia integrado. |
| 12 | Estabilización E2E / Unicode / Correcciones | ✅ Completo | Pipeline cognitivo robustecido. |
| 13 | Protocolo Visual de Agendamiento (Guías & WhatsApp) | ✅ Completo | Secuencia de 3 imágenes instructivas y enlace de Calendar. |
| 14 | Protocolo de Atención y Flujo de Audios | ✅ Completo | Notas de voz nativas con simulación de grabación 100% operativas. |
| 15 | Pasarela de Pago Stripe y Facturación | ✅ Completo | Stripe e invoice PDF implementados; pipeline asíncrono robusto. |
| 16 | Web App, Agendamiento y Guías WebP | 📝 Diseñado | Webhook de Supabase planificado. Pendiente codificación. |

---

## 🛠️ Trabajo Realizado (Sesión 2026-05-21 — Fase 2)

### 1. Eliminación Definitiva de Visualización en Local
- **Limpieza del Entorno:** Se removieron por completo todas las referencias, carpetas y archivos locales que servían para la visualización local de facturas (`invoice-designer/` y puertos redundantes de desarrollo). El renderizado de facturas ahora se basa exclusivamente en un motor PDF nativo y premium en `api/services/billing.py`, despachado de manera nativa como documento por WhatsApp.

### 2. Implementación de Guías de Agendamiento Visual (Spec 13)
- **Secuencia Asíncrona de Imágenes:** Para guiar al consultante en el registro manual de su cita dentro de su calendario móvil, se implementó en `api/services/calendar_client.py` la subrutina asíncrona `send_visual_agenda_protocol`:
  1. **Imagen 1 (`1trespuntos.jpeg`):** Le indica al usuario que, al abrir el enlace de la cita agendada, verá tres puntos en la parte superior derecha donde tendrá que hacer clic.
  2. **Imagen 2 (`2copiaren.jpeg`):** Le indica que debe hacer clic en la opción *"Copiar en..."*.
  3. **Imagen 3 (`3micalendario.jpeg`):** Le indica que debe hacer clic en la opción *"Mi calendario"* para registrar la cita automáticamente en su dispositivo.
- **Intervalos de Tiempo:** Se configuró un delay asíncrono de `2.0 segundos` entre cada mensaje e imagen para garantizar que lleguen a la app de WhatsApp del celular en el orden correcto y con sus respectivos captions explicativos.
- **Enlace Final:** Al concluir las guías visuales, se despacha el enlace directo `htmlLink` oficial de Google Calendar para que el consultante registre la cita con un solo toque.

### 3. Refinamiento en las Reglas Cognitivas de Gemini
- **System Prompt:** Se actualizó `api/services/gemini_client.py` reordenando las prioridades conversacionales del modelo. Orus sabe que, inmediatamente después de enviarse la factura de pago (Stripe), se activa proactivamente el protocolo de agendamiento llamando a `check_free_slots`.
- **Descripción del Protocolo:** Se inyectó la descripción detallada de las tres imágenes explicativas del calendario en las reglas de procesamiento exitoso de datos de Gemini para mantener una perfecta sintonía cognitiva entre el LLM y la herramienta `book_appointment`.

---

## 🛠️ Trabajo Realizado (Sesión 2026-05-22 — Fase 3: Integración E2E Web App Biométricos y Confirmación Reactiva)

### 1. Integración de Extremo a Extremo (E2E) para el Spec 16 (Completo)
- **Envío Automatizado:** Al concluir el flujo de guías de Google Calendar en `calendar_client.py`, se implementó un delay asíncrono de **3.0 segundos** seguido del despacho automático del enlace directo a la Web App de Datos Biométricos (`https://ruta-del-escultor.vercel.app/`).
- **Trigger Reactivo de Base de Datos (Supabase):**
  - Se habilitó la extensión `pg_net` para permitir llamadas HTTP desde la base de datos de PostgreSQL en Supabase.
  - Se creó la función `public.handle_evaluacion_completa()` que genera un payload JSON limpio del usuario (inyectando de manera dura `'fotos_completadas': true`) y realiza un `HTTP POST` reactivo a nuestro backend expuesto en ngrok.
  - Se configuró el trigger `tr_evaluaciones_completas_insert` que se dispara `AFTER INSERT` sobre la tabla `public.evaluaciones_completas`.
- **Backend FastAPI (`api/routes/webhooks.py`):**
  - Se expandió el endpoint `/api/biometrics/completed` para recibir el payload POST desde Supabase.
  - El backend extrae el número de teléfono/JID (`wa_id`) y el nombre del consultante, añade el sufijo necesario para WhatsApp, e instruye a la Evolution API a enviar un mensaje formal y empático que confirma el correcto registro biométrico y cierra definitivamente el ciclo conversacional de preparación.
- **Validación:** Validado con éxito absoluto simulando una llamada HTTP reactiva del webhook desde Supabase usando el script de prueba local `scratch/test_biometrics_webhook.py` respondiendo con **HTTP 200 OK**.

### 2. Reinicio de Servidores con Recarga en Caliente (Reload)
- Se cancelaron las instancias antiguas de Uvicorn que operaban sin autorecarga.
- Se levantó exitosamente la nueva tarea del servidor backend **Uvicorn** en `http://0.0.0.0:8000` con la bandera `--reload` activa en segundo plano (ID de tarea: `task-197`). 

## 🚦 Estado de los Specs (Actualizado)

| # | Spec | Estado | Notas |
|---|------|--------|-------|
| 08 | Calendar, Logs & Métricas | ✅ Completo | Totalmente operativo. |
| 11 | Multimodal Vision/Audio/Docs | ✅ Completo | Procesamiento de multimedia integrado. |
| 12 | Estabilización E2E / Unicode / Correcciones | ✅ Completo | Pipeline cognitivo robustecido. |
| 13 | Protocolo Visual de Agendamiento (Guías & WhatsApp) | ✅ Completo | Secuencia de 3 imágenes explicativas y enlace de Calendar. |
| 14 | Protocolo de Atención y Flujo de Audios | ✅ Completo | Notas de voz nativas con simulación de grabación 100% operativas. |
| 15 | Pasarela de Pago Stripe y Facturación | ✅ Completo | Stripe e invoice PDF implementados; pipeline asíncrono robusto. |
| 16 | Web App, Agendamiento y Guías WebP | ✅ Completo | Integración reactiva E2E completada a través de triggers Supabase y webhook FastAPI con confirmación de cierre por WhatsApp. |
| 17 | Agendamiento Proactivo Post-Pago y Blindaje | ✅ Completo | Transición asíncrona post-pago, cálculo de disponibilidad directa en servidor y blindaje de formateador validados. |

---

## 🛠️ Trabajo Realizado (Sesión 2026-05-22 — Fase 4: Auditoría y Suite de Pruebas E2E del Spec 17)

### 1. Levantamiento e Infraestructura Activa (Completo)
- **Servidores en Segundo Plano**: Se reactivaron de forma limpia y persistente el backend **Uvicorn** expuesto en el puerto `8000` (con variable `PYTHONUTF8=1` activa) y el túnel **ngrok** expuesto en el mismo puerto en segundo plano.
- **Registro del Webhook**: Se ejecutó de forma autónoma el script `register_webhook.py`, detectando automáticamente la URL activa del túnel (`https://annually-murmuring-reuse.ngrok-free.dev`) y registrando el endpoint `/webhook` en la Evolution API remota de producción, completando el canal de entrada interactivo al 100%.

### 2. Suite de Pruebas E2E y Certificación del Spec 17 (Completo)
- **Simulación Criptográfica de Stripe**: Se corrió el script simulador de webhooks `scratch/simulate_stripe_webhook.py` enviando un payload de cobro exitoso por un valor de 49.00 USD para el JID `553598869018@s.whatsapp.net` con firma criptográfica HMAC SHA-256 válida.
- **Auditoría del Pipeline**:
  -- **Cálculo y Formateo Directo en Servidor**:
  - El backend calculó de forma dinámica los siguientes 5 días hábiles consecutivos (lunes a viernes comerciales: `25` al `29` de mayo) omitiendo fines de semana.
  - Consultó en caliente la Google Calendar API a través de `get_free_slots_data` para cada día y generó el reporte textual exacto de espacios disponibles.
- **Inferencia Cognitiva y Formateador**:
  - Se verificó que Gemini 2.5 Flash asimile la disponibilidad inyectada de forma directa y genere su JSON de agendamiento de forma limpia en la primera fase.
  - Se validó que el backend fragmente secuencialmente las respuestas de WhatsApp mediante el delimitador `|||` con retrasos asíncronos para simular digitación humana de alta fidelidad.
  - Se auditó el pipeline corrector y el blindaje preventivo del formateador que intercepta outputs vacíos del LLM de forma resilio-cognitiva.

### 3. Parche Correctivo E2E: Erradicación de Alucinaciones y Falsos Pagos (Completo)
- **Falla de Formateador Solucionada**: Se reescribió `FORMAT_INSTRUCTION` removiendo los placeholders confusos `<...>` de la plantilla. Gemini ya no los reproduce textualmente y formatea de manera directa el contenido de las respuestas en JSON limpio.
- **Robustecimiento del Blindaje contra Falsos Pagos**: Se restringió el fallback de agendamiento post-pago de Stripe verificando de forma contextual el prompt. Si el usuario realiza una conversación ordinaria, el bot ya no confirmará pagos falsos si la inferencia llega a fallar, sino que inyecta un fallback conversacional elegante en el tono de "El Escultor".
- **Pruebas de Validación**: Se corrieron simulaciones locales del flujo conversacional para precio y compra de lectura. El bot reconoció las intenciones, llamó con precisión a la herramienta `generate_payment_link` para crear la sesión de Stripe y formateó correctamente el JSON sin alucinaciones de plantillas.

### 4. Reestructuración Profunda y Restauración de Flujo (Completo)
- **Diagnóstico de Quiebre de Estructura**: Se detectó que la sobrecarga del prompt con guiones estrictos y el cambio radical de identidad a "Auditor Clínico" estaba provocando que el LLM perdiera su fluidez conversacional original. Además, los múltiples parches de formateo y fallback manuales interrumpían el *function calling* natural.
- **Restauración de Código Base**: Se revirtió `gemini_client.py` a su estado estructural limpio. Se eliminó la segunda llamada recursiva al LLM y las intercepciones rígidas.
- **Implementación de JSON Nativo**: Se integró exitosamente `response_mime_type="application/json"` directamente en Gemini para garantizar la salida estructurada de `OrusResponse` sin depender de trucos de prompt.
- **Validación Local Exitosa**: El agente recuperó su fluidez respondiendo como asistente de ventas de quiromancia védica, integrando armónicamente las llamadas a funciones de audio y pasarela de pago.

---

## 🛠️ Trabajo Realizado (Sesión 2026-05-23 — Planificación de Reestructuración E2E)

### Diagnóstico y Plan de Implementación
- **Diagnóstico técnico completo:** Se auditó el flujo E2E identificando 8 bugs de raíz: doble confirmación de pago en `payments.py` L84–91, caption redundante en `billing.py`, flujo de audio sin garantía de orden, `check_free_slots()` con dependencia de fechas ISO formateadas por el LLM, y desincronización del pipeline post-agendamiento.
- **Plan de implementación generado:** Se creó el [implementation_plan.md](file:///C:/Users/Pichau/.gemini/antigravity-ide/brain/0ef3811a-c733-4760-b5c6-f68965950b32/implementation_plan.md) con 3 Specs nuevos y sus Tasks atómicas.

---

## 🚀 Siguiente Misión — Specs 19, 20 y 21 (Plan Activo)

> [!IMPORTANT]
> El plan técnico completo está documentado en el [implementation_plan.md](file:///C:/Users/Pichau/.gemini/antigravity-ide/brain/0ef3811a-c733-4760-b5c6-f68965950b32/implementation_plan.md). **Leerlo antes de ejecutar cualquier task.**

### Orden de ejecución secuencial:

**Spec 19 — Embudo de Ventas y Audio** (`specs/spec_19_embudo_ventas_y_audios.md`)
- `Task 19.1` → Rediseño de `system_rules` en `gemini_client.py` con Checklist de Estado Conversacional + FAQ.
- `Task 19.2` → Crear `send_text_then_audio()` en `wa_client.py` + actualizar herramienta `send_introductory_audio()`.
- `Task 19.3` → Agregar sección de manejo de desvíos y preguntas frecuentes al prompt.
- **→ TEST E2E desde el celular antes de avanzar al Spec 20.**

**Spec 20 — Cierre de Pago y Factura Única** (`specs/spec_20_cierre_pago_y_factura_unica.md`)
- `Task 20.1` → Bifurcación 3A/3B (intención implícita vs. explícita) en el prompt de `gemini_client.py`.
- `Task 20.2` → Eliminar bloque `whatsapp_msg` (líneas 84–91) en `payments.py` + actualizar caption de `billing.py`.
- `Task 20.3` → Agregar manejo de objeciones al prompt.
- **→ TEST E2E desde el celular antes de avanzar al Spec 21.**

**Spec 21 — Agendamiento Humanizado** (`specs/spec_21_agendamiento_humanizado.md`)
- `Task 21.1` → Crear `format_availability_table()` en `calendar_client.py` con formato AM/PM tabular.
- `Task 21.2` → Agregar reglas de inferencia de fechas naturales a la FASE 4 del prompt.
- `Task 21.3` → Actualizar `trigger_prompt` en `payments.py` con la tabla de disponibilidad.
- `Task 21.4` → Ajustar delays asíncronos en `send_visual_agenda_protocol()` para orden garantizado.
- **→ TEST E2E final completo desde el celular.**

---

## 🚦 Estado de los Specs

| # | Spec | Estado | Notas |
|---|------|--------|-------|
| 08 | Calendar, Logs & Métricas | ✅ Completo | Totalmente operativo. |
| 11 | Multimodal Vision/Audio/Docs | ✅ Completo | Procesamiento de multimedia integrado. |
| 12 | Estabilización E2E / Unicode / Correcciones | ✅ Completo | Pipeline cognitivo robustecido. |
| 13 | Protocolo Visual de Agendamiento (Guías & WhatsApp) | ✅ Completo | Secuencia de 3 imágenes + enlace de Calendar. |
| 14 | Protocolo de Atención y Flujo de Audios | ✅ Completo | Notas de voz nativas con simulación de grabación 100% operativas. |
| 15 | Pasarela de Pago Stripe y Facturación | ✅ Completo | Stripe + invoice PDF + trigger Spec 13 post-pago implementado. |
| 16 | Web App Datos Biométricos | ✅ Completo | Integración reactiva E2E completada. |
| 17 | Agendamiento Proactivo Post-Pago y Blindaje | ✅ Completo | Transición asíncrona post-pago y blindaje de formateador validados. |
| 18 | Identidad Cognitiva El Escultor | ✅ Completo | System prompt clínico, sin misticismo, vocabulario biosemiótico. |
| 19 | Embudo de Ventas y Audio | ✅ Completo | System prompt con checklist de estado y FAQ. Flujo texto -> audio asíncrono. |
| 20 | Cierre de Pago y Factura Única | ✅ Completo | Bifurcación 3A/3B. Eliminado mensaje redundante y actualizado caption. |
| 21 | Agendamiento Humanizado | ✅ Completo | Tabla AM/PM. Reglas de fechas naturales. Sincronización asíncrona verificada. |
| 23 | Homologación Flujo y Blindaje | ✅ Completo | Implementada intercepción silenciosa e inyección de fallback antierosivo. |
| 26 | Migración VPS Dashboard | ✅ Completo | Dockerfile, Nginx y docker-compose actualizados para EasyPanel. |

---

## 🛠️ Notas Técnicas, MCPs y Variables
- **Evolution API URL:** `https://217.196.61.72` (Bypass TLS activo: cabecera `"Host": "whatsapp.orusquiroterapia.online"`, `verify=False` / `ssl=False`).
- **Túnel ngrok actual:** `https://annually-murmuring-reuse.ngrok-free.dev`
- **Uvicorn local:** `http://0.0.0.0:8000` (con `--reload` y `$env:PYTHONUTF8=1` activos).
- **Cerebro Cognitivo:** Gemini 2.5 Flash.
- **Stripe:** Regenerar `STRIPE_SECRET_KEY` y `STRIPE_WEBHOOK_SECRET` antes de cualquier prueba de pago.

---

## ⏸️ Estado del Proyecto: Pausa por Soporte Técnico (2026-06-07)

* **Motivo:** Pausa preventiva en las pruebas de estrés conversacionales y en el pipeline agentico hasta recibir una respuesta formal del soporte técnico de Google.
* **Acción Tomada:** 
  - Generación del reporte de caídas y falsas cancelaciones en el orquestador (`soporte_caida_procesos_agenticos.md`).
  - Ejecución paso a paso del protocolo de limpieza en caliente de la terminal local (purgado de archivos JSON temporales de test, verificación del puerto 8000 libre y confirmación de ausencia de subprocesos huérfanos de Python).
  - Verificación estática sintáctica de los cambios en `api/routes/webhooks.py`, confirmando que el entorno está estable.
* **Próximos Pasos:** Esperar la resolución del caso por parte del soporte de Google antes de continuar con la ejecución del Spec 35.

---

## 🛠️ Trabajo Realizado (Sesión 2026-06-08 — Resolución de Conflicto de Notas y Estados)

### 1. Detección y Resolución de Conflicto Lógico
- **Detección**: Las notas administrativas (`[SYSTEM_NOTE]`) inyectadas durante los handovers manuales persistían de forma activa en el historial enviado a Gemini en turnos posteriores (nuevas interacciones), provocando contradicciones cognitivas directas ante nuevas fases y resultando en un `[SILENT_FALLBACK]`.
- **Filtro de Notas Obsoletas**: Se modificó `message_processor.py` para ignorar la inyección de `[SYSTEM_NOTE]` como instrucción administrativa activa si ya existe una respuesta del asistente posterior a la misma (lo que indica que la instrucción ya fue ejecutada).
- **Inyección Dinámica de Estado**: Se reestructuró la comunicación con Gemini pasando los campos `payment_status` y `appointment_date` directamente desde Supabase en la consulta de usuario.
- **Reglas de Estado en el Prompt**: Se agregaron reglas de invalidación explícitas en el system prompt de Gemini (`gemini_client.py`) para omitir de forma absoluta las fases previas si el consultante ya está en estado `PAGADO` (redirección directa a agendamiento) o `AGENDADO` (soporte y respuesta cordial).
- **Certificación**: Se diseñó y ejecutó una suite de validación en `scratch/test_gemini_resolution.py` que comprueba el correcto comportamiento en los tres estados lógicos (`pending`, `paid/unscheduled`, `paid/scheduled`).

### 2. Refinamiento de la Fase 4 de Agendamiento (Resolución de Fechas Parciales y Evitación de Redundancia)
- **Detección de Redundancia y Selección Parcial**: Se detectó que si el usuario seleccionaba un día pero no la hora (ej: "Martes 9 de junio"), el bot respondía confirmando el pago nuevamente de forma redundante y solicitando de nuevo elegir el día.
- **Corrección en el Prompt**: Se reescribieron las reglas de la Fase 4 en `system_rules` (`api/services/gemini_client.py`) para:
  1. Evitar por completo repetir el mensaje de confirmación de pago una vez que el usuario ya está interactuando en la fase de agendamiento.
  2. Si el usuario selecciona el día pero no la hora, el bot confirma el día elegido, lista únicamente los horarios correspondientes a ese día, y le pide elegir la hora (sin pedir datos personales ni volver a preguntar el día).
  3. Resolver correctamente el mes y fechas correspondientes a los próximos 5 días hábiles a partir de la fecha del sistema.
- **Certificación**: Se actualizó `scratch/test_gemini_resolution.py` para simular la selección de día sin hora y se certificó que la respuesta de Gemini cumple con las nuevas pautas sin redundancia de pago.
