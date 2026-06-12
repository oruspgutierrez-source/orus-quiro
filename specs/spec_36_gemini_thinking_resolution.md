# Spec 36: Resolución de Conflictos Cognitivos en Gemini 2.5 Flash (Thinking Tokens vs Function Calling)

## 1. Naturaleza del Problema a Resolver
Se ha identificado una incompatibilidad crítica entre la **racionalidad (capacidad de seguir reglas complejas)** y la **estabilidad de ejecución (Tool Calling)** en el agente Orus impulsado por `gemini-2.5-flash`.

*   **Conflicto Inicial (`SILENT_FALLBACK`):** Al tener activados los *thinking tokens* (comportamiento por defecto de 2.5 Flash), el modelo generaba firmas de pensamiento (`thoughtSignature`) para planificar sus herramientas. Sin embargo, en ciertos cruces de estado, el modelo generaba *únicamente* tokens de pensamiento sin transición a una llamada a función o texto final, resultando en respuestas vacías (`parts=None` o sin texto) que disparaban el mecanismo de seguridad `SILENT_FALLBACK`.
*   **Intento de Mitigación (Causante de Alucinaciones):** Se desactivó el presupuesto de pensamiento mediante `thinking_budget=0`. Esto resolvió el problema técnico de las respuestas vacías (el modelo ejecutaba las herramientas inmediatamente), pero eliminó su capacidad cognitiva para procesar prompts multirrestricción.
*   **Consecuencia Actual:** Sin tokens de pensamiento, el modelo falla en tareas "zero-shot" complejas:
    1. Rompe reglas de formato estricto (inserta `|||` dentro de la agenda, desencadenando bombardeos de mensajes).
    2. Alucina fechas y pierde la coherencia temporal al mapear disponibilidades (ofrece fechas falsas o se contradice).

## 2. Blueprint de Solución (Plan de Acción)
El objetivo es **reactivar la racionalidad del agente (Thinking Tokens)** sin que el SDK o el bucle de herramientas colapse por respuestas vacías.

### Alternativa A: Manejo Robusto del Objeto de Respuesta (Prioridad Alta)
Reactivaremos el pensamiento (`thinking_config=None` o budget por defecto) y blindaremos el parser en `gemini_client.py`.
1.  **Extracción Directa:** En lugar de depender de iterar sobre `response.candidates[0].content.parts`, usaremos `response.function_calls` que el SDK proporciona a nivel global, aislando la lógica de las herramientas de los bloques de pensamiento.
2.  **Manejo de "Thought-Only" Responses:** Si el modelo genera *solo* un pensamiento sin función ni texto (lo cual puede pasar si alcanza el límite de tokens de pensamiento o si se confunde con la restricción JSON):
    *   Implementaremos un sistema de reintentos interno (Retry Logic). Si `response.text` está vacío y `function_calls` está vacío, pero hay un `thought`, no dispararemos `SILENT_FALLBACK` de inmediato, sino que inyectaremos un aviso al modelo: "Continúa y emite tu llamada a función o texto en formato JSON".
3.  **Alineación del Prompt:** Modificaremos la directriz de `[AUDIO_ENVIADO]` o `[COBRO_ENVIADO]`. En ocasiones, obligar al modelo a emitir un JSON *inmediatamente* después de usar una herramienta choca con su proceso de pensamiento. Evaluaremos si el modelo puede simplemente responder "OK" o ejecutar la herramienta de forma asíncrona real.

### Alternativa B: Migración Controlada a Gemini 2.0 Pro (Si la Alternativa A falla)
Si `gemini-2.5-flash` demuestra ser inestable al combinar JSON Output + Tool Calling + Thinking (un problema recurrente en la serie Flash), la alternativa arquitectónica es migrar el orquestador a `gemini-2.0-pro-exp` o `gemini-2.0-pro`. 
*   **Ventaja:** Los modelos Pro tienen capacidades de razonamiento superiores sin depender tan rígidamente de grandes bloques de *thinking tokens* externos que rompan el SDK.

### Alternativa C: Separación de Concerns (Arquitectura de Dos Agentes)
Si el modelo monolítico sigue chocando:
1.  **Agente Router/ToolCaller:** Un modelo rápido con *thinking=0* cuya ÚNICA tarea es leer el mensaje y decidir qué herramienta ejecutar (o pasar al agente de respuesta).
2.  **Agente Conversacional:** Un modelo con *thinking activado* que no tiene herramientas conectadas, dedicado únicamente a mantener el rol de "Escultor", seguir las reglas de formato, calcular fechas y generar el JSON final.

## 3. Pruebas de Estrés y Verificación (Test Plan)
Antes de declarar el problema resuelto de raíz, se ejecutarán las siguientes pruebas sin intervención de código manual por parte del usuario:

1.  **Test de Fragmentación (Anti-Bombardeo):**
    *   Simular el pago de un usuario (`estado_pago='paid'`).
    *   Solicitar horarios.
    *   *Criterio de éxito:* El modelo debe devolver una lista de al menos 4 opciones en un único mensaje de WhatsApp sin cortes abruptos.
2.  **Test de Coherencia Temporal (Anti-Alucinación):**
    *   El usuario pide "agenda para el día que me ofreciste".
    *   *Criterio de éxito:* El agente debe confirmar la fecha contra la disponibilidad inyectada sin rechazar su propia oferta previa.
3.  **Test de Tool Calling Multiturno:**
    *   Simular intención de compra ("quiero empezar ya").
    *   *Criterio de éxito:* El agente activa `generate_payment_link` y responde el token `[COBRO_ENVIADO]` (o similar) sin disparar `SILENT_FALLBACK`.
4.  **Test de Recuperación de Estado:**
    *   Enviar "hola" tras limpiar la tabla `orus_messages` pero no `orus_users` (simulando un reset parcial).
    *   *Criterio de éxito:* El modelo debe inferir su estado actual basándose estrictamente en los campos `payment_status`, ignorando ambigüedades.

## 4. Próximos Pasos de Ejecución
1. Actualizar `gemini_client.py` implementando la **Alternativa A**.
2. Ejecutar la suite de Pruebas de Estrés local/remota.
3. Analizar los logs crudos (`docker logs`) de las interacciones para verificar que la firma de pensamiento (`thoughtSignature`) se genera y que las herramientas se extraen sin anular el `response.text`.
