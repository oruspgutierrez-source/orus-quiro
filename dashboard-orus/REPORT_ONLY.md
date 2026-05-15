# SKILL: REPORT_ONLY
**Versión:** 1.0
**Objetivo:** Diagnóstico puro sin alteración de archivos.

## Contexto de Activación
- Cuando el Director solicita una "auditoría", "revisión" o "análisis de discrepancias".
- Cuando se requiere validar la integridad de los datos antes de una migración.

## Protocolo de Acción
1. **ANÁLISIS PASIVO:** El agente solo leerá archivos (`READ_ONLY`).
2. **PROHIBICIÓN DE ESCRITURA:** No se permite usar comandos como `fs.writeFileSync` o similares.
3. **ENTREGA DE RESULTADOS:** - Tabla de discrepancias encontrada.
   - Origen del error (Root Cause Analysis).
   - Sugerencia de cambio (solo en texto, no ejecutable).

## Salida Obligatoria
"Diagnóstico completado bajo protocolo REPORT_ONLY. No se han realizado cambios en el sistema."