# Orus Quiro Backend

Backend en FastAPI para el asistente virtual de quiromancia védica "Orus", con soporte para Webhooks de Meta, IA (Gemini), almacenamiento en Supabase y notificaciones vía Telegram.

## Requisitos
- Python 3.10+
- Credenciales de Supabase, Meta y Google Gemini.

## Instalación y Ejecución

1. **Clonar el repositorio**
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd proyecto orus-quiro
   ```

2. **Crear Entorno Virtual e Instalar Dependencias**
   ```bash
   python -m venv venv
   # En Windows:
   .\venv\Scripts\activate
   # En macOS/Linux:
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```

3. **Configurar Variables de Entorno**
   Copia el archivo `.env.example` a `.env` y rellena las claves.
   ```bash
   cp .env.example .env
   ```

4. **Levantar el Servidor**
   ```bash
   uvicorn main:app --port 8000 --reload
   ```

## Estructura
- `/api`: Rutas y lógica de negocio.
- `/api/services/orchestrator.py`: Maneja el flujo de mensajes (Debounce y agrupamiento asíncrono).
- `/api/routes/dashboard.py`: Endpoints para el Command Center (Frontend externo).
