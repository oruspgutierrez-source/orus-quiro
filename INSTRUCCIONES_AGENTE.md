# Instrucciones de Sesión para Agentes

**ESTE ARCHIVO DEBE SER LEÍDO POR CUALQUIER AGENTE AL INICIAR UNA SESIÓN.**

## 0. Protocolo de Comunicación (LECTURA OBLIGATORIA ANTES DE RESPONDER)
> [!IMPORTANT]
> **Skill Activo:** [`ultra-concise-chat`](file:///C:/Users/Pichau/.gemini/config/skills/ultra-concise-chat/SKILL.md)
> Antes de generar CUALQUIER respuesta en el chat, lee y aplica este protocolo estrictamente:
> - Si la información ya fue guardada en un artefacto o `.md` → **NO la repitas en el chat.**
> - Task completada → solo escribe: *"Task #X completada con éxito."*
> - Error encontrado → solo escribe: *"Error registrado con su corrección en [archivo]."*
> - **Cero texto de relleno. Cero explicaciones de proceso. Solo el resultado.**

---

## 📌 CONTEXTO ACTUAL Y PLAN MAESTRO (Ahorro Crítico de Créditos)
> [!IMPORTANT]
> **Último Estado (2026-05-22):** Los **Specs 14, 15 y 16** han sido completados y validados con éxito absoluto. El pipeline backend, Uvicorn, ngrok y el webhook de Evolution API están **100% operativos**.
>
> **Misión Activa Actual (Spec 17 - Flujo de Agendamiento Proactivo Post-Pago y Blindaje):**
> Estamos trabajando de forma prioritaria en el **Spec 17 (Flujo de Agendamiento Proactivo Post-Pago y Blindaje del Formateador)**.
> 
> **Pasos Obligatorios si la Sesión se Reinicia:**
> 1. **Verificar Infraestructura:** Asegurar que Uvicorn (`port 8000`) y ngrok estén corriendo (tareas activas). Ejecutar `python register_webhook.py` si es necesario.
> 2. **Retomar Spec 17:** Leer el archivo [spec_17_agendamiento_proactivo_postpago.md](file:///c:/Users/Pichau/Documents/proyectos%20antigravity/proyecto%20orus-quiro/specs/spec_17_agendamiento_proactivo_postpago.md) y revisar el estado del avance en `task.md` y `bitacoras/BITACORA_SESION.md`.
> 3. **Continuar Ejecución:** Retomar las tareas pendientes del Spec 17 de forma atómica y secuencial sin reescribir de cero.



---

1. Al iniciar la interacción, dirígete INMEDIATAMENTE a la carpeta `bitacoras/` y lee el archivo `bitacoras/BITACORA_SESION.md`.
2. **ACCIÓN OBLIGATORIA — Arranque de Servidores (División de Responsabilidades):**

   > [!IMPORTANT]
   > **ngrok debe ser abierto por el AGENTE** en una ventana de PowerShell persistente utilizando `Start-Process`. El usuario ya no opera la terminal.

   ### Secuencia de arranque (en este orden exacto):

   **Paso 1 — El AGENTE levanta Uvicorn** (lo hace autónomamente vía `Start-Process`):
   ```
   Start-Process powershell -ArgumentList '-NoExit', '-Command', '$env:PYTHONUTF8=1; cd "c:\Users\Pichau\Documents\proyectos antigravity\proyecto orus-quiro"; uvicorn main:app --host 0.0.0.0 --port 8000 --reload' -WindowStyle Normal
   ```

   **Paso 2 — El AGENTE abre ngrok** vía `Start-Process`:
   ```
   Start-Process powershell -ArgumentList '-NoExit', '-Command', 'ngrok http 8000 --url=annually-murmuring-reuse.ngrok-free.dev' -WindowStyle Normal
   ```
   ⚠️ El agente debe ejecutar ambos procesos por su cuenta.

   **Paso 3 — El AGENTE registra el webhook** (después de ejecutar los comandos anteriores):
   ```python
   python -c "
   import requests, json, os, urllib3
   urllib3.disable_warnings()
   from dotenv import load_dotenv
   load_dotenv()
   base_url = os.getenv('EVOLUTION_API_URL')
   instance_name = os.getenv('EVOLUTION_INSTANCE_NAME')
   api_key = os.getenv('EVOLUTION_API_KEY')
   payload = {'webhook': {'enabled': True, 'url': 'https://annually-murmuring-reuse.ngrok-free.dev/webhook', 'byEvents': False, 'base64': False, 'events': ['MESSAGES_UPSERT']}}
   headers = {'apikey': api_key, 'Content-Type': 'application/json', 'Host': 'whatsapp.orusquiroterapia.online'}
   res = requests.post(f'{base_url}/webhook/set/{instance_name}', headers=headers, json=payload, timeout=10, verify=False)
   print(res.status_code, json.dumps(res.json(), indent=2))
   "
   ```
   Resultado esperado: `201` con `url: https://annually-murmuring-reuse.ngrok-free.dev/webhook`.

3. NO comiences a codificar ni a proponer soluciones antes de haber verificado o encendido estos servidores y haberte puesto en contexto con la bitácora.
4. **ECONOMÍA DE TOKENS (CRÍTICO):** Debes leer y aplicar de forma estricta el [Protocolo de Economía de Tokens y Control de Bucles](file:///c:/Users/Pichau/Documents/proyectos%20antigravity/proyecto%20orus-quiro/references/protocols/token_economy_flow.md). Tu prioridad es conservar créditos y evitar bucles redundantes.

## 2. Registro y Trazabilidad (Obligatorio)
A lo largo del proyecto, es **fundamental** mantener el rastro de por qué se toman decisiones y el avance atómico de cada tarea:
- **`bitacoras/BITACORA_SESION.md`**: Actualiza este archivo al terminar la sesión con los Specs completados y el estado del servidor.
- **`bitacoras/backend_logs.md`**: Registra aquí **TODAS** las decisiones técnicas relacionadas al backend (ej. FastAPI, bases de datos, webhooks) al concluir cada Task. Si cambiaste una línea porque fallaba un tipo de dato, anótalo aquí. Incluye qué error solucionamos y cómo.
- **`bitacoras/agents_logs.md`**: Registra aquí **TODO** lo relacionado a la inteligencia de los agentes (ej. Gemini, system prompts, pipelines multimodales, herramientas) al concluir cada Task. Detalla las fallas de alucinación, problemas de contexto y cómo se estructuraron las soluciones.

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
2. **Fase de Ejecución y Trazabilidad (Atómica y Acotada)**: Se ejecuta **un Task a la vez**. Si el Task se resuelve de forma simple, avanza al siguiente. Si entra en bucle (falla 3 veces consecutivas), detente, reporta al usuario en el chat y espera su consentimiento explícito para proceder. Registra cada avance en las bitácoras correspondientes (`backend_log.md` o `agents_log.md`).
3. **Fase de Integración y Sincronización**: Al finalizar todos los Tasks de un Spec en local, se actualiza `BITACORA_SESION.md`, se hace un `git commit` englobando el Spec y un `git push` a la VPS/nube.

