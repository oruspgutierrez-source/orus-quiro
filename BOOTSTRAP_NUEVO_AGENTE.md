# Orus-Quiro: Guía de Arranque para Nuevo Agente (Antigravity Bootstrap)

> **ATENCIÓN AGENTE (ANTIGRAVITY):** Si estás leyendo este archivo, acabas de ser instanciado en un nuevo equipo (PC principal) para tomar el control del ecosistema de desarrollo y operaciones del proyecto **Orus-Quiro**.
> Tu objetivo principal es configurar tu propio entorno, establecer enlaces de comunicación remotos y continuar el desarrollo del sistema.

Sigue paso a paso este procedimiento de inicialización. Si te atascas en algún paso que requiera permisos fuera de tu alcance, **guía al usuario de manera clara para que lo realice manualmente**.

---

## FASE 1: Clonación y Sincronización del Proyecto

1. **Verificar MCP de GitHub:** Confirma que tienes acceso a las herramientas del MCP de GitHub (`mcp_github_*`).
2. **Clonar Repositorio:** Si te han pasado este archivo suelto o estás en una carpeta vacía, usa tus herramientas o ejecuta comandos de terminal para clonar el repositorio principal:
   * Repo: `oruspgutierrez-source/orus-quiro`
   * Comando: `git clone https://github.com/oruspgutierrez-source/orus-quiro.git .`
3. **Exploración Inicial:** Revisa brevemente la estructura del directorio (`/api`, `/dashboard-orus`, `/specs`).

---

## FASE 2: Conexión Remota al VPS (EasyPanel)

El entorno de producción se encuentra alojado en un VPS remoto (`194.163.142.112`). Para que puedas administrar los contenedores, leer logs y solucionar problemas en vivo, necesitas acceso SSH.

1. **Generación de Llave SSH:**
   * Utiliza tus herramientas de ejecución de comandos (`run_command`) para verificar si existe una llave SSH en `C:\Users\tu-usuario\.ssh\id_rsa` o `id_ed25519`.
   * Si no existe, genera una silenciosamente: `ssh-keygen -t ed25519 -N "" -f "$HOME\.ssh\id_ed25519"`
2. **Autorización en el VPS:**
   * **Pide ayuda al humano:** Lee el contenido de la llave pública recién generada (`cat ~/.ssh/id_ed25519.pub` o similar) y muéstrasela al usuario en la pantalla.
   * Pídele explícitamente al humano que copie ese texto y lo añada al archivo `~/.ssh/authorized_keys` del VPS (puede hacerlo desde la terminal web de EasyPanel o pidiéndoselo al agente de la laptop anterior).
3. **Prueba de Conexión:**
   * Una vez que el usuario te confirme que añadió la llave, realiza un ping SSH: `ssh -o StrictHostKeyChecking=accept-new root@194.163.142.112 "echo 'Conexión exitosa desde nuevo agente'"`
4. **Setup MCP SSH (Opcional pero recomendado):** Si es soportado, instruye al usuario para que añada el servidor MCP de SSH a tu configuración de Antigravity para facilitarte operaciones remotas estructuradas.

---

## FASE 3: Enlace con Base de Datos (Supabase)

El sistema centraliza todos sus datos (usuarios, logs, mensajes) en Supabase.
1. **Verificar MCP de Supabase:** Confirma si tienes cargado un servidor MCP que te permita interactuar directamente con Supabase. 
2. Si no lo tienes, revisa el archivo `api/db/supabase_client.py` y `dashboard-orus/src/supabaseClient.js` para entender cómo se conecta la aplicación.

---

## FASE 4: Contextualización del Proyecto

Antes de empezar a codificar o proponer cambios, **debes leer de forma obligatoria**:
1. `INSTRUCCIONES_AGENTE.md`: Reglas base del proyecto y tono de personalidad del bot (El Escultor).
2. Los archivos en la carpeta `/specs`, particularmente los más recientes (`spec_26`, `spec_27`, `spec_28`) para entender el estado actual del Dashboard y la migración al VPS.
3. Comprender que el sistema envía WhatsApps nativos usando **Evolution API**, cuyo endpoint está ya conectado en el Backend.

---

**[Para el Usuario Humano]**
Cuando abras Antigravity en tu nueva PC, simplemente arrastra este archivo, o dile al agente: *"Acabo de clonar el proyecto, por favor lee el archivo BOOTSTRAP_NUEVO_AGENTE.md y ejecuta los pasos de inicialización."*
