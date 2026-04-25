# Spec 01: Core Backend & Meta Webhooks

## Objetivo
Establecer la base del servidor FastAPI y configurar los endpoints de webhooks necesarios para la validación y recepción de mensajes de la Meta Cloud API (WhatsApp e Instagram).

## Componentes Requeridos
1.  **Gestión de Entorno:** Un archivo `.env.example` y la lógica para cargar variables de entorno (ej. `META_VERIFY_TOKEN`).
2.  **Servidor Base:** Un archivo `main.py` que inicialice la aplicación FastAPI.
3.  **Rutas (Routers):** Un directorio `api/routes/` que contenga un archivo `webhooks.py`.
4.  **Endpoints Específicos:**
    * `GET /webhook`: Debe manejar la verificación de Meta (recibir `hub.mode`, `hub.verify_token` y devolver el `hub.challenge`).
    * `POST /webhook`: Debe recibir la carga útil (payload) JSON de los mensajes entrantes de Meta y devolver un HTTP 200 OK inmediatamente.
5.  **Dependencias:** Un archivo `requirements.txt` con `fastapi`, `uvicorn` y cualquier otra librería esencial.

## Criterios de Aceptación
* El servidor debe poder ejecutarse localmente con `uvicorn main:app --reload`.
* El endpoint `GET /webhook` debe validar correctamente un token de prueba.
