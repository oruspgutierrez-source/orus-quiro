# Spec 40: Activación de OpenRouter y Análisis de Facturación (Google AI Studio vs. OpenRouter)

Este informe detalla el análisis del cambio de políticas de facturación de Google AI Studio, la respuesta a la duda sobre la consciencia de los límites de tokens en los Modelos de Lenguaje (LLMs), la confirmación de la activación de OpenRouter y la migración de rutas adicionales para blindar el sistema ante caídas de API.

---

## 1. Análisis de Facturación de Google AI Studio (Prepagos y Bloqueos)

### ¿Por qué Google exige prepago?
Google AI Studio/Cloud ha implementado de forma global un **modelo de facturación prepagada obligatoria** (Pay-as-you-go / Prepaid) para las cuentas de nivel de entrada o de reciente creación en la API de Gemini:
1. **Control de Abuso e Impagos**: Para evitar que cuentas fantasmas generen cobros post-pagos no cobrables (bad debt), Google obliga a realizar una recarga inicial mínima en saldo.
2. **Límites de Uso**: En cuentas de tipo prepago, la API se suspende inmediatamente al agotarse el saldo precargado.
3. **Monto Mínimo (R$ 100 / $10 USD)**: Dependiendo del país (por ejemplo, en Brasil o Colombia), la plataforma exige un prepago inicial mínimo (comúnmente equivalente a 100 Reales o 10 Dólares) para habilitar el uso comercial de producción estable (Tier 1 de pago) sin las limitaciones agresivas del Tier gratuito.

### ¿Se pueden usar tarjetas normales?
*   **Sí, pero con restricciones**: Google Cloud acepta tarjetas de crédito o débito estándar internacionales. 
*   **Tarjetas virtuales y prepagadas**: Las tarjetas virtuales de un solo uso o prepagadas suelen ser **rechazadas** o disparan bloqueos de seguridad temporales del sistema de pagos de Google.

---

## 2. Consciencia de Límites de Tokens en LLMs

El usuario plantea una pregunta crucial: *¿Aumentar el límite de tokens en la llamada de la API incita al LLM a dar respuestas más largas, o el LLM no es consciente de estos límites?*

*   **Inconsciencia del Límite de la API**: Los LLMs **no son conscientes** del parámetro `max_tokens` enviado en el payload de la API. El modelo genera texto token por token de forma probabilística hasta que:
    1.  Decide de forma natural terminar la generación (emitiendo un token especial de fin de texto como `<|im_end|>` o `[##EOS##]`).
    2.  La infraestructura de la API corta la respuesta a la fuerza al alcanzar el valor exacto de `max_tokens` (causando respuestas truncadas o JSONs corruptos).
*   **Consecuencias de un límite de tokens elevado**:
    *   **No incrementa el tamaño de la respuesta por sí mismo**: Si el LLM tiene instrucciones de ser conciso, terminará su respuesta rápidamente (ej. 150 tokens) aunque el límite configurado sea 1000.
    *   **Evita el truncamiento accidental**: Proporcionar un límite amplio (ej. 1000 tokens) asegura que respuestas complejas o listados largos de horarios/precios se completen de manera íntegra y sin corromper el formato JSON.

---

## 3. Estado de la Activación de OpenRouter en el Backend

El sistema de Orus ya se encuentra operando de forma 100% nativa con **OpenRouter** en producción, eliminando los riesgos de cuota de Google AI Studio.

### Detalles de la Configuración Activa
*   **Archivo**: `api/services/gemini_client.py`
*   **Variables de Entorno**:
    *   `OPENROUTER_API_KEY`: Cargada y configurada con saldo activo.
    *   `OPENROUTER_MODEL`: Apuntando a `google/gemini-2.5-flash` para mantener el mismo comportamiento inteligente a bajo coste.
*   **Blindaje ante Truncamiento**: Se implementó el parámetro `"max_tokens": 1000` y un bucle de reintento en caliente que inyecta una instrucción de concisión al prompt si el JSON de salida no termina con la llave de cierre `}`.

---

## 4. Cambios Realizados: Migración de la Ruta de Análisis de Logs

Durante la inspección de la base de código, se detectó una dependencia oculta del SDK de Google Gemini directo (`google-genai`) en la ruta de backend `/api/logs/analyze`. 

Para evitar cualquier error inesperado debido a la falta de facturación en Google Cloud:
1.  **Refactorización**: Se modificó `api/routes/logs.py` para redirigir las peticiones de análisis de logs a **OpenRouter** a través del cliente HTTP asíncrono (`httpx`).
2.  **Unificación**: Ambas rutas de IA del backend ahora consumen el mismo backend de OpenRouter de forma unificada.

---

## 5. Próximos Pasos (Despliegue)

Para subir estos cambios a producción en la VPS de EasyPanel:
1.  Hacer git push a la rama `main`.
2.  Disparar el deploy asíncrono del backend mediante el comando curl provisto en `INSTRUCCIONES_AGENTE.md`.
