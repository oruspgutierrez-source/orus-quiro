# Mapa de Arquitectura del Sistema Orus

Este documento presenta gráficamente el flujo de datos y la topología del backend.

## Flujo de Mensajería y Pipeline Multimodal

```mermaid
graph TD
    %% Entidades Externas
    User((Usuario de WhatsApp))
    EvolutionAPI[VPS Evolution API]
    Gemini[Google Gemini 2.5 Flash]
    Supabase[(Supabase BD)]
    
    %% API FastAPI
    subgraph Orus Backend FastAPI
        WebhookRoute[webhooks.py POST /webhook]
        MsgProc[message_processor.py]
        GeminiClient[gemini_client.py]
        DBClient[db_client.py]
        
        %% Componentes internos de MsgProc
        Buffer[(Sliding Window Buffer\n10 seg Debounce)]
        FFMPEG[FFmpeg Audio Converter]
    end
    
    %% Flujo
    User -- Envía Texto/Imagen/Audio --> EvolutionAPI
    EvolutionAPI -- Envía Payload JSON --> WebhookRoute
    WebhookRoute -- Parsea e ignora ecos/historia --> MsgProc
    
    MsgProc -- Guarda en --> Buffer
    Buffer -- Pasan 10 seg silencio --> MsgProc
    
    MsgProc -- Extrae Base64 / Transforma Audio --> FFMPEG
    MsgProc -- Formatea Prompt Multimodal --> GeminiClient
    
    GeminiClient -- Petición REST + Binarios --> Gemini
    Gemini -- Retorna Respuesta Texto --> GeminiClient
    
    GeminiClient -- Pasa texto --> MsgProc
    MsgProc -- Guarda Logs (Spec 08) --> DBClient
    DBClient -- Inserción asíncrona --> Supabase
    
    MsgProc -- Trocea respuesta (|||) --> EvolutionAPI
    EvolutionAPI -- Envía de vuelta --> User

    %% Estilos
    style User fill:#25D366,stroke:#128C7E,stroke-width:2px,color:#fff
    style EvolutionAPI fill:#f39c12,stroke:#e67e22,stroke-width:2px,color:#fff
    style Gemini fill:#4285F4,stroke:#34a853,stroke-width:2px,color:#fff
    style Supabase fill:#3ECF8E,stroke:#249361,stroke-width:2px,color:#fff
    style Orus Backend FastAPI fill:#2C3E50,stroke:#34495E,stroke-width:2px,color:#fff
```

### Componentes Clave
1. **Sliding Window Buffer:** Permite la agregación de múltiples mensajes (texto, imágenes, audios) enviados en una "ráfaga" por el usuario en una única intención para Gemini.
2. **FFmpeg Converter:** Evita errores de compatibilidad convirtiendo nativamente el `audio/ogg; codecs=opus` de WhatsApp Web a `audio/mp3`.
3. **Mapeo Explícito Multimodal:** En `gemini_client.py`, los binarios están aislados con etiquetas `[--- INICIO DEL ARCHIVO X ---]` para evitar que Gemini mezcle contexto entre texto y audio.
