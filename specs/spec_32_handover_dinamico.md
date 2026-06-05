# Spec 32: Handover Dinámico y Amnesia Controlada (Dashboard & Backend)

**Estado:** Completado
**Fecha de Implementación:** Junio 2026

## 1. Problema Abordado (Contextual Amnesia)
En transiciones humano-IA (`HUMAN` -> `AI`), el bot reanudaba su ejecución leyendo los últimos mensajes de la base de datos de manera agnóstica. Si en el historial reciente existían imágenes, notas de voz o instrucciones sin procesar que ya habían sido gestionadas por el administrador humano, el bot "alucinaba" e intentaba responder a esos estímulos viejos, ignorando la intervención humana.

Además, el bot tenía instrucciones de interpretar imágenes y leer manos, lo cual se desviaba de su propósito como "Asistente de Agendamiento".

## 2. Solución Técnica Implementada

### A. Modificación del System Prompt (Gemini)
Se ajustaron las directivas en `api/services/gemini_client.py`:
- **Imágenes:** Se prohíbe explícitamente al bot interpretar o diagnosticar manos u otras imágenes. El bot asume un rol de recepcionista de imágenes para el expediente clínico.
- **Audio:** Se asegura de que el bot procese los audios con el fin de reconducir la conversación al embudo de ventas, sin pedir que se transcriba la información (ya que usa su capacidad multimodal nativa).

### B. Inyección de Contexto Invisible (`[SYSTEM_NOTE]`)
Se implementó un mecanismo de "handback contextual" en el endpoint `POST /api/users/{user_id}/resolve` (`api/routes/dashboard.py`):
1. El administrador ahora puede proporcionar un texto de contexto opcional al finalizar la intervención.
2. Si se proporciona, el backend inserta un mensaje en `orus_messages` con el rol `assistant` y el prefijo `[SYSTEM_NOTE]`.

### C. Amnesia Controlada en la Máquina de Estados
En `api/services/message_processor.py`, se modificó la recolección del historial (`limit(8)`).
- Al leer de forma descendente (del más reciente al más antiguo), si el iterador detecta una etiqueta `[SYSTEM_NOTE]`, inserta una instrucción interna para el LLM: `[Instrucción Interna del Administrador]: {nota}. Retoma la conversación a partir de aquí.`
- Inmediatamente **corta** la recolección. El LLM ya no ve ningún estímulo, imagen o audio previo a esa instrucción de retorno.

### D. Intervención Unilateral (Takeover)
Se creó un nuevo endpoint `POST /api/users/{user_id}/takeover` en `api/routes/dashboard.py` para forzar un cambio de `session_mode` a `HUMAN` sin requerir una alerta previa.

### E. Actualización Frontend del Dashboard (EasyPanel)
En `dashboard-orus/src/pages/InboxChatView.jsx`:
- Se implementó el botón `👨‍💻 Tomar Control` visible cuando el estado es `AI`.
- Se rediseñó el flujo de retorno: al hacer clic en `Devolver al Bot`, aparece un menú desplegable (popover dropdown) donde el administrador puede redactar el contexto invisible y confirmar la devolución.

## 3. Despliegue
- Dashboard UI: Alojado en VPS (EasyPanel).
- Backend: Alojado en VPS (EasyPanel).
- Biométrica Web App: Vercel.
- Los cambios se fusionaron en producción.
