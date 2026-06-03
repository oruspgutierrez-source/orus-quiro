# Análisis de Viabilidad y Estrategia de Despliegue en VPS (Bot + Dashboard)

## 1. Análisis de Infraestructura Actual (Readiness para Producción)

Tras analizar la arquitectura actual del backend (FastAPI) y el frontend (Dashboard React/Vite), se han identificado puntos críticos que **DEBEN** resolverse antes de exponer el sistema en un entorno de producción (VPS) para garantizar seguridad ("minado") y estabilidad.

### Puntos Críticos Encontrados:
1. **Seguridad en Endpoints del Dashboard:** Las rutas en `api.routes.metrics` y `api.routes.dashboard` no tienen protección de autenticación (JWT o API Key). Cualquier persona con la IP/Dominio de la VPS podría leer las métricas o enviar mensajes manuales.
2. **CORS Inseguro:** En `main.py`, `CORSMiddleware` está configurado con `allow_origins=["*"]`. En producción, debe restringirse exclusivamente al dominio del Dashboard (ej. `https://dashboard.orus-quiro.com`).
3. **Manejo de Webhooks (Evolution API):** La ruta `/webhook` no valida el origen de la petición. Se recomienda implementar un secreto o validación de header para evitar que atacantes inyecten mensajes falsos.
4. **Ejecución del Servidor:** Actualmente se usa `uvicorn ... --reload`. En producción, se debe usar un gestor de procesos como **Gunicorn** con *workers* de Uvicorn, o **Docker** + **PM2** para reiniciar automáticamente en caso de caídas.
5. **Debounce en Memoria vs Serverless:** El bot utiliza `asyncio.sleep()` en memoria para el *debounce* de mensajes. Esto hace **imposible** alojarlo en Vercel (Serverless mata los procesos en background). **La VPS es obligatoria y correcta para el backend.**

---

## 2. Proceso Recomendado para el Despliegue

La estrategia más segura y profesional divide el proyecto en dos capas:

### Capa 1: Frontend (Dashboard) -> Vercel
* El código en `dashboard-orus` es estático (React/Vite). Su lugar ideal es **Vercel**, ya que ofrece CDN global, SSL automático y despliegue continuo desde GitHub gratis.
* **Configuración:** Solo requiere crear variables de entorno (ej. `VITE_API_URL=https://api.tudominio.com`).

### Capa 2: Backend (Bot FastAPI) -> VPS (Ubuntu)
* El código del bot requiere ejecución continua.
* **Proceso de instalación:**
  1. Conectar la VPS a GitHub (clonar el repositorio).
  2. Usar **Docker Compose** (recomendado para aislar dependencias) o un entorno virtual (venv) con **Systemd**.
  3. Configurar **Nginx** (o Caddy) como Reverse Proxy para exponer el puerto 8000 al puerto 443 (HTTPS) con un certificado SSL gratuito de Let's Encrypt.
  4. Crear un `.env.production` con las credenciales reales.

---

## 3. Cambios Necesarios en Supabase (`pg_net`)

Actualmente, Supabase envía notificaciones (como la finalización de la biometría) a través de *Database Webhooks* (`pg_net`).
* **Problema:** Están apuntando a la URL de ngrok (o a una URL temporal de Vercel).
* **Solución:** Una vez que la VPS tenga su dominio/IP fijo (ej. `https://api.tudominio.com/api/biometrics/completed`), será necesario ejecutar un script SQL en Supabase (o usar el panel web) para **actualizar el endpoint del trigger**.

---

## 4. Plan de Acción (Specs Propuestos)

Se proponen las siguientes Tasks para completar el pase a producción de forma segura:

- [x] **Task 1: Hardening del Backend (Seguridad)**
  - [x] Implementar API Key o Token simple para proteger las rutas de `/api/metrics` y `/api/users`.
  - [x] Configurar CORS dinámico según el entorno (`.env`).
  - [x] Agregar validación básica al `/webhook` de Evolution API.

- [x] **Task 2: Preparación Docker / Systemd**
  - [x] Crear un `Dockerfile` y `docker-compose.yml` para el backend, o en su defecto, un script `.sh` de despliegue automatizado para Ubuntu/VPS.
  - [x] Eliminar la dependencia de `register_webhook.py` basada en ngrok, creando un script de registro de webhook para producción (`register_prod_webhook.py`).

- [ ] **Task 3: Despliegue del Dashboard en Vercel**
  - Conectar la carpeta `dashboard-orus` a Vercel.
  - Integrar la autenticación de la Task 1 en las llamadas Axios/Fetch del frontend.

- [ ] **Task 4: Despliegue en VPS y Configuración de Supabase**
  - Clonar repo en VPS, configurar `.env.production`, arrancar servidor.
  - Configurar Nginx y Let's Encrypt.
  - Actualizar webhooks en Supabase y registrar webhooks de Evolution API/Stripe hacia la nueva URL.

**Conclusión de Viabilidad:** El bot es estructuralmente viable para producción, pero **requiere la capa de seguridad (Hardening)** antes de ser expuesto en internet abierto. La elección de VPS para backend y Vercel para frontend es el estándar de la industria y el camino más sólido.

---

## 5. Estrategia de Monitoreo Autónomo (MCP + EasyPanel en VPS)

La propuesta de utilizar un Servidor MCP (Model Context Protocol) en la VPS es **altamente viable y recomendada**. Permitirá que el Agente AI (Antigravity) tenga telemetría en tiempo real y capacidad de corrección de código sin intervención humana directa.

### ¿Qué se logra con esta integración?
1. **Auditoría en tiempo real:** Leer logs de EasyPanel/Docker, métricas de RAM/CPU, y logs de FastAPI.
2. **Ciclo CI/CD Autónomo:** El agente puede diagnosticar errores locales, escribir la solución, hacer `git push`, y mediante MCP, instruir a la VPS a hacer un redeploy en EasyPanel.
3. **Análisis de Metadatos:** Consultar directamente Supabase (o Redis) y procesar sentimientos y logs de errores sin salir del entorno.

### Acciones Externas Requeridas por el Usuario (Paso a Paso)

Para que el Agente pueda operar la VPS de esta manera, el usuario debe realizar **solo una de estas dos opciones** externas:

**Opción A (La más rápida): Instalar un Servidor MCP de SSH localmente**
1. Consigue las credenciales SSH de tu VPS. **Nota:** EasyPanel no proporciona la contraseña SSH en su interfaz web. Debes buscar el correo de bienvenida de tu proveedor de hosting (Hostinger, Hetzner, DigitalOcean, etc.) o entrar a su panel para ver la IP (`217.196.61.72`), usuario (usualmente `root` o `ubuntu`) y la contraseña o clave `.pem`.
2. Configura un servidor MCP de SSH en tu cliente Claude/Cursor/Cline local.
3. *Resultado:* El Agente se conecta por SSH a tu VPS de forma transparente a través de tu máquina y opera Docker/EasyPanel por terminal.

**Opción B (Nativa VPS): Instalar un Servidor MCP en la VPS**
1. Entra a la VPS y crea un contenedor ligero que exponga una API segura (MCP).
2. Conecta tu entorno local (Claude/Cursor) a la URL de ese servidor MCP.
3. *Resultado:* La VPS expone sus herramientas (leer logs, ejecutar bash) de forma segura al Agente.

**Recomendación:** La **Opción A (SSH MCP o tool de SSH directo)** es la más segura porque no expone puertos adicionales en la VPS y aprovecha el protocolo de seguridad nativo de la nube. 

**Siguiente paso:** Decide qué opción prefieres (SSH directo o MCP en VPS) y proporciona las credenciales/IP (si es seguro) o instálalo localmente para comenzar el despliegue.
