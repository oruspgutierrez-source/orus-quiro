# Instrucciones de Sesión para Agentes

**ESTE ARCHIVO DEBE SER LEÍDO POR CUALQUIER AGENTE AL INICIAR UNA SESIÓN.**

## 1. Contexto y Orientación
1. Al iniciar la interacción, dirígete INMEDIATAMENTE a la carpeta `bitacoras/` y lee el archivo `bitacoras/BITACORA_SESION.md`.
2. **ACCIÓN OBLIGATORIA:** En tu **primer mensaje** hacia el usuario, debes entregarle los comandos de PowerShell para encender los servidores (`uvicorn` y `ngrok`), los cuales se encuentran en la sección de Arranque Rápido de la bitácora.
3. NO comiences a codificar ni a proponer soluciones antes de haber entregado estos comandos y haberte puesto en contexto con la bitácora.

## 2. Registro y Trazabilidad (Obligatorio)
A lo largo del proyecto, es **fundamental** mantener el rastro de por qué se toman decisiones. No basta con hacer el código que funcione; hay que documentar la evolución:
- **`bitacoras/BITACORA_SESION.md`**: Actualiza este archivo al terminar la sesión con los Specs completados y el estado del servidor.
- **`bitacoras/backend_logs.md`**: Registra aquí **TODAS** las decisiones técnicas relacionadas al backend (ej. FastAPI, bases de datos, webhooks). Si cambiaste una línea porque fallaba un tipo de dato, anótalo aquí. Incluye qué error solucionamos y cómo.
- **`bitacoras/agents_logs.md`**: Registra aquí **TODO** lo relacionado a la inteligencia de los agentes (ej. Gemini, system prompts, pipelines multimodales, herramientas). Detalla las fallas de alucinación, problemas de contexto y cómo se estructuraron las soluciones.

## 3. Protocolo de Artefactos (REPORT_ONLY)
**REGLA DE ORO:** Está terminantemente **PROHIBIDO** incluir solicitudes de autorización para ejecutar código dentro de cualquier artefacto (`.md`, logs, etc).
- **El por qué:** El sistema multi-agente puede leer el artefacto, ver la pregunta de autorización y tomarla como una instrucción para auto-ejecutarse, causando ciclos o errores sin supervisión humana.
- **La solución:** Toda la comunicación de "permiso para continuar" o "ejecutar" debe hacerse **ÚNICA Y EXCLUSIVAMENTE a través de la ventana de chat principal**.

## 4. Reciclaje y Estructura de Código
- Antes de crear un script nuevo, revisa el directorio `scripts/` y la carpeta `api/services/` para reciclar funciones existentes (como utilidades de formato, requests a APIs, conversiones).
- Todo mapa arquitectónico gráfico debe actualizarse o crearse en la subcarpeta `references/architecture/`.

## 5. Estructura de Trabajo ("Spec -> Task -> Execute -> Log -> Commit")
Esta es la metodología oficial de avance del proyecto:
1. **Fase de Análisis y Desglose (El Spec)**: Todo objetivo se documenta en `specs/` (Ej: `spec_08...md`) y se divide en **Tasks** atómicos. No se ejecuta código; se reporta el plan al usuario esperando aprobación (Fase de Aprobación).
2. **Fase de Ejecución y Trazabilidad**: Se ejecuta **un Task a la vez**. Los errores, decisiones de diseño o problemas con prompts se mapean inmediatamente en las bitácoras (`backend_logs.md` o `agents_logs.md`) explicando el *"por qué"*.
3. **Fase de Integración y Sincronización**: Al finalizar todos los Tasks de un Spec en local, se actualiza `BITACORA_SESION.md`, se hace un `git commit` englobando el Spec y un `git push` a la VPS/nube.
