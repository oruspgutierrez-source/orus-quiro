# Spec 33: Protocolo de Hard-Reset Criptográfico y Refactorización del Routing (LID)

**Estado:** En progreso
**Fecha:** Junio 2026

## 1. Auditoría Documental: El Problema de los `@lid` (Linked IDs)

### ¿Qué es el `@lid`?
El **LID (Linked ID)** es un identificador opaco introducido por Meta/WhatsApp para proteger la privacidad de los usuarios. En lugar de exponer el número de teléfono real (`55XXXXXXXX@s.whatsapp.net`), la API puede entregar un identificador como `1234567890@lid`.
Esto ocurre habitualmente con usuarios provenientes de anuncios (Click-to-WhatsApp), newsletters o en ciertas interacciones híbridas.

### Impacto en Orus Quiro
1. **Fallas de Ruteo:** Cuando el sistema registra a un usuario con `@lid` y luego intenta enviarle un mensaje proactivo, Evolution API o WhatsApp Cloud pueden rechazarlo (400 Bad Request) o el mensaje se pierde porque no resuelve la ruta criptográfica.
2. **Duplicación de Usuarios:** Un mismo usuario puede ser registrado con su JID real y luego con su LID, creando silos de conversación separados en el Dashboard.

### Soluciones Oficiales (Evolution API v2)
1. **Desactivación Global (Recomendada):** Configurar la variable de entorno `WPP_LID_MODE=false` en la instancia de Evolution API (EasyPanel). Esto fuerza a la API a mapear y exponer el JID tradicional en la medida de lo posible.
2. **Mapeo Activo:** Utilizar la caché interna de Evolution API o el endpoint de perfil para mapear `LID <-> JID`. Actualmente, nuestra función `resolve_lid` busca por `pushName` o `profilePicUrl`, lo cual es propenso a fallos si los perfiles son anónimos o no tienen fotos.
3. **Resolución en Webhook:** Utilizar las propiedades `participant` o explorar si la API ya adjunta el JID real en las actualizaciones de contactos (`contact.update`).

## 2. Plan de Hard-Reset Criptográfico

El cliente experimenta el clásico bucle "Waiting for this message. This may take a while", indicando una corrupción en las llaves de encriptación de extremo a extremo (E2EE) entre la sesión web (Evolution API) y el dispositivo principal (celular del administrador). Esto comúnmente ocurre por desincronización del caché en Redis o backups corruptos.

Para solucionar el bucle criptográfico y aplicar la configuración anti-LID, ejecutaremos un Hard-Reset en ambos extremos.

### Fase A: Preparación y Entorno (Servidor)
1. **Modificar Entorno en EasyPanel:**
   - En la configuración de la Evolution API en EasyPanel, agregar/asegurar la variable: `WPP_LID_MODE=false`.
2. **Purgar Instancia:**
   - Detener el contenedor de Evolution API.
   - Purgar la caché de Redis asociada a las sesiones de Evolution API.
   - Destruir la sesión/instancia actual de "Orus" en Evolution API (para forzar la generación de un nuevo código QR/emparejamiento limpio).

### Fase B: Limpieza de Cliente (Celular Admin)
1. **Desvinculación:**
   - Ir a "Dispositivos Vinculados" en el WhatsApp del celular y cerrar la sesión actual.
2. **Limpieza Profunda (Opcional pero recomendada):**
   - Hacer un backup limpio (sin incluir chats corruptos si es posible) o simplemente vaciar la caché de WhatsApp en el dispositivo.

### Fase C: Re-emparejamiento y Telemetría
1. **Generar Nueva Instancia:** Crear nuevamente la instancia en Evolution API.
2. **Escanear QR:** El admin escanea el nuevo QR.
3. **Establecer Alarma Anti-Amateur:** 
   - Refinar el endpoint de webhooks para escuchar eventos de desconexión o errores criptográficos (`connection.update`) y gatillar una alerta a Telegram o al log centralizado de forma prominente.

## 3. Siguientes Pasos
- Proceder con la destrucción de la sesión actual en EasyPanel y la configuración de `WPP_LID_MODE=false`.
- Actualizar el parser de LIDs en `wa_client.py` en caso de que aún se filtren LIDs residuales.

### Tarea 4: Telemetría de Errores y Blindaje de Recepción (Completada)
**Objetivo:** Capturar desconexiones criptográficas de WhatsApp y errores de parsing provocados por cambios en la API de Evolution v2, reportando todo vía Telegram.
**Ejecución:**
- Modificado `api/routes/webhooks.py` para escuchar eventos `connection.update` y disparar alarmas en Telegram si el `state` es distinto a `open` o `connecting`.
- **Hotfix (List Payload):** La versión actual de Evolution API v2 ocasionalmente envía el payload de `data` como una lista (`[dict]`) en vez de un `dict`. Esto generaba un `AttributeError: 'list' object has no attribute 'get'` que colapsaba el servidor con error 500. Se añadió sanitización (`data_debug[0] if isinstance(data_debug, list) else data_debug`) para proteger el parser de fallas y permitir el procesamiento continuo.

### Tarea 5: Bypass de Safety Settings en Gemini (Completada)
**Objetivo:** Prevenir que Gemini genere un `[SILENT_FALLBACK]` (respuesta vacía) cuando el usuario interactúa con la venta y acepta recibir información médica simulada ("Auditoría Biosemiótica").
**Ejecución:**
- **Contexto:** El uso de términos como "diagnóstico", "hardware biológico" o "neuroanatomía" activaba los filtros nativos de protección médica/daño de la API de Gemini (generando un `finish_reason=SAFETY` y texto vacío).
- Modificado `api/services/gemini_client.py` para inyectar `types.SafetySetting` con `BLOCK_NONE` en todas las categorías, desactivando la censura nativa.
- Se forzó estructuralmente la respuesta en JSON usando `response_mime_type="application/json"` en `GenerateContentConfig` para garantizar la estabilidad de la extracción del campo `reply`.
- Añadido log detallado de `finish_reason` si llegara a repetirse.

---
## Criterios de Éxito (Actualizados)
- [x] Variable `WPP_LID_MODE=false` inyectada en EasyPanel.
- [x] Instancia recreada y vinculada limpiamente (nuevo nombre: `orusboth`).
- [x] Telegram recibe alarmas asíncronas si ocurre un fallo de conexión.
- [x] El webhook soporta payloads en formato `list` de Evolution v2 para evitar errores 500.
- [x] Gemini no bloquea respuestas por falsos positivos médicos (Safety = BLOCK_NONE).
- [ ] Flujo End-to-End validado en celular personal sin errores `[SILENT_FALLBACK]`.
