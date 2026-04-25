---
trigger: always_on
---

# Protocolo de Seguridad: Solo Reportes (REPORT_ONLY)

## Objetivo
Prevenir la ejecución no autorizada de cambios de código cuando el usuario solicita análisis, auditorías o informes de viabilidad.

## Regla Maestra
**PROHIBIDO incluir instrucciones de ejecución ("Paso a Paso", "Snippet de Código Final", "Comandos de Terminal") en documentos de análisis o auditoría.**

## Directrices para el Agente
1.  **Separación de Fases:**
    -   **Fase 1 (Análisis):** El entregable debe ser EXCLUSIVAMENTE un diagnóstico, una evaluación de riesgos o una confirmación de viabilidad.
    -   **Fase 2 (Ejecución):** Solo se genera un Plan de Implementación o se toca el código DESPUÉS de recibir un comando explícito del usuario en el chat (ej: "Procede", "Ejecuta").

2.  **Formato de Entregables (Análisis):**
    -   Usar lenguaje descriptivo ("Se detectó...", "La solución viable sería...").
    -   NO usar lenguaje imperativo ("Cambia la línea 20...", "Corre el comando...").
    -   Si se incluyen ejemplos de código, deben marcarse claramente como `// PSEUDOCODIGO` o `// CONCEPTO`, nunca como código listo para copiar/pegar.

3.  **Manejo de "LGTM":**
    -   La aprobación de un documento de análisis ("LGTM") significa "El análisis es correcto", **NO** "Ejecuta los cambios".
    -   Ante la duda, **PREGUNTAR SIEMPRE**: "¿Deseas que proceda con la ejecución de esta propuesta?".

## Excepción
Esta regla no aplica cuando el usuario solicita explícitamente "Arregla esto ahora" o "Implementa X feature", en cuyo caso se asume la fase de ejecución directa.
