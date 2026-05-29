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

---

## [2026-05-21] Refactorización Prompt del Sistema y Referencia Dinámica JID (Spec 14)

### Contexto y Desafío Técnico
- **Invocación de la nota de voz (`send_introductory_audio`):** La herramienta requiere un parámetro `to_number` que corresponde al JID de WhatsApp real del destinatario.
- **Desafío:** En el pipeline conversacional normal, Gemini no tiene acceso dinámico a los metadatos del webhook (el JID del remitente). Pedirle al usuario su número antes de mandarle el audio rompe el principio de automatización fluida (acogida instantánea).

### Solución Diseñada e Implementada
1. **Inyección en el Pipeline (`message_processor.py`):**
   Al procesar el buffer, se inyecta de forma dura y transparente al principio del prompt del usuario una etiqueta de metadatos del remitente:
   `[Metadatos del Remitente: JID={real_sender_id}]`
   Esto proporciona un ancla in-context permanente para que el LLM lea el JID exacto y lo inyecte directamente como argumento sin alucinar ni requerir que el usuario lo escriba de forma textual en el chat.

2. **Ingeniería de Prompts en `system_rules`:**
   Se incorporó el bloque estructural `PROTOCOLO DE ACOGIDA Y FLUJO DE AUDIOS EXPLICATIVOS (CRITICO - SPEC 14)` instruyendo al modelo a:
   - Mantener una formalidad absoluta (cero emojis) y responder dudas iniciales con tono sobrio.
   - Forzar en el primer o segundo mensaje la pregunta de enganche exacta: *"¿Te gustaría saber a profundidad cómo funciona el proceso completo de la lectura y el impacto de esta guía védica?"*.
   - Ejecutar la herramienta `send_introductory_audio(to_number)` tan pronto como el usuario asienta o demuestre interés en el proceso.
   - Garantizar una respuesta de confirmación idéntica y estandarizada tras la invocación del envío de audio: *"Te comparto este audio donde te explico detalladamente la metodología. Estaré atento a cualquier inquietud que te surja antes de continuar."*

### Resultado Esperado
- El bot cuenta con referencias exactas y lógicas estrictas para despachar el audio nativo simulado sin fricciones, sin emojis y sin alucinaciones de JID.

---

## [2026-05-21] Refinamiento del Flujo de Agendamiento Visual (Spec 13) y Prohibición de Emojis

### Contexto y Problema
- **Agendamiento Proactivo:** El agendamiento debe activarse inmediatamente después del pago sin esperar a que el usuario lo solicite.
- **Flujo Visual Secuencial:** El bot debe explicar al consultante de forma limpia y formal que recibirá un instructivo en 3 pasos por separado con imágenes en lugar de un enlace crudo sin explicación, garantizando una sintonía cognitiva perfecta.
- **Ausencia de Emojis:** Es de vital importancia mantener una comunicación de alta gama, formal, y libre de cualquier emoji.

### Solución Implementada
- **Modificación en `system_rules`:**
  - Se reordenó la sección `ORDEN DE ACTIVACIÓN Y PRIORIDAD CONVERSACIONAL` para que Gemini priorice de forma inquebrantable el flujo de agendamiento post-pago, ofreciendo inmediatamente consultar horarios libres llamando a `check_free_slots`.
  - Se detalló el paso `4. PROCESAMIENTO DE RESPUESTA Y GUÍAS DE WhatsApp` para que, cuando el usuario confirme los datos de la cita, Gemini explique que se ha iniciado el envío automático del instructivo secuencial en 3 pasos con imágenes de soporte, y al final, el enlace directo del calendario.
  - Se añadió una regla estricta prohibiendo explícitamente cualquier emoji en todas las respuestas de Gemini para mantener un tono formal de alta gama.

### Resultado
- El flujo conversacional de Orus está 100% alineado con las guías visuales de WhatsApp enviadas secuencialmente desde `calendar_client.py`, y mantiene un estilo de comunicación impecable y pulido.

### Corrección Adicional [2026-05-21 — Emergencia]
- **Bug de Compilación en Caliente:** Al cargar el prompt cognitivo `system_rules` como f-string, Python intentaba evaluar `{link_generado}` en el ámbito local. Al no estar definido, se producía un error `NameError: name 'link_generado' is not defined`, bloqueando el pipeline al recibir un mensaje del usuario.
- **Resolución:** Se escapó la cadena como `{{link_generado}}` en el prompt del sistema. Se comprobó la recarga en caliente del reloader de Uvicorn exitosamente.

---

## [2026-05-22] Cambio de Arquetipo Cognitivo: "El Escultor" / Auditoría Biosemiótica

### Contexto y Decisión Estratégica
- Tras evaluar los outputs cognitivos, se determinó realizar un cambio radical de posicionamiento comercial y de marca.
- Se abandonó por completo el arquetipo místico, quiromántico y védico, y se adoptó la identidad sobria, directa y clínica de **"El Escultor"**.
- El servicio interactivo de lectura y diagnóstico ahora se denomina formalmente **Auditoría Biosemiótica**.

### Solución e Ingeniería de Prompts
- **Reescritura de `system_rules` (`gemini_client.py`):**
  - Se eliminó el uso de terminología esotérica como "mágico", "destino", "karma" y expresiones de acogida tipo "namasté".
  - Se redefinió la voz de Orus como la de un analista clínico de altísima gama, preciso, perspicaz y directo.
  - Se inyectó una estructura dura en 3 fases para presentar el servicio al consultante: **La Calibración** (análisis biométrico inicial), **La Revelación** (auditoría en tiempo real) y **El Protocolo** (guía escrita y material de corrección).
  - Se inyectó la pregunta activadora y el guion exacto de redirección para justificar el envío del audio explicativo de 3 minutos.
  - Se actualizó el prompt de agendamiento para referir a las fotos de las manos como "material de trabajo" y "hardware biológico", requiriendo iluminación perfecta.

### Resultado
- El tono del bot en la conversación de WhatsApp es sumamente elegante, profesional y sobrio, alineándose de forma consistente con un servicio premium.

---

## [2026-05-22] Integración de Advertencia de Spec 16 en System Prompt
- Se incorporaron reglas explícitas al `system_rules` para que Orus, al procesar el final del agendamiento exitoso, prepare cognitivamente al consultante advirtiéndole que recibirá de inmediato las guías ilustradas de calendario y el enlace seguro del formulario de recolección de datos biométricos.
- Esto mantiene una transición conceptual limpia hacia la Web App, reduciendo la deserción al solicitar las fotos de manos.

---

## [2026-05-22] Ajuste Técnico del SDK GenAI (Desactivación de Automatic Function Calling)

### Contexto y Problema
- Durante las pruebas interactiva reales, al aceptar la pregunta activadora de audio, el bot no enviaba la nota de voz y respondía de forma errónea con texto sobre la conversión JSON.
- **Causa Raíz:** El SDK oficial de Google GenAI (`google-genai` en Python) tiene activa la ejecución automática de funciones (`automatic_function_calling=True`) de forma nativa. Sin embargo, su bucle interno síncrono no soporta corrutinas asíncronas (`async def`) como herramientas, lo que producía un error silencioso de validación, devolviendo objetos nulos a la Fase 2 (formateador en dos pasos).

### Solución Implementada
- Se configuró explícitamente `automatic_function_calling=False` dentro de `GenerateContentConfig` al invocar a Gemini.
- Se delegó el 100% del despacho y ejecución de herramientas asíncronas a nuestro bucle asíncrono nativo en `gemini_client.py`, que es robusto y compatible con corrutinas.

### Resultado
- Las llamadas a funciones asíncronas (`send_introductory_audio` y `book_appointment`) se detectan de forma estable en la primera fase y se ejecutan secuencialmente de manera impecable y segura.

---

## [2026-05-22] - Auditoría y Certificación Cognitiva del Spec 17: Agendamiento Proactivo y Blindaje

### Contexto de Negocio
- Se requería que tras la confirmación de pago de Stripe, el bot presentara de forma inmediata el menú de agendamiento clínico sin rastro de agradecimientos redundantes de por medio, puesto que la factura PDF ya hace la transición conceptual.
- Para mitigar la latencia y fallas cognitivas en el llamado autónomo a herramientas, la disponibilidad del calendario debía calcularse directamente en el servidor y ser inyectada en el prompt del LLM.

### Ajustes Cognitivos y Soluciones de Ingeniería
1. **Inyección Dinámica de Disponibilidad Comercial**:
   - En el endpoint `/payments/webhook`, tras la facturación exitosa, se calcula la agenda disponible para los próximos 5 días hábiles.
   - Esta disponibilidad se inyecta directamente al prompt de trigger asíncrono (`trigger_prompt`).
   - Se inyectaron directivas estrictas en el prompt prohibiendo saludos o agradecimientos redundantes por el pago ("gracias por tu pago", "ya recibí tu dinero") y ordenando al LLM proponer directamente las opciones horarias en el formato de "El Escultor".

2. **Mitigación Antierosiva del Formateador (Fase 2 de Gemini)**:
   - Se diseñó y validó un bloque de intercepción preventiva en `generate_response()` (Fase 2).
   - Si la primera fase (inferncia cognitiva) devuelve un string vacío o nulo debido a una anomalía del LLM o fallo de red, el sistema intercepta la ejecución antes de lanzar la segunda llamada de formateo e inyecta un JSON clínico de fallback con el reporte de disponibilidad estructurada de respaldo.

### Resultado y Verificación
- **Validación de Inferencia**: En las simulaciones de pago en caliente con Stripe, Gemini 2.5 Flash asimiló la disponibilidad inyectada y formateó directamente la respuesta JSON en la primera fase.
- **Tono Exclusivo**: El bot envió a WhatsApp el menú de horarios de agendamiento de forma directa, sobria y secuencial, garantizando un tránsito silencioso y premium inmediatamente posterior al despacho del PDF de factura.

---

## [2026-05-22] - Corrección de Alucinaciones Conversacionales y Robustecimiento de Fallback (Spec 17)

### Contexto del Fallo
- Durante las pruebas interactiva reales, el bot sufrió dos fallas cognitivas severas:
  1. **Alucinación de Plantilla de Fase 2**: El formateador devolvía textualmente la frase explicativa de los placeholders genéricos del prompt en lugar del texto real.
  2. **Falsos Positivos de Pago**: El fallback preventivo de respuesta vacía asumía erróneamente que todas las caídas eran del agendamiento de Stripe, confirmando pagos falsos a usuarios que hacían consultas normales.

### Soluciones de Ingeniería Aplicadas
1. **Refactorización de `FORMAT_INSTRUCTION`**:
   - Se removieron por completo todos los placeholders genéricos con delimitadores `<...>` y se reemplazaron por descripciones en lenguaje natural explícitas de instrucción rígida de formateo.
   - Se inyectó una advertencia in-context prohibiendo reescribir o usar las frases de ejemplo, forzando la inyección del contenido real de la Fase 1.
2. **Robustecimiento Contextual del Blindaje**:
   - Se modificó la intercepción en `gemini_client.py` para verificar contextualmente la presencia de la cadena `"INFORME DE DISPONIBILIDAD OBTENIDO DIRECTAMENTE DEL SERVIDOR:"` en el prompt.
   - Si no está presente (chat ordinario), el blindaje despacha un fallback conversacional pulido e impersonal en el tono de "El Escultor" que previene falsos positivos de Stripe.

### Resultado de la Verificación
- **Flujo Ordinario**: Consultas de precio y saludos se parsearon exitosamente como JSON a la primera, sin alucinaciones de plantillas.
- **Intención de Compra**: Gemini detectó y llamó con total precisión a la herramienta `generate_payment_link`, obteniendo la sesión de Stripe local. La Fase 2 formateó de forma perfecta la respuesta con el enlace de pago inyectado, sin activar falsos positivos de confirmación de cobro. El bot se encuentra 100% estabilizado.

### Task 19.1 & 19.3
- **Cambio:** Redise�o de system_rules con Checklist de Estado Conversacional (M�quina de Estados) y FAQ.
- **Motivo:** Evitar alucinaciones en el flujo, asegurar avance secuencial y manejar desv�os (Preguntas sobre precio y quiromancia).
