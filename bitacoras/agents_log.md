# Bitácora de Agentes (LLM & Prompts)

Este documento centraliza el histórico de ajustes en la Inteligencia Artificial: Prompts del sistema, configuración del modelo Gemini 2.5 Flash, mapeo de contexto y mitigación de alucinaciones o pérdida de información.

## Propósito
Tener un registro claro de **por qué** un prompt está estructurado de cierta manera, **cómo** se resolvieron confusiones del LLM (alucinaciones) y **qué** reglas de negocio se implementaron en el sistema experto (Orus Quiromancia, Análisis Biométrico).

---

## [2026-05-14] Mitigación de Alucinación en Contexto Multimodal (Spec 11)

### Contexto y Problema
- Al probar enviar ráfagas compuestas por: **[Imagen con texto] + [Nota de voz] + [Texto suelto]**, el modelo Gemini asimilaba el "Texto suelto" como si fuera la transcripción literal de la "Nota de voz".
- Esto pasaba porque se enviaba el binario y luego el texto secuencial en el prompt de historial, lo cual llevaba a la IA a inferir que el texto describía el binario anterior.

### Solución Implementada
- **Mapeo Explícito y Segregación:** Se modificó la construcción de la lista `contents` en `gemini_client.py` y `message_processor.py` para aislar drásticamente cada elemento:
  1. Se envuelven los bytes del archivo en marcadores rígidos: `[--- INICIO DEL ARCHIVO ADJUNTO X ---]` y `[--- FIN DEL ARCHIVO ADJUNTO X ---]`.
  2. Si es audio, se inyecta la instrucción dura: `[Adjunto X: NOTA DE VOZ. ATENCIÓN ORUS: DEBES procesar el audio adjunto X. El texto a continuación NO es el audio]`.
  3. Los mensajes de texto independientes se envuelven en: `[Mensaje de texto independiente]: {texto}`.

### Resultado
- Pruebas posteriores confirmaron que Gemini logró aislar la escucha del audio (detectando la palabra secreta correcta) sin confundirse con el texto que venía en el mismo bloque. Esta segregación debe mantenerse para cualquier nuevo tipo de archivo.
