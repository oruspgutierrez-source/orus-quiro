# Architecture

## Stack Tecnológico
- **Lenguaje:** Python
- **Framework Web:** FastAPI + Uvicorn
- **Base de Datos:** Supabase (PostgreSQL)
- **LLM:** Google Gemini (gemini-2.5-flash) via google-genai SDK
- **WhatsApp:** Evolution API v2.2.3 (instancia OrusBot en VPS)
- **Debounce:** asyncio nativo (Sliding Window Cancel-and-Restart, 10s)
- **Túnel dev:** ngrok (dominio fijo: annually-murmuring-reuse.ngrok-free.dev)

## Reglas de Arquitectura
- **Thin Client, Fat Server:** La lógica de negocio y el procesamiento principal deben residir en el servidor (backend). El cliente debe mantenerse ligero, encargándose principalmente de la presentación de la interfaz y la recolección de entradas del usuario.

## Fases Futuras y Procesos a Estructurar (Post-Integración WhatsApp)

Una vez que el flujo base del chatbot con WhatsApp (Z-API/Evolution) esté operativo, la arquitectura se expandirá para interactuar con dos interfaces front-end independientes ya creadas en otro proyecto.

### 1. Aplicación de Recolección de Datos del Usuario (Mini-App Web)
Esta aplicación operará como el punto de entrada para que el usuario proporcione sus datos de forma estructurada antes de la sesión de quiromancia.
- **Flujo de Acceso:** El bot generará y enviará un enlace único al cliente a través del chat de WhatsApp.
- **Formulario Personal:** Recolección de datos personales básicos del paciente.
- **Prueba Psicométrica:** Un módulo interactivo para captar datos conductuales y psicológicos.
- **Carga Multimodal (Fotografía de Manos):** Un sistema de subida con instrucciones visuales, que permitirá al usuario acceder a su cámara para tomar la foto en tiempo real o cargarla desde la galería.
- **Envío y Persistencia:** Al presionar enviar, el paquete completo se guarda en **Supabase** (asociado al `user_id` del paciente).

### 2. Dashboard Principal de Administración
Este será el panel de control central (Command Center) del terapeuta.
- **Sincronización:** Escuchará (vía Realtime o fetch) a Supabase para mapear e inyectar los datos en la interfaz.
- **Consolidación de Datos:** Unificará las interacciones del agente de WhatsApp, el estado en las plataformas de pago y el paquete de datos/imágenes subidos desde la Mini-App.
- **Disparador Operativo:** La visualización de la ficha completa del usuario en este Dashboard será el punto de inicio para la "lectura" holística.

*Nota: La estructura exacta de estos flujos, la estructura de datos (tablas) y las peticiones de modificación de interfaz se definirán (mediante nuevos Specs) una vez se reciban los datos exactos sobre la conformación actual del Dashboard y la Mini-App.*
