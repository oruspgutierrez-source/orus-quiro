# Spec 09: Frontend Plan - Orus Command Center (Phase 1)

## 1. Stack Tecnológico
*   **Core:** React + Vite (Fast HMR, empaquetado optimizado).
*   **Styling:** TailwindCSS (para el desarrollo ágil de la interfaz basada en utilidades).
*   **Iconografía:** `lucide-react` (reemplazando los iconos estáticos para tener componentes dinámicos y escalables en React).
*   **Enrutamiento:** `react-router-dom` (para manejar la navegación entre Dashboard, Calendar, Logs y Chat sin recargar la página).

## 2. Arquitectura de Componentes
La aplicación se estructurará modularmente para facilitar la reutilización y el acoplamiento futuro con FastAPI:

*   **`AppLayout.jsx`**: El contenedor principal persistente. Gestiona el enrutamiento interno.
    *   **`Sidebar.jsx`**: Navegación lateral izquierda.
    *   **`Header.jsx`**: Barra superior (Búsqueda global, Perfil, Notificaciones).
*   **Páginas (Views)**:
    *   **`DashboardView.jsx`**: Vista general (KPI Cards, Gráficos base, Client Handovers).
    *   **`SystemLogsView.jsx`**: Tabla de eventos del sistema con filtros de severidad.
    *   **`CalendarView.jsx`**: Grilla interactiva de agenda y operaciones diarias.
    *   **`InboxChatView.jsx`**: Interfaz de 3 columnas (Lista de usuarios, Hilo de chat, Client Intelligence).
*   **Componentes Reutilizables (UI)**:
    *   `MetricCard.jsx`: Tarjetas de KPI.
    *   `DataTable.jsx`: Módulo de tablas genérico.
    *   `Badge.jsx`: Etiquetas de estado (Error, Info, Warning).
    *   `Button.jsx`, `Input.jsx`: Controles base uniformes.

## 3. Estrategia de Estilos (Split-Theme / Tema Híbrido)
Cumpliendo con la directriz del CEO, la aplicación usará un contraste dramático:

*   **Cascarón (Shell - Modo Dark Estricto):**
    *   *Sidebar, Header y Fondo Global (Body/Layout):* `bg-slate-950` o `bg-zinc-950`.
    *   *Textos del Shell:* `text-emerald-500` para acentos, `text-slate-400` para secundarios, `text-white` para títulos principales.
    *   *Bordes divisorios:* `border-slate-800`.
*   **Áreas de Trabajo (Contenedores Luminosos - High Contrast):**
    *   *Fondos principales (ej. Columna central de Chat, Tarjetas KPI, Contenedor de Tablas):* `bg-white` o `bg-slate-50`.
    *   *Textos de contenido:* `text-slate-900` para títulos/datos, `text-slate-600` para descripciones.
    *   *Elevación:* `shadow-md` o `shadow-lg` combinado con `border border-slate-200` para que el módulo blanco "flote" sobre el fondo oscuro.

## 4. Plan de Ejecución
Al recibir la orden exacta de **"Aprobado. Procede a la ejecución"**, ejecutaré secuencialmente los siguientes pasos:

1.  **Inicialización:** Ejecutar `npx create-vite@latest . --template react-ts` (o versión JS según convenga) de forma no interactiva.
2.  **Dependencias:** Instalar TailwindCSS (y sus dependencias peer), `react-router-dom` y `lucide-react`.
3.  **Configuración:** Configurar `tailwind.config.js` y el archivo `index.css` global.
4.  **Estructura de Carpetas:** Crear directorios `src/components`, `src/pages`, `src/layouts`.
5.  **Construcción del Cascarón:** Implementar `AppLayout`, `Sidebar` y `Header`.
6.  **Construcción de Vistas:** Traducir el código HTML de `dasboardmuestra.txt` a los componentes React correspondientes (`DashboardView`, `SystemLogsView`, `CalendarView`, `InboxChatView`), inyectando la nueva paleta de colores del *Split-Theme*.
7.  **Revisión Final:** Asegurar que el layout funcione, sea responsivo y cumpla la regla de contraste estricta.
