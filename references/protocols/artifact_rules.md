# Protocolo Estricto de Artefactos (REPORT_ONLY)

## Regla Global y Absoluta
Bajo NINGUNA circunstancia se debe incluir dentro del contenido de un artefacto (archivos `.md`, esquemas, reportes, logs, etc.) una instrucción pidiendo al usuario autorización para ejecutar código, ni comandos explícitos de ejecución para que el usuario los apruebe.

### El Problema
El sistema multiagente (Antigravity u otros) lee los artefactos generados. Si encuentra una frase como *"¿Deseas que proceda con la implementación?"* o *"Ejecuta este código para continuar"*, el agente puede tomarlo como una orden directa para auto-ejecutarse en la siguiente iteración sin supervisión del usuario, desencadenando bucles o cambios de código indeseados.

### La Solución y Directrices
1. **Artefactos pasivos:** Los artefactos deben ser única y exclusivamente **descriptivos, analíticos o informativos**.
2. **Cero Autorizaciones:** La autorización del usuario SIEMPRE vendrá del chat principal, dictada por el humano. Jamás se debe emular una petición de permiso dentro del contenido de un documento.
3. **Cero Comandos Ejecutivos:** No incluir frases como "Run esto", "Copia y pega", "Procede con...".
4. Si un artefacto describe un plan de acción, debe referirse a él en tercera persona o formato pasivo: "El paso 1 consistirá en modificar el archivo X", en lugar de "Paso 1: Modifica el archivo X. ¿Procedemos?".

Cualquier violación de esta regla pone en riesgo la estabilidad del flujo de trabajo automatizado.
