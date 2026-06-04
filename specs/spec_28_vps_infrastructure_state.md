# Orus Quiro - VPS Infrastructure State

Este documento sirve como la fuente de la verdad para el estado de la infraestructura en producción (VPS gestionada por EasyPanel). El proyecto en EasyPanel se llama **`whatsapp-api`**.

Debe ser actualizado cada vez que se agreguen nuevos servicios, se cambien variables de entorno clave, o se modifiquen dominios.

## 1. EasyPanel Services

### 1.1 `orus-backend`
- **Tipo**: Aplicación (Python/FastAPI)
- **Repositorio**: `oruspgutierrez-source/orus-quiro` (Rama: `main`)
- **Directorio de construcción**: `/` (Raíz del repositorio)
- **Dominios**: 
  - `https://whatsapp-api-orus-backend.bybcsf.easypanel.host` -> puerto interno `80`
  - `https://api.orusquiroterapia.online` -> puerto interno `8000`
- **Variables de Entorno Configuradas**:
  - `SUPABASE_URL=https://rfwfveaudrnughtulbco.supabase.co`
  - `SUPABASE_KEY=sb_publishable_vhupF9kAOgV3GG-4TEMlPQ_jhqLPxY6`
  - `GEMINI_API_KEY=...`
  - `TELEGRAM_BOT_TOKEN=...`
  - `TELEGRAM_CHAT_ID=8158168585`
  - `CALENDAR_ID=oruspgutierrez@gmail.com`
  - `ENVIRONMENT=production`
  - `EVOLUTION_API_URL=http://evolution-api:8080` *(Nota: Si hay problemas de red interna, usar `http://whatsapp-api_evolution-api:8080`)*
  - `EVOLUTION_INSTANCE_NAME=OrusBot`
  - `EVOLUTION_API_KEY=Vida2025@`
  - `UPSTASH_REDIS_URL=rediss://...`
  - `STRIPE_SECRET_KEY=...`
  - `STRIPE_WEBHOOK_SECRET=...`
  - `ADMIN_WHATSAPP_NUMBER=15556348064`
  - `VPS_DOMAIN_URL=https://api.orusquiroterapia.online`
  - `API_SECRET_KEY=OrusDashboardAdmin2026`
  - `GOOGLE_CREDENTIALS_JSON={ ... }` *(Contenido del archivo JSON de la Service Account en una sola línea)*

### 1.2 `orus-dashboard`
- **Tipo**: Aplicación (Node.js/Vite/React)
- **Repositorio**: `oruspgutierrez-source/orus-quiro` (Rama: `main`)
- **Directorio de construcción**: `/dashboard-orus`
- **Comando de Build**: `npm run build`
- **Dominios**: 
  - `https://whatsapp-api-orus-dashboard.bybcsf.easypanel.host` -> puerto interno `80`
  - `https://dashboard.orusquiroterapia.online` -> puerto interno `80`
- **Variables de Entorno Configuradas**:
  - `VITE_SUPABASE_URL=https://rfwfveaudrnughtulbco.supabase.co`
  - `VITE_SUPABASE_ANON_KEY=sb_publishable_vhupF9kAOgV3GG-4TEMlPQ_jhqLPxY6`
  *(Nota: Se recomienda agregar explícitamente `VITE_API_URL=https://api.orusquiroterapia.online` y `VITE_API_KEY=OrusDashboardAdmin2026` aunque el código tenga fallbacks).*

### 1.3 `evolution-api`
- **Tipo**: Servicio de terceros (Evolution API / Instancia de WhatsApp)
- **Dominios**:
  - `https://whatsapp.orusquiroterapia.online` -> puerto interno `8080`
- **Variables de Entorno Configuradas**:
  - `SERVER_URL=https://whatsapp.orusquiroterapia.online`
  - `AUTHENTICATION_API_KEY=Vida2025@`
  - `DATABASE_PROVIDER=postgresql`
  - `DATABASE_CONNECTION_URI=postgresql://postgres:b5d7bbe1b54f5bf8f4eb@whatsapp-api_db-postgres:5432/whatsapp-api?schema=public`
  - `CACHE_REDIS_ENABLED=true`
  - `CACHE_REDIS_URI=redis://default:81f7cba07f1b07c9055d@whatsapp-api_db-redis:6379/0`
  - `DOCS=true`
  - `CONFIG_SESSION_PHONE_VERSION=2.3000.1033773198`

### 1.4 `db-postgres`
- **Tipo**: Base de datos (PostgreSQL)
- **Uso**: Base de datos interna de Evolution API
- **Host Interno**: `whatsapp-api_db-postgres`
- **Puerto**: `5432`
- **Credenciales**: Usuario `postgres`, Password `b5d7bbe1b54f5bf8f4eb`

### 1.5 `db-redis`
- **Tipo**: Base de datos (Redis)
- **Uso**: Caché interna de Evolution API
- **Host Interno**: `whatsapp-api_db-redis`
- **Puerto**: `6379`
- **Credenciales**: Usuario `default`, Password `81f7cba07f1b07c9055d`

## 2. Supabase (BaaS Externo)
- **URL**: `https://rfwfveaudrnughtulbco.supabase.co`
- **Tablas principales**:
  - `orus_users` (Directorio de clientes de WA)
  - `orus_messages` (Historial de chat en tiempo real)
  - `orus_logs` / `orus_system_logs` (Telemetría y errores de infraestructura con interfaz de estado 'resolved')
  - `orus_agent_interventions` (Registro de handovers)
  - `orus_session_notes` (Bitácora Clínica vinculada a eventos de Google Calendar. Implementa UI con modal flotante para lectura y soporte de borrado con UUID real.)

## 3. Comandos Frecuentes
Para forzar actualizaciones en la VPS mediante EasyPanel:
1. Ir al servicio correspondiente (`orus-backend` o `orus-dashboard`).
2. Presionar **Deploy** para descargar los últimos cambios de GitHub `main`.
