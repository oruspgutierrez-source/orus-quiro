# Spec 37: Análisis de Migración de Gemini a OpenRouter (Modelos de Bajo Costo)

## 1. Viabilidad de OpenRouter en la Arquitectura de Orus
Migrar el bot de Orus de la API oficial de Google Gemini a **OpenRouter** es técnicamente factible y económicamente muy ventajoso. OpenRouter permite acceder a una gran variedad de modelos (incluyendo la familia DeepSeek de China, Llama 3.3 de Meta, Claude de Anthropic, etc.) utilizando una única API unificada compatible con el formato de OpenAI.

### Comparación de Costos Estimados (por 1M de tokens)
| Proveedor / Modelo | Costo Input (por 1M) | Costo Output (por 1M) | Soporte de Herramientas (Tool Calling) |
| :--- | :--- | :--- | :--- |
| **Gemini 2.5 Flash** (Google) | ~$0.075 USD (Gratis en tier bajo, pero requiere saldo) | ~$0.30 USD | Excelente |
| **DeepSeek V3** (`deepseek/deepseek-chat`) | **$0.14 USD** | **$0.28 USD** | Excelente |
| **Llama 3.3 70B Instruct** | **$0.12 USD** | **$0.30 USD** | Excelente |
| **Qwen 2.5 72B Instruct** (Alibaba - Chino) | **$0.23 USD** | **$0.40 USD** | Excelente |

> [!NOTE]
> Aunque Gemini 2.5 Flash es técnicamente barato en consumo por token, Google AI Studio bloquea el uso productivo de forma agresiva si no se mantiene una cuenta con recargas prepagadas elevadas (exigiendo un mínimo de saldo inicial). Con OpenRouter, puedes usar tu saldo existente para consumir modelos extremadamente inteligentes por una fracción de centavo.

---

## 2. Impacto y Cambios Requeridos en la Infraestructura
El impacto de la migración está **altamente acotado** gracias a que el código del bot está estructurado con un patrón de diseño desacoplado. El archivo `api/services/gemini_client.py` actúa como una caja negra: el resto del sistema (`message_processor.py`) no sabe qué modelo está detrás, solo recibe un JSON estructurado.

### Cambios en `api/services/gemini_client.py` (Orquestador LLM)
Para cambiar a OpenRouter, debemos reemplazar el SDK `google-genai` por el SDK de `openai` (configurando el `base_url` hacia OpenRouter) o mediante peticiones directas HTTP asíncronas con `httpx`.

#### 1. Formato de Historial de Mensajes
Gemini usa la estructura `role: "user" | "model"`.
OpenRouter (OpenAI format) requiere la estructura estándar de chat:
```python
contents = [
    {"role": "system", "content": "System prompt..."},
    {"role": "user", "content": "Hola"},
    {"role": "assistant", "content": "JSON..."},
]
```

#### 2. Declaración de Herramientas (Tools / Function Calling)
Debemos transformar la forma en que definimos las funciones. 
*   **Gemini (Actual):** Usa objetos de tipo `FunctionDeclaration` de Google.
*   **OpenRouter (Nuevo):** Usa el formato estándar de OpenAI:
    ```json
    {
      "type": "function",
      "function": {
        "name": "check_free_slots",
        "description": "...",
        "parameters": {
          "type": "object",
          "properties": { ... }
        }
      }
    }
    ```

#### 3. Bucle de Ejecución de Herramientas
El bucle multiturno para resolver llamadas a funciones debe adaptarse al formato OpenAI:
*   Cuando el modelo decide llamar a una función, devuelve un campo `tool_calls`.
*   Ejecutamos la función y añadimos la respuesta al historial con el rol `"tool"` y el `tool_call_id` correspondiente.
*   Volvemos a llamar al modelo enviando todo el historial actualizado.

---

## 3. Alternativas de Modelos Recomendados en OpenRouter

### Alternativa A: DeepSeek V3 (`deepseek/deepseek-chat`)
Es el modelo insignia actual de DeepSeek. Tiene capacidades de razonamiento matemático, lógico y de programación al nivel de GPT-4o, pero a un costo 10 veces menor.
*   **Ventajas:** Racionalidad extremadamente alta, respeta instrucciones JSON de forma excelente, soporta Tool Calling nativo de forma muy estable.
*   **Costo:** Prácticamente gratis ($0.14 / $0.28 por millón de tokens).

### Alternativa B: Qwen 2.5 72B Instruct (`qwen/qwen-2.5-72b-instruct`)
Desarrollado por Alibaba (China). Es uno de los modelos de código abierto más potentes del mundo.
*   **Ventajas:** Excelente soporte multiidioma (español fluido), gran capacidad para seguir formatos complejos y llamadas a funciones robustas.

### Alternativa C: Llama 3.3 70B Instruct (`meta-llama/llama-3.3-70b-instruct`)
El modelo open-source de Meta ejecutado en servidores optimizados de OpenRouter.
*   **Ventajas:** Muy rápido, excelente en tareas de chat y extremadamente barato.

---

## 4. Plan de Acción para la Migración
Si decides avanzar con esta migración, el plan de trabajo estructurado es:

1.  **Instalar dependencia:** Añadir `openai` o `httpx` a `requirements.txt`.
2.  **Configurar Variables:** Añadir `OPENROUTER_API_KEY` en EasyPanel y el modelo seleccionado (ej: `deepseek/deepseek-chat`).
3.  **Refactorizar `gemini_client.py`:** Reescribir la función `generate_response` para enviar el payload al endpoint de chat completions de OpenRouter con el formato de herramientas de OpenAI.
4.  **Adaptar los Retornos:** Asegurar que las respuestas de las herramientas locales (`check_free_slots`, etc.) se devuelvan en el formato de mensajes de OpenAI.
5.  **Pruebas de Integración:** Verificar el flujo de bienvenida, agendamiento y links de pago usando el simulador.
