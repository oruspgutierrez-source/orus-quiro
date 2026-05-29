# Spec 14: Protocolo de Atención, Tono Conversacional y Flujo de Audios Explicativos

## 1. Objetivo
Rediseñar el tono y comportamiento del sistema experto de IA en el prompt de sistema (`system_rules`) y dotar a la infraestructura de la capacidad para reproducir archivos multimedia pregrabados (notas de voz y audios de alta duración), guiando al consultante a través del flujo introductorio de quiromancia antes del proceso de venta.

---

## 2. Diseño Técnico y Arquitectura de Medios

### A. Almacenamiento de Recursos Fijos (Media Assets)
Se estructurará una jerarquía de almacenamiento estático local dentro de la VPS para alojar los audios explicativos del consultante y las imágenes instructivas:
- **Ruta de Audios:** `resources/media/audios/`
  - Recurso: `explicacion_proceso.mp3` / `explicacion_proceso.ogg` (Audio explicativo de 3 minutos de duración).
- **Ruta de Imágenes:** `resources/media/images/`
  - Recurso: `calendar_step1.webp` (Captura que ilustra los tres puntos del menú en el navegador móvil).
  - Recurso: `calendar_step2.webp` (Captura que ilustra la opción "Copiar en mi calendario").

### B. Envío Simulado de Nota de Voz en WhatsApp
Para que el audio pregrabado sea entregado al consultante simulando una nota de voz grabada de forma nativa en el instante (en lugar de aparecer como un archivo de música adjunto):
- Se utilizará el endpoint `/message/sendAudio/{instance_name}` de Evolution API.
- **Configuración del Payload:**
  - `number`: Número del destinatario en formato real JID.
  - `audio`: Archivo codificado en Base64 o URL pública segura del recurso estático (formato OGG-Opus recomendado).
  - `audioDelay`: Retraso simulado para emular el tiempo de "grabación" en tiempo real.

---

## 3. Comportamiento Conversacional y System Rules (IA)

Se modificará el prompt del sistema en `api/services/gemini_client.py` para cumplir con las siguientes reglas conversacionales en la fase inicial:

1. **Fase de Acogida:** Orus atiende al usuario de forma empática y sobria. Responde preguntas iniciales sobre las lecturas biométricas y el proceso quiromántico.
2. **Activador de Interés:** Al responder a la primera o segunda inquietud, Orus introducirá una pregunta obligatoria de enganche: *"¿Te gustaría saber a profundidad cómo funciona el proceso completo de la lectura y el impacto de esta guía védica?"*
3. **Disparador de Herramienta (`send_introductory_audio`):**
   - Si el consultante responde afirmativamente o demuestra interés, Gemini invocará una herramienta dedicada.
   - La herramienta enviará al chat de WhatsApp el audio pregrabado de 3 minutos y un mensaje de seguimiento: *"Te comparto este audio donde te explico detalladamente la metodología. Estaré atento a cualquier inquietud que te surja antes de continuar."*

---

## 4. Plan de Implementación (Tareas)

- **[ ] Task 1. Estructura de Directorios de Medios:** Crear el directorio `resources/media/` con sus respectivas subcarpetas para audios e imágenes en el servidor local.
- **[ ] Task 2. Adaptación del Cliente WhatsApp (`wa_client.py`):** Desarrollar la función asíncrona `send_audio_message` en la clase `WhatsAppClient` que interactúe con el endpoint `/message/sendAudio` de Evolution API con soporte para simular la grabación nativa.
- **[ ] Task 3. Declaración de la Herramienta en Gemini (`tools`):** Definir la función `send_introductory_audio` como una herramienta disponible para Gemini 2.5 Flash en `gemini_client.py`.
- **[ ] Task 4. Refactorización de las Reglas del Sistema (System Rules):** Actualizar el prompt cognitivo de Orus para forzar el protocolo de acogida, la pregunta de interés, y la invocación precisa de la herramienta de audio.
- **[ ] Task 5. Pruebas de Flujo Conversacional:** Crear un script de prueba que simule la conversación introductoria y valide el envío exitoso del audio en el chat del destinatario.
