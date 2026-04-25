# Spec 02: Supabase Connection & Memory Core

## Objetivo
Establecer una conexión segura y modular entre nuestro servidor FastAPI y el proyecto de Supabase, preparando el terreno para el almacenamiento de sesiones, la futura gestión de usuarios y la base de datos vectorial (RAG).

## Componentes Requeridos
1.  **Gestión de Entorno:** Actualizar `.env.example` para incluir `SUPABASE_URL` y `SUPABASE_KEY`.
2.  **Dependencias:** Agregar el SDK de base de datos necesario (ej. `supabase`) al archivo `requirements.txt`.
3.  **Módulo de Base de Datos:** Crear un nuevo directorio `api/db/` y dentro un archivo `supabase_client.py`. Este archivo debe contener la lógica para inicializar y exportar el cliente de Supabase utilizando las variables de entorno, aplicando el patrón Singleton o una dependencia inyectable de FastAPI.
4.  **Health Check Endpoint:** Crear un nuevo enrutador (ej. `api/routes/health.py`) con un endpoint `GET /health/db`. Este endpoint debe realizar una operación segura y básica (como verificar el estado de conexión) hacia Supabase para confirmar que el puente de red funciona.
5.  **Registro:** Actualizar `main.py` para incluir este nuevo enrutador de "health check".

## Criterios de Aceptación
* El cliente de Supabase se inicializa sin exponer credenciales.
* El endpoint `GET /health/db` retorna HTTP 200 OK si la conexión a Supabase es exitosa, o un error HTTP 500 controlado si falla la conexión.
