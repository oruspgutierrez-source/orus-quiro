# Spec 26: Migración de Dashboard a VPS (EasyPanel)

## Objetivo
Mudar el alojamiento del Dashboard desde Vercel directamente al VPS (EasyPanel) para tener el Backend y Frontend centralizados en el mismo servidor bajo el dominio `dashboard.orusquiroterapia.online`.

## Estado Actual
- El Backend ya se encuentra en el VPS usando EasyPanel (desplegado mediante Docker).
- El Dashboard es una aplicación Vite (React/SPA) que actualmente reside en el directorio `/dashboard-orus` y se despliega en Vercel.

## Tareas (Tasks)

### Task 1: Dockerizar el Dashboard
1. Crear un `Dockerfile` dentro del directorio `dashboard-orus`.
   - Utilizar un multi-stage build: una fase de construcción con Node.js (`npm run build`) y una fase de producción con Nginx para servir los archivos estáticos de la carpeta `dist`.
2. Crear un archivo de configuración de Nginx (`nginx.conf`) para asegurar que el enrutamiento de la SPA funcione correctamente (redireccionando rutas al `index.html`).

### Task 2: Actualizar `docker-compose.yml`
1. Modificar el archivo `docker-compose.yml` en la raíz del proyecto para incluir el nuevo servicio `dashboard`.
2. Configurar el contexto de construcción hacia `./dashboard-orus` y mapear el puerto de exposición.
3. Asegurar la inyección de variables de entorno (como los accesos de Supabase y la URL del Backend) si fuesen necesarias durante la etapa de construcción.

### Task 3: Integración y Push
1. Realizar un commit con la nueva infraestructura (`Dockerfile`, `nginx.conf`, y actualización de `docker-compose.yml`).
2. Hacer push al repositorio para que EasyPanel intercepte el cambio y lance el despliegue automático (si está configurado, o para que se lance de forma manual desde el panel).

---
*Esperando aprobación para comenzar con Task 1.*
