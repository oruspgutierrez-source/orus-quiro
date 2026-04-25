# Spec 07: R&D Orus Command Center & Arquitectura Base

## 1. Centro de Operaciones (Dashboard)

### 1.1 Viabilidad de Streamlit con Supabase
**Diagnóstico:** Streamlit es altamente viable y una de las soluciones más eficientes en Python para crear paneles de control internos sin fricción. 
- **Conexión a Supabase:** Se puede integrar utilizando la librería oficial `supabase-py` o manejando peticiones HTTP si se requiere algo muy ligero. Streamlit permite cachear la instancia de base de datos usando `@st.cache_resource`, lo que optimiza las llamadas.
- **Tiempo Real:** Streamlit nativamente es síncrono y se recarga de arriba hacia abajo. Sin embargo, para simular "tiempo real" o mantener el dashboard fresco, se puede utilizar el componente `st_autorefresh` o bucles `time.sleep` con `st.rerun()`. Otra alternativa más moderna es apoyarse en los canales de Realtime de Supabase procesados en segundo plano, aunque un polling cada 5 segundos mediante Streamlit suele ser suficiente y menos complejo para paneles de soporte.

### 1.2 Alertas Administrativas (python-telegram-bot)
**Diagnóstico:** Para escalar notificaciones críticas a los humanos a cargo de la operación, Telegram es la plataforma ideal debido a su API abierta y notificaciones push inmediatas.
- **Integración:** La biblioteca `python-telegram-bot` es la más madura. Dado que nuestra arquitectura usa FastAPI y `asyncio`, encaja perfectamente porque la librería de Telegram es totalmente asíncrona.
- **Casos de uso clave:** Se dispararía una alerta al `ADMIN_PHONE_ID` cuando:
  - Un usuario expresa enojo o frustración grave.
  - La IA determina explícitamente que no puede resolver la duda y necesita un humano (Handover).
  - Un usuario pasa por primera vez a un estado importante (ej. "Cliente Premium").

### 1.3 Sentiment Analysis Eficiente con Gemini
**Diagnóstico:** Ejecutar un modelo grande solo para clasificación puede disparar el uso de tokens. La estrategia para mantener esto eficiente y económico es la siguiente:
- **Respuesta Estructurada (JSON Schema):** Al enviar el prompt principal (en Spec 03) a Gemini para generar la respuesta de Orus, en lugar de solicitar solo texto plano, se le pedirá a Gemini que devuelva una estructura JSON.
- **Consolidación en una sola llamada:**
  En la misma llamada en la que el LLM genera la respuesta, se le obliga a devolver metadatos de su análisis del usuario:
  ```json
  {
    "reply": "Hola, entiendo perfectamente...",
    "sentiment": "Frustración",
    "requires_human": true
  }
  ```
- **Ventaja:** Solo gastamos los tokens de salida de unas cuantas palabras adicionales por respuesta, y evitamos hacer una llamada a una API paralela o un modelo secundario. FastAPI intercepta el JSON, guarda la data en Supabase, envía la alerta por Telegram si `requires_human` es true, y finalmente entrega solo la propiedad `"reply"` al orquestador para ser enviada al cliente.

---

## 2. Diseño de Esquema Maestro en Supabase (Propuesta SQL)

En anticipación a la creación de persistencia (Spec 06) y la visualización de los datos (Spec 07), se ha diseñado la siguiente arquitectura de tablas. **No se ejecutarán hasta su respectiva aprobación y avance de fase.**

> [!NOTE]
> Las tablas utilizan el prefijo `orus_` para mantener un orden riguroso si el proyecto comparte base de datos con otros servicios, y hacen uso nativo de UUIDs y JSONB de PostgreSQL para máxima flexibilidad.

### Tabla: `orus_users`
Contiene la información de los leads y el estado actual de su sesión (si habla con la IA o si un humano ha tomado el control).

```sql
-- CONCEPTUAL DDL: No ejecutar en esta fase.
CREATE TABLE orus_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_number VARCHAR(50) UNIQUE NOT NULL,
    wa_name VARCHAR(255),
    session_mode VARCHAR(20) DEFAULT 'AI', -- Posibles valores: 'AI', 'HUMAN'
    admin_notified BOOLEAN DEFAULT FALSE,  -- True si ya mandamos Telegram alert
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_interaction TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Tabla: `orus_messages`
Registra el historial conversacional. Cada registro sirve como memoria para el contexto de la IA y como punto de dato para el Dashboard.

```sql
-- CONCEPTUAL DDL: No ejecutar en esta fase.
CREATE TABLE orus_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES orus_users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,            -- 'user' (cliente), 'assistant' (Orus), 'system' (contexto)
    content TEXT NOT NULL,                -- El cuerpo del mensaje (con ||| incluidos si aplica)
    sentiment_flag VARCHAR(50),           -- Ej. 'Neutral', 'Frustrated', 'Curious', 'Angry'
    requires_human BOOLEAN DEFAULT FALSE, -- Flag levantada por Gemini
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indice para recuperar historial de chat rápidamente
CREATE INDEX idx_orus_messages_user_id ON orus_messages(user_id);
```

---

## 3. Próximos Pasos (Pendiente de Autorización)

1. **Aprobación de la Arquitectura:** Confirmar si el esquema SQL satisface todas las necesidades de la visión ampliada.
2. **Ejecución (Fase Posterior):** 
   - Ejecutar el SQL de creación en Supabase.
   - Refactorizar FastAPI para usar el esquema JSON de Gemini y guardar los mensajes en la DB.
   - Iniciar la integración del bot de Telegram.
