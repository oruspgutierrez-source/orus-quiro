# Protocolo de Economía de Tokens y Control de Bucles (Token Economy & Loop Control)

## Objetivo
Prevenir el agotamiento prematuro de créditos de modelos y tokens diarios debido a ejecuciones en bucles sin supervisión humana, asegurando al mismo tiempo la continuidad absoluta y la trazabilidad del desarrollo del proyecto `Orus-Quiro` a través de múltiples sesiones y agentes independientes.

---

## 1. Principio de Ejecución Atómica (Un Task a la vez)
1. **Sin Cascadas Autónomas:** Queda estrictamente prohibida la ejecución en cadena de múltiples tareas complejas de un Spec en un solo turno.
2. **Tareas Simples:** Si una tarea es sumamente trivial (corrección ortográfica, cambio de un parámetro de configuración simple, renombrado menor), el agente puede completarla y avanzar de forma continua a la siguiente.
3. **Tareas Complejas:** Para cualquier tarea que implique lógica de negocio, integración de APIs o refactorización:
   - Se debe ejecutar de forma aislada.
   - Se debe verificar su funcionamiento local.
   - Se debe documentar el progreso de inmediato en las bitácoras (`backend_log.md` o `agents_log.md`).
   - Se debe detener la ejecución y notificar al usuario en el chat para obtener retroalimentación, a menos que el usuario haya aprobado previamente la ejecución secuencial explícita en ese turno.

---

## 2. Política Antibucle (Loop Breaker)
Los bucles automáticos de corrección de código son el principal factor de consumo absurdo de tokens. Para evitar esto:
1. **Regla de 3 Intentos:**
   - **Intento 1:** Implementación inicial de la solución de la Task.
   - **Intento 2 (Si falla el 1):** Corrección aplicando un enfoque alternativo o ajustando la lógica defectuosa.
   - **Intento 3 (Si falla el 2):** Último ajuste guiado por trazas específicas de error.
2. **Detención Obligatoria:** Si tras el **tercer intento** la tarea sigue fallando (errores de compilación, fallos de tests o comportamientos inesperados), el agente **DEBE DETENERSE INMEDIATAMENTE**.
3. **Acción Conversacional:** El agente notificará al usuario en el chat:
   > *"La Task [ID de Task] ha fallado por 3ª vez consecutiva. De acuerdo con el Protocolo de Economía de Tokens, detengo la ejecución automática para evitar un consumo excesivo de créditos. Esta tarea requiere una **Iteración Profunda** de diseño. Presento el análisis del error y espero tus indicaciones para rediseñar el camino o pausar la sesión."*
4. Queda prohibido realizar un cuarto intento de manera autónoma sin la autorización expresa del usuario en la conversación del chat.

---

## 3. Registro Progresivo de Avance
Para garantizar que cualquier agente nuevo pueda continuar el trabajo sin perder contexto:
1. **Documentación Post-Task:** Al concluir cada tarea de un Spec (tanto con éxito como si se detiene por la política antibucle), el agente debe actualizar inmediatamente los logs correspondientes en:
   - `bitacoras/backend_log.md` (si el cambio es del sistema base/APIs).
   - `bitacoras/agents_log.md` (si es relativo al LLM, prompts o integraciones de IA).
2. **Estructura del Registro:** Cada entrada en el log debe incluir:
   - ID de la Task y título.
   - Estado final (`COMPLETO`, `PAUSADO por Bucle`, `PENDIENTE`).
   - Problemas técnicos encontrados y cómo se resolvieron o por qué bloquearon la tarea.
   - Decisiones críticas de arquitectura o dependencias introducidas.

---

## 4. Control de Créditos y Fin de Sesión
El sistema de créditos se recarga cada 5 horas (o límites diarios).
1. **Pausas Estratégicas:** Si se detecta un consumo elevado o se aproxima el límite de créditos, o el usuario lo solicita explícitamente:
   - Detener toda llamada a herramientas.
   - Actualizar el archivo `bitacoras/BITACORA_SESION.md` reflejando el progreso del Spec actual y el estado general.
   - Guardar una lista clara de próximos pasos detallados y accionables en la sección "Siguiente Misión" para que el próximo agente los retome directamente.
   - Despedirse confirmando que la sesión ha sido congelada con éxito.
