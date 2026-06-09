# Spec 39: Resiliencia Conversacional y Análisis de Estabilidad (OpenRouter vs. Gemini Directo)

Este documento analiza el error de truncamiento de respuestas observado en producción (`Unterminated string` en el JSON devuelto por OpenRouter), evalúa los riesgos y propone dos soluciones definitivas: la implementación de un mecanismo de auto-reintento con control de tokens y la migración a la API directa de Google Gemini con esquemas estructurados nativos.

---

## 1. Análisis Técnico del Error de Truncamiento

### ¿Por qué se genera el error?
El error `Unterminated string starting at: line 1 column 11` ocurre porque la respuesta del LLM a través de OpenRouter llega incompleta (cortada a la mitad), por ejemplo:
```json
{"reply": "La Auditoría Biosemiótica no es una 'lectura' en el sentido tradicional. [...] La segunda, 'La Revelación', cru
```

Esto se debe a tres factores principales:
1. **Límite de Tokens por Defecto (`max_tokens`)**: En la implementación actual en `gemini_client.py`, el payload enviado a OpenRouter **no especifica** el parámetro `max_tokens` (o `max_completion_tokens`). Muchos proveedores y endpoints en OpenRouter aplican un límite por defecto muy bajo (generalmente entre 150 y 250 tokens) si no se declara explícitamente. Cuando el modelo genera un texto detallado explicándole al usuario el servicio clínico, agota ese límite y la generación se corta abruptamente.
2. **Latencia e Interrupciones de Red en el Proxy**: OpenRouter actúa como un intermediario proxy. La petición viaja de nuestro servidor a OpenRouter, de OpenRouter a los servidores de Google, y de regreso. Si ocurre un microcorte, una caída en la conexión o el backend de Google responde lento, OpenRouter retorna el buffer acumulado hasta el momento, el cual resulta en un JSON corrupto y truncado.
3. **Complejidad del Formato JSON**: Obligar al modelo a formatear la salida como JSON consume tokens adicionales en llaves, comillas y caracteres de escape, lo que reduce el espacio disponible para el texto real y aumenta la probabilidad de truncamiento si los límites son estrictos.

### Riesgo en Producción y Experiencia de Usuario (UX)
*   **Riesgo de Bloqueo (Mitigado)**: Sin el parser robusto, el webhook del backend lanza una excepción 500 y no responde al usuario, dejando el chat "colgado". El parser robusto actúa como un "paracaídas" para evitar el colapso del bot, pero...
*   **Suboptimidad de UX (Riesgo Crítico)**: Enviar un mensaje cortado a la mitad a un cliente de alta gama rompe por completo la ilusión de un servicio premium y la voz clínica de "El Escultor". Parece un fallo técnico obvio y reduce la confianza de conversión de venta. Por ende, **el parser robusto local es un mecanismo de seguridad (safety net), pero no una solución de calidad de servicio.**

---

## 2. Comparativa: OpenRouter vs. Google Gemini Directo

El usuario plantea una pregunta clave: *¿Usar Gemini directamente desde los servidores de Google es más estable?* **La respuesta es un rotundo SÍ.**

A continuación se detalla la comparación técnica:

| Criterio | OpenRouter (Estado Actual) | Google Gemini Directo (API / SDK Oficial) |
| :--- | :--- | :--- |
| **Estabilidad y SLA** | Media. Depende del estado del proxy de OpenRouter y sus proveedores. | Alta. Conexión directa a la infraestructura global de Google. |
| **Esquemas Estructurados Nativos** | Limitado. Depende del modelo; a menudo se simula mediante prompts del sistema. | **Excelente (Nativo)**. Permite pasar un esquema Pydantic directo (`response_schema`), y el decodificador de Google garantiza que la salida sea 100% JSON válido. |
| **Latencia** | Mayor (doble salto de red). | Menor (conexión directa de latencia ultra-baja). |
| **Facturación y Límites** | Flexible. Permite saldo prepagado único y cambiar de modelos (DeepSeek, Llama) al vuelo. | Restringida. Requiere registrar tarjeta en Google Cloud / AI Studio, y aplican límites de cuota estrictos en tiers gratuitos. |

### Recomendación de Arquitectura
*   **Si la prioridad absoluta es la estabilidad y la calidad de la respuesta (UX)**: Se debe migrar a la **API Directa de Gemini** utilizando el SDK oficial (`google-genai`), forzando el formato estructurado con `response_schema`.
*   **Si se prefiere mantener OpenRouter por costes y flexibilidad de modelos**: Debemos blindar la llamada con un **Límite de Tokens Explícito** y un **Mecanismo de Auto-Reintento con Autocorrección**.

---

## 3. Propuesta de Solución 1: Auto-Reintento con Autocorrección en OpenRouter

Si decidimos mantener OpenRouter, podemos añadir una capa de resiliencia conversacional directa en `gemini_client.py`:

```mermaid
graph TD
    A[Inicio Petición LLM] --> B[Enviar a OpenRouter con max_tokens=1000]
    B --> C{¿La respuesta termina en '}'?}
    C -- Sí (JSON Completo) --> D[Procesar JSON y retornar]
    C -- No (Truncado) --> E{¿Quedan reintentos?}
    E -- Sí --> F[Agregar aviso de concisión al prompt]
    F --> G[Re-solicitar respuesta limpia e íntegra]
    G --> B
    E -- No --> H[Usar Parser robusto como último recurso]
    H --> I[Marcar requires_human=True en base de datos]
```

### Código Conceptual del Mecanismo (en `generate_response`)
1.  **Declarar `max_tokens`**: Asegurar que siempre se pida `max_tokens: 1000` para dar margen al modelo.
2.  **Detección de Truncamiento**: Verificar si la respuesta cruda no termina en `}` o si el parser robusto se activa debido a un error de sintaxis JSON.
3.  **Bucle de Reintento**:
    ```python
    retries = 1
    for attempt in range(retries + 1):
        # 1. Realizar petición HTTP a OpenRouter con max_tokens=1000
        # ...
        raw_text = content.strip()
        
        # 2. Verificar si está truncado
        is_truncated = not raw_text.endswith("}")
        
        if not is_truncated:
            try:
                parsed_json = json.loads(raw_text)
                return parsed_json
            except json.JSONDecodeError:
                is_truncated = True # Si falla el parseo, lo tratamos como truncado
        
        if is_truncated and attempt < retries:
            print(f"[OpenRouter] Respuesta truncada detectada. Reintentando con instrucción de concisión...", flush=True)
            # Modificamos temporalmente el prompt para exigir concisión y evitar el corte
            prompt += "\n\n[SISTEMA - ALERTA]: Tu respuesta anterior fue cortada por el límite de caracteres. Por favor, genera la respuesta de nuevo de forma mucho más concisa para asegurarte de que quepa completa y con formato JSON válido."
            continue
        else:
            # Si se agotaron los reintentos, usamos el parser robusto para salvar el webhook
            parsed_json = run_robust_parser(raw_text)
            # Adicionalmente, alertamos al dashboard humano ya que el mensaje es subóptimo
            parsed_json["requires_human"] = True
            return parsed_json
    ```

---

## 4. Propuesta de Solución 2: Migración a Gemini Directo con Esquema Estructurado

Esta solución elimina OpenRouter y vuelve a la API oficial de Google AI Studio, utilizando la biblioteca `google-genai` con soporte nativo de tipos.

### Ventajas de la Implementación
Al definir el esquema usando Pydantic, la API de Google restringe los tokens de salida para que sigan exactamente la estructura definida. Si el modelo intenta salirse de la estructura, el decodificador lo corrige en caliente.

### Ejemplo de Configuración
```python
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=OrusResponse, # Pydantic Model
        system_instruction=system_rules,
        max_output_tokens=1000,
    ),
)
```
Esto garantiza al 100% que la respuesta será un JSON válido, reduciendo el riesgo de truncamiento sintáctico a cero.
