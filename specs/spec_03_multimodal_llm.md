# Spec 03: Multimodal LLM Core (Gemini Última Generación)

## Objetivo
Integrar el SDK oficial de Google GenAI para dotar al sistema de capacidades de procesamiento de lenguaje natural y sentar las bases para la futura ingesta multimodal (imágenes de manos y audios). 

## Componentes Requeridos
1.  **Dependencias:** Actualizar `requirements.txt` con el SDK de Google más actual para Python.
2.  **Servicio LLM:** Crear un nuevo directorio `api/services/` y dentro un archivo `gemini_client.py`. Este módulo debe:
    * Configurar la API key de forma segura.
    * Inicializar una instancia del modelo **Flash** más reciente y potente que esté disponible (ej. gemini-2.5-flash, gemini-3.1-flash o superior).
    * Exponer una función asíncrona básica (ej. `generate_response(prompt: str)`) que envíe un texto al modelo y retorne la respuesta.
3.  **Endpoint de Prueba de Inteligencia:** Crear un nuevo enrutador `api/routes/llm_test.py` con un endpoint `POST /health/llm`. 
    * Debe recibir un JSON básico: `{"prompt": "Hola, ¿eres un experto en quiromancia védica?"}`.
    * Debe procesarlo a través de `gemini_client.py` y devolver la respuesta de la IA.
4.  **Registro:** Actualizar `main.py` para incluir este nuevo enrutador.

## Criterios de Aceptación
* El cliente no expone credenciales.
* El endpoint responde exitosamente con texto generado por el modelo Flash actualizado.
