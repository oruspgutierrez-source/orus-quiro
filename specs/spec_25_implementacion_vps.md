# Spec 25: Implementación en VPS y Vercel (Producción)

## 1. Objetivo y Resumen
El objetivo principal de esta fase fue desplegar y conectar todos los componentes de la aplicación Orus Quiroterapia en entornos de producción definitivos, abandonando las conexiones locales mediante `ngrok` y reemplazándolas por un servidor expuesto con HTTPS real en un dominio propio. Adicionalmente, se conectó la interfaz gráfica del Dashboard al Backend de producción y a Supabase.

## 2. Acciones Realizadas

### 2.1 Backend en VPS (EasyPanel)
- Se montó el código fuente en un contenedor Docker manejado por **EasyPanel**.
- Se configuró el dominio `api.orusquiroterapia.online` con certificado SSL (Traefik).
- Se cargó el archivo `credentials.json` montando un volumen persistente en EasyPanel `/app/credentials.json`.
- Se corrigió un error en el que `google-api-python-client` y `google-auth` faltaban en `requirements.txt`, lo cual provocaba caídas del bot al consultar Google Calendar.
- Se actualizaron las variables de entorno para la integración de Stripe y Webhooks.

### 2.2 Integración Webhooks
- El bot (Evolution API) y Stripe ahora apuntan directamente a `https://api.orusquiroterapia.online/webhook` y `https://api.orusquiroterapia.online/payments/webhook`, eliminando bloqueos de Vercel por mixed-content (HTTP vs HTTPS).

### 2.3 Dashboard en Vercel
- Se limpió el repositorio de una carpeta pesada (`node_modules`) que bloqueaba los despliegues de Vercel.
- Se forzó el despliegue del código de `dashboard-orus` directamente a Vercel usando `vercel cli`.
- **Conexión a Datos Reales (Supabase):**
  - Se creó un cliente `supabaseClient.js`.
  - Se modificó `DashboardView.jsx` para dejar de usar datos locales de prueba (Mocks).
  - El Dashboard ahora muestra en tiempo real el total de usuarios interactuando, el total de mensajes procesados, y las alertas "Handover" de clientes que solicitan atención humana.

### 2.4 Handovers de Cliente (Modo Humano)
- Se actualizó el `.env` de producción (`ADMIN_WHATSAPP_NUMBER`) al número de Meta `15556348064` para que el sistema envíe los avisos de Handover de forma separada al administrador cuando un cliente pida hablar con un humano.
- Se generaron scripts automáticos para retornar al estado "BOT" (`session_mode: 'AI'`) a los clientes de prueba que quedaron atascados en `HUMAN`.

## 3. Próximos Pasos (Pendiente para la tarde)
- **Log System en el Dashboard:** Configurar la pestaña "System Logs" para que consuma en vivo el registro de eventos técnicos y conversacionales del servidor.
- **Inbox Chat (Dashboard):** Reemplazar los datos simulados de la pestaña "Inbox Chat" para reflejar el historial real del paciente que solicita ayuda humana.
- **Handover Test con dos números:** El usuario realizará pruebas con el teléfono de su pareja simulando un cliente, mientras que el administrador recibirá alertas en el teléfono configurado en EasyPanel.
