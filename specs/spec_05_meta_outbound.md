# Spec 05: Meta Outbound & Humanized Delivery (Blindado)

## Objetivo
Implementar el servicio simulado de envío hacia Meta, incorporando un sistema de 'Fraccionamiento Humano' blindado con Expresiones Regulares para mitigar alucinaciones de la IA y asegurar entregas fluidas.

## Componentes Requeridos
1.  **System Prompt (Gemini):** Inyectar reglas estrictas en `gemini_client.py` para forzar a la IA a usar el delimitador semántico `|||`.
2.  **Servicio de Envío (api/services/meta_client.py):**
    * Función `send_humanized_response(recipient_id, full_text)`.
    * **Lógica Blindada:** Uso de `re.split(r'\|{2,}', text)` para particionar, con un *fallback* a saltos de línea `\n{2,}` si la IA olvida el delimitador.
    * **Filtro:** Ignorar fragmentos con una longitud `<= 1`.
    * **Simulación Asíncrona:** Bucle `for` iterando sobre los fragmentos limpios y simulando el envío con un `await asyncio.sleep(random.uniform(3, 5))`.
3.  **Conexión Final:** Modificar `api/services/orchestrator.py` para invocar este módulo en lugar del `print` básico.

## Criterios de Aceptación
* El servidor procesa una entrada y solicita a Gemini el formato delimitado.
* El texto en crudo de Gemini es parseado por Regex y convertido en una lista validada.
* La consola muestra cada mensaje enviándose de forma seriada y pausada.
