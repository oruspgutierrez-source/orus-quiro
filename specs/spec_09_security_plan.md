# Spec 09: Blindaje, Seguridad y Anti-Spam

> **Protocolo:** REPORT_ONLY — Este documento es exclusivamente analítico y descriptivo. No contiene código ejecutable.
> **Fecha:** 2026-04-27
> **Autor:** Antigravity

---

## 0. Resumen Ejecutivo

Se propone un sistema de seguridad en 4 capas que protege el backend de Orus Quiro contra inyecciones (Prompt Injection, SQLi), spam/abuso, y webhooks no autorizados. Cada capa opera de forma independiente pero complementaria, siguiendo el principio de **defensa en profundidad**.

```
┌─────────────────────────────────────────────────────────────────┐
│                    PETICIÓN ENTRANTE (Meta)                      │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
              ┌────────────────────────┐
              │  CAPA 1: Validación    │
              │  de Firma HMAC-256     │──── Firma inválida ──► LOG (ERROR) ──► 200 OK (silencioso)
              └────────────┬───────────┘
                           ▼
              ┌────────────────────────┐
              │  CAPA 2: Firewall      │
              │  de Usuario (Bloqueo)  │──── is_blocked=TRUE ──► LOG (WARNING) ──► 200 OK (silencioso)
              └────────────┬───────────┘
                           ▼
              ┌────────────────────────┐
              │  CAPA 3: Rate Limiter  │
              │  (Anti-Spam)           │──── Umbral superado ──► BLOQUEAR usuario ──► LOG (WARNING) ──► 200 OK
              └────────────┬───────────┘
                           ▼
              ┌────────────────────────┐
              │  CAPA 4: Sanitización  │
              │  de Texto              │──── Texto limpio ──► enqueue_message()
              └────────────────────────┘
```

---

## 1. Sanitización de Entradas (Anti-Injection)

### 1.1 Ubicación Propuesta
Se crearía un nuevo módulo **`api/services/security.py`** que centraliza toda la lógica defensiva. La función principal sería `sanitize_input(raw_text: str) -> tuple`.

### 1.2 Pipeline de Filtrado (5 etapas)

| Etapa | Nombre | Descripción | Justificación |
|-------|--------|-------------|---------------|
| **F1** | Límite de longitud | Se truncaría el texto a un máximo de **2000 caracteres**. | Un mensaje legítimo de WhatsApp rara vez excede 500 chars. 2000 da margen a usuarios prolijos pero bloquea payloads masivos. |
| **F2** | Caracteres de control | Se eliminarían caracteres no imprimibles (Unicode C0/C1 controls) excepto `\n` y espacios. | Previene inyección de secuencias de escape que podrían corromper logs o explotar parsers. |
| **F3** | Patrones SQLi | Se buscarían patrones de inyección SQL clásica mediante Regex (`'; DROP`, `UNION SELECT`, `OR 1=1`, `--`, etc.) y se neutralizarían escapando comillas simples. | Aunque Supabase usa prepared statements via su SDK, esta capa actúa como red de seguridad adicional contra payloads almacenados. |
| **F4** | Prompt Injection | Se detectarían frases de manipulación de LLM como `"ignore previous instructions"`, `"you are now"`, `"system prompt"`, `"act as"`, `"forget your rules"`. Si se detecta, el texto sería marcado con una flag de advertencia para logging. | Gemini recibe el texto en bruto dentro de `contents`. Un atacante que conozca la estructura podría intentar sobrescribir las `system_rules`. |
| **F5** | Normalización Unicode | Se aplicaría normalización NFC para colapsar caracteres homóglifos (ej. `Ꭵgnore` → `ignore`). | Atacantes sofisticados usan caracteres Unicode visualmente idénticos para evadir detecciones basadas en string matching. |

### 1.3 Valor de Retorno
La función retornaría una tupla `(texto_limpio: str, threat_detected: bool, threat_type: str | None)`.

- Si `threat_detected` es `True`, el orquestador registraría el evento en `orus_logs` pero **aún así procesaría** el mensaje limpio (salvo que el usuario esté bloqueado por otra capa).
- La decisión de no descartar el mensaje ante una amenaza de prompt injection es deliberada: Gemini ya tiene `system_rules` blindadas con Structured Outputs. Simplemente se neutraliza el payload peligroso y se loguea para auditoría.

### 1.4 Punto de Integración
La invocación se haría en **`webhooks.py`**, justo después de extraer `text_body` y antes de llamar a `enqueue_message()`:

```
// PSEUDOCODIGO — NO EJECUTAR
text_body = message.get("text", {}).get("body")
cleaned_text, is_threat, threat_type = sanitize_input(text_body)
SI is_threat:
    insertar_log(severity='WARNING', event_type=threat_type, source=sender_id, raw=text_body)
enqueue_message(sender_id, cleaned_text)
```

---

## 2. Firewall de Usuario (Auto-Bloqueo y Anti-Spam)

### 2.1 Cambio de Esquema en Supabase
Se requeriría agregar una columna a `orus_users`:

```sql
-- DDL PROPUESTO (No ejecutar en fase de análisis)
ALTER TABLE orus_users
ADD COLUMN is_blocked BOOLEAN DEFAULT FALSE;
```

### 2.2 Rate Limiter In-Memory
Se implementaría un diccionario global en `security.py` similar al patrón ya usado en `orchestrator.py` con `active_sessions`.

**Estructura conceptual:**

```
// PSEUDOCODIGO — NO EJECUTAR
rate_limiter = {}
// Formato: { "5521999888777": [timestamp1, timestamp2, ...] }

VENTANA_TIEMPO = 60 segundos
UMBRAL_MENSAJES = 12 mensajes por ventana
```

**Lógica conceptual de `check_rate_limit(sender_id: str) -> bool`:**
1. Se obtendría la lista de timestamps del sender.
2. Se filtrarían los que estén dentro de la ventana de 60 segundos.
3. Si la cantidad supera el umbral (12), se retornaría `True` (bloqueado).
4. Caso contrario, se agregaría el timestamp actual y se retornaría `False`.

### 2.3 Bloqueo Persistente
Cuando `check_rate_limit()` devuelve `True`:
1. Se actualizaría `orus_users` con `is_blocked = TRUE` para ese `phone_number`.
2. Se insertaría un registro en `orus_logs` con `severity = 'WARNING'` y `event_type = 'SPAM_AUTOBLOCK'`.
3. Se enviaría una alerta Telegram al admin con el teléfono del spammer.

### 2.4 Guardia en Webhooks
Antes de procesar cualquier mensaje, se consultaría si el usuario está bloqueado. El flujo conceptual:

```
// PSEUDOCODIGO — NO EJECUTAR
SI sender_id tiene is_blocked == TRUE en DB:
    insertar_log('WARNING', 'BLOCKED_REQUEST', sender_id)
    RETORNAR {"status": "ok"}  // 200 OK silencioso para Meta

SI check_rate_limit(sender_id) == BLOQUEADO:
    marcar_usuario_bloqueado(sender_id)
    insertar_log('WARNING', 'SPAM_AUTOBLOCK', sender_id)
    enviar_alerta_telegram(...)
    RETORNAR {"status": "ok"}  // 200 OK silencioso

// Si pasa ambas capas, continuar al sanitizador y luego al enqueue
```

### 2.5 Desbloqueo Manual
Se propondría un nuevo endpoint en `dashboard.py`:

```
// CONCEPTO
POST /api/users/{user_id}/unblock
→ Actualiza is_blocked = FALSE en orus_users
→ Limpia el rate_limiter in-memory para ese sender
→ Inserta log con event_type = 'MANUAL_UNBLOCK'
```

---

## 3. Validación de Firmas del Webhook (HMAC SHA-256)

### 3.1 Contexto
Meta envía un header `X-Hub-Signature-256` en cada POST al webhook. Este header contiene un hash HMAC-SHA256 del body usando el **App Secret** como clave. Verificar esta firma garantiza que el payload realmente proviene de Meta y no de un atacante.

### 3.2 Variable de Entorno Requerida
Se agregaría al `.env`:

```
// CONCEPTO
META_APP_SECRET=<app_secret_de_la_configuracion_de_meta>
```

### 3.3 Estrategia de Implementación
Se crearía un **middleware de FastAPI** (no un decorador de ruta) para interceptar **solo** las peticiones POST a `/webhook`.

**Lógica conceptual del middleware:**

```
// PSEUDOCODIGO — NO EJECUTAR
FUNCIÓN verify_meta_signature(request):
    app_secret = ENV["META_APP_SECRET"]
    
    SI app_secret está vacío Y ENV["ENVIRONMENT"] == "development":
        // Bypass: en desarrollo local no se valida
        LOG("Signature check bypassed (dev mode)")
        CONTINUAR
    
    signature_header = request.headers.get("X-Hub-Signature-256")
    SI NO existe signature_header:
        insertar_log('ERROR', 'MISSING_SIGNATURE', request.client.host)
        RETORNAR 200 OK silencioso  // No dar pistas al atacante
    
    raw_body = request.body()
    expected_hash = HMAC_SHA256(clave=app_secret, mensaje=raw_body)
    expected_signature = "sha256=" + expected_hash
    
    SI NO comparación_segura(signature_header, expected_signature):
        insertar_log('ERROR', 'INVALID_SIGNATURE', request.client.host)
        RETORNAR 200 OK silencioso  // Silenciar al atacante
    
    // Firma válida, continuar al handler
    CONTINUAR
```

### 3.4 Consideraciones de Seguridad

| Aspecto | Decisión |
|---------|----------|
| **Comparación de hash** | Se usaría `hmac.compare_digest()` de la stdlib de Python para prevenir timing attacks. |
| **Respuesta ante fallo** | Siempre 200 OK. No se retornaría 401/403 porque Meta reintentaría y un atacante obtendría información del estado. |
| **Bypass en desarrollo** | Controlado por la variable `ENVIRONMENT=development`. En producción, el bypass se desactiva automáticamente. |
| **Lectura del body** | FastAPI consume el body stream una sola vez. Se necesitaría usar el hook `request.body()` y almacenar el resultado para que el handler de ruta pueda reutilizarlo. |

---

## 4. Registro de Intrusiones (Logging Centralizado)

### 4.1 Evolución de la Tabla `orus_logs`
Actualmente `orus_logs` tiene: `id`, `error_message`, `stack_trace`, `created_at`, `severity`. Se propone agregar campos para clasificación de eventos de seguridad:

```sql
-- DDL PROPUESTO (No ejecutar en fase de análisis)
ALTER TABLE orus_logs
ADD COLUMN event_type VARCHAR(50),
ADD COLUMN source_identifier TEXT,
ADD COLUMN raw_payload TEXT;
```

| Campo | Uso |
|-------|-----|
| `event_type` | Clasificador del evento: `SPAM_AUTOBLOCK`, `BLOCKED_REQUEST`, `PROMPT_INJECTION`, `SQL_INJECTION`, `MISSING_SIGNATURE`, `INVALID_SIGNATURE`, `MANUAL_UNBLOCK`, `UNICODE_ATTACK`. |
| `source_identifier` | El `phone_number` del usuario o la IP del request, según corresponda. |
| `raw_payload` | El texto original (antes de sanitizar) para auditoría forense. Truncado a 500 chars por seguridad de almacenamiento. |

### 4.2 Función Helper de Logging
Se crearía una función utilitaria en `security.py` para simplificar la inserción:

```
// PSEUDOCODIGO — NO EJECUTAR
FUNCIÓN log_security_event(severity, event_type, source, message, raw_payload=None):
    supabase.table('orus_logs').insert({
        'severity': severity,          // 'WARNING' o 'ERROR'
        'event_type': event_type,       // 'SPAM_AUTOBLOCK', etc.
        'source_identifier': source,    // teléfono o IP
        'error_message': message,       // descripción legible
        'raw_payload': truncar(raw_payload, 500),
    }).execute()
```

---

## 5. Mapa de Archivos Afectados

| Archivo | Acción | Descripción |
|---------|--------|-------------|
| `api/services/security.py` | **CREAR** | Módulo nuevo. Contendría `sanitize_input()`, `check_rate_limit()`, `log_security_event()`, y el diccionario `rate_limiter`. |
| `api/middleware/__init__.py` | **CREAR** | Init del paquete middleware. |
| `api/middleware/webhook_signature.py` | **CREAR** | Middleware de validación HMAC SHA-256. |
| `api/routes/webhooks.py` | **MODIFICAR** | Integrar las guardias de bloqueo, rate limit y sanitización antes de `enqueue_message()`. |
| `api/routes/dashboard.py` | **MODIFICAR** | Agregar endpoint `POST /{user_id}/unblock`. |
| `main.py` | **MODIFICAR** | Registrar el middleware de firma. Agregar variable `ENVIRONMENT`. |
| `.env` / `.env.example` | **MODIFICAR** | Agregar `META_APP_SECRET` y `ENVIRONMENT=development`. |
| `requirements.txt` | **SIN CAMBIOS** | `hmac` y `hashlib` son parte de la stdlib de Python. No se requieren dependencias externas. |

---

## 6. Dependencias Externas

**Ninguna nueva.** Todo el sistema se construiría con la stdlib de Python:
- `hmac` — para HMAC-SHA256
- `hashlib` — para SHA256
- `re` — para detección de patrones (ya importado en `meta_client.py`)
- `unicodedata` — para normalización NFC
- `time` — para timestamps del rate limiter

---

## 7. Orden de Ejecución Propuesto (Micro-Pasos)

Cuando se reciba autorización de ejecución, el plan se descompondría en estos pasos atómicos:

| Paso | Entregable | Validación |
|------|-----------|------------|
| **P1** | Migración SQL: `ALTER TABLE orus_logs` y `ALTER TABLE orus_users` | El CEO confirma vía dashboard de Supabase |
| **P2** | Crear `api/services/security.py` con `sanitize_input()` + `log_security_event()` | Test unitario con strings maliciosos |
| **P3** | Integrar sanitización en `webhooks.py` | Probar con `test_burst.py` modificado |
| **P4** | Agregar rate limiter y guardia de bloqueo en `webhooks.py` | Simular ráfaga de 15 mensajes en 30 segundos |
| **P5** | Crear `api/middleware/webhook_signature.py` | Test con header falso vs. header válido |
| **P6** | Registrar middleware en `main.py` + variables de entorno | `uvicorn main:app --port 8000` sin errores |
| **P7** | Endpoint `/unblock` en `dashboard.py` | Test manual vía cURL |

---

## 8. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Rate limiter in-memory se pierde al reiniciar el servidor | Media | Bajo | Aceptable para MVP. El bloqueo persistente en Supabase (`is_blocked`) sobrevive reinicios. Mejora futura: Redis. |
| False positive en detección de prompt injection | Media | Medio | Los patrones se diseñarían conservadores (frases completas, no palabras sueltas). Se loguea pero no se descarta el mensaje. |
| Body stream consumido por middleware impide lectura en handler | Alta | Alto | Se usaría el patrón de `request.body()` con cache, o un middleware basado en `BaseHTTPMiddleware` con `set_body()`. |
| CORS abierto (`allow_origins=["*"]`) debilita la postura | Baja | Bajo | Fuera del alcance de este Spec. Se recomienda restringir en un Spec futuro de hardening de producción. |
