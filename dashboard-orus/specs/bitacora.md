# Bitácora de Desarrollo — Orus Command Center
**Proyecto:** `dashboard-orus`  
**Host:** `http://localhost:5173`  
**Stack:** React + Vite (JS) + Tailwind CSS v3.4.3  
**Fecha:** 25 de abril de 2026  
**Rol:** Antigravity — Ingeniero Frontend Senior  

---

## Estado General del Proyecto

### Arquitectura de Layout

```
App (React Router)
├── AppLayout.jsx          → Layout principal: Sidebar + Header + <Outlet>
│   ├── Sidebar (nav)      → w-64, bg-slate-950, elevación con sombra lateral
│   └── Header (header)    → h-16, sticky, degradado oscuro con franja de marca
└── Pages (via Outlet)
    ├── DashboardView.jsx
    ├── InboxChatView.jsx
    ├── CalendarView.jsx
    └── SystemLogsView.jsx
```

---

## Cambios Realizados — Sesión 25/04/2026

### 1. Header — Fondo y Degradado

**Objetivo:** Que el header se integre visualmente con la sidebar sin una línea de corte.

- Se eliminó `border-r` de la sidebar para borrar la división entre ambas secciones.
- Se aplicó un `linear-gradient(to right)` en el header que parte del color de la sidebar (`#33373d`) y se funde al negro carbón (`#0c0e12`).
- Degradado final configurado en:
  `#33373d 0% → #33373d 25% → #0c0e12 50% → #0c0e12f2 100%`
- Se añadió `overflow-hidden` al header para evitar que elementos internos causen overflow en el layout.
- Se añadió una línea de brillo superior (`h-px via-white/[0.08]`) para el efecto de bisel 3D.
- Sombra inferior: `shadow-[0_4px_20px_rgba(0,0,0,0.4)]`.
- La sidebar recibió sombra lateral derecha: `shadow-[10px_0_30px_rgba(0,0,0,0.5)]` para que "flote" sobre el header.

### 2. Header — Barra de Búsqueda (Crystal / Frosted Glass)

- Fondo: `bg-white/[0.06]` con `backdrop-blur-md`.
- Borde: `border-white/[0.1]` con brillo interno superior.
- Al hacer focus: glow esmeralda `rgba(16,185,129,0.15)` y borde `emerald-500/50`.
- Ícono lupa (`<Search>`): se añadió `z-10` para que no sea ocultado por el backdrop-blur del input.

### 3. Header — Branding: "Camino del Escultor"

- Se renombró "Orus Command Center" → **"Camino del Escultor"** con estilo cursivo fino (`font-light italic text-sm tracking-widest text-emerald-400`).
- Se renombró "Orus CC" → **"Orus-quiro"** en el logo de la sidebar.
- El texto está montado sobre una **franja oscura con degradado** que nace desde el borde de la sidebar (posición absoluta `inset-y-0 left-0 w-96`) y se desvanece hacia la derecha (`from-[#050608] via-[#050608]/80 to-transparent`).
- La franja es `pointer-events-none` y `position: absolute`, por lo que **no afecta al layout ni genera overflow**.

### 4. Layout Fix — Eliminación de Scrollbars Fantasmas

**Problema:** Las barras de scroll aparecían en todos los módulos y crecían progresivamente.

**Causa raíz:** El `<main>` del `AppLayout` tenía `overflow-auto`, y la mandala de 1200px expandía el contenido interno más allá del viewport.

**Solución:**
- Se cambió `<main>` de `overflow-auto` a `overflow-hidden` en `AppLayout.jsx`.
- Cada módulo de página maneja su propio scroll con `overflow-auto` en su div raíz.

### 5. Módulos — Limpieza de Fondos e Imágenes

**Problema:** Los módulos tenían una mandala de 1200px como fondo y paddings excesivos.

**Cambios aplicados en los 4 módulos:**
- Eliminadas las imágenes `<img src="/mandala.png">` de: `DashboardView`, `SystemLogsView`, `CalendarView`.
- Eliminada la imagen `fondo-area-de-trabajo.jpg` de `InboxChatView`.
- Padding reducido de `p-8` / `p-6` → `p-4` en todos los módulos.
- Gap reducido de `gap-6` → `gap-4`.

### 6. InboxChatView — Panel "Inteligencia del Cliente"

**Problema:** La caja "Total Gastado" aparecía entrecortada fuera del área visible.

**Solución:**
- El contenedor del panel pasó a usar `flex-1 overflow-y-auto no-scrollbar`, permitiendo scroll interno sin cortar contenido.
- Avatar reducido de `w-24` → `w-20` para liberar espacio vertical.
- "Total Gastado": padding reducido a `py-2 px-4`, texto de `text-2xl` → `text-xl`.
- Espaciados generales reducidos de `space-y-5` → `space-y-3` y `mb-6` → `mb-4`.

### 7. Refinamiento de Estilos: Dark Mode Selectivo y Fondo Radial

**Objetivo:** Crear una jerarquía visual con foco intenso en datos críticos mediante un negro profundo (`zinc-900` / `black`), manteniendo la estructura general luminosa.

**Cambios aplicados:**
- **Fondo de Módulos (Lienzo):** Se implementó un degradado radial Gaussiano que crea una esfera de luz blanca en el centro del espacio de trabajo y se difumina hacia gris suave en los bordes (`radial-gradient(circle at 50% 50%, #ffffff... )`).
- **Dark Card (Zinc/Black):** Se creó un nuevo componente visual `darkCard` que utiliza la escala de grises puros `zinc` y fondos casi negros para maximizar el contraste de la tipografía.
- **Aplicación Selectiva:**
  - `InboxChatView`: Aplicado solo en la tarjeta central de chat (laterales en slate).
  - `CalendarView`: Aplicado en el panel lateral derecho (Citas y Ubicación).
  - `SystemLogsView`: Aplicado en la tabla de registros principal (header en slate).
  - `DashboardView`: Aplicado en la tarjeta de gráfico "Actividad de Usuarios Esta Semana".

---

## Estado Actual de Archivos Clave

### `src/layouts/AppLayout.jsx`

| Elemento | Estado |
|---|---|
| Sidebar | `bg-slate-950`, sin `border-r`, con sombra lateral derecha |
| Header | `h-16 sticky`, degradado `#33373d → #0c0e12`, `overflow-hidden` |
| Franja marca | Absoluta, oscura, desvanecida hacia el centro del header |
| Barra de búsqueda | Crystal glass, lupa visible con `z-10` |
| `<main>` | `overflow-hidden` — el scroll es delegado a cada página |

### `src/pages/DashboardView.jsx`
- Fondo: Degradado radial gaussiano (blanco a gris claro).
- `p-4 space-y-4`.
- Tarjetas generales KPI en `glassCard` (slate).
- Gráfico de barras interactivo en `darkCard` (zinc/negro).

### `src/pages/SystemLogsView.jsx`
- Fondo: Degradado radial gaussiano.
- Header de filtros en `glassCard` (slate).
- Tabla principal de eventos en `darkCard` (zinc) con severities.

### `src/pages/CalendarView.jsx`
- Fondo: Degradado radial gaussiano.
- Calendario principal en `glassCard` (slate).
- Panel lateral ("Próximas Citas" y "Ubicación") en `darkCard` (zinc).

### `src/pages/InboxChatView.jsx`
- Fondo: Degradado radial gaussiano.
- 3 columnas: Laterales en `glassCard` (slate) | Chat Central en `darkCard` (zinc).
- Panel derecho scrollable internamente (`overflow-y-auto no-scrollbar`).

---

## Sistema de Design Tokens

### Paleta Principal

| Token | Valor | Uso |
|---|---|---|
| Brand Accent | `emerald-400` (#34d399) | Links activos, íconos, CTAs |
| Sidebar BG | `slate-950` (#020617) | Barra lateral |
| Fondo Lienzo | `radial-gradient(...)` | Esfera de luz gaussiana central |
| Glass Card BG | `from-slate-800 to-slate-950`| Tarjetas estructurales (Slate) |
| Dark Card BG | `from-zinc-900 to-black` | Áreas de datos críticos (Zinc) |

### Estilos de Tarjeta Base

**1. Glass Card (Estructural / Navegación):**
```css
relative overflow-hidden rounded-2xl
bg-gradient-to-br from-slate-800 to-slate-950
border border-slate-700/50
shadow-[0_20px_40px_rgba(0,0,0,0.4),inset_0_1px_1px_rgba(255,255,255,0.15)]
backdrop-blur-md
```

**2. Dark Card (Foco en Datos / Contraste):**
```css
relative overflow-hidden rounded-2xl
bg-gradient-to-br from-zinc-900 to-black
border border-zinc-700/50
shadow-[0_20px_40px_rgba(0,0,0,0.4),inset_0_1px_1px_rgba(255,255,255,0.15)]
backdrop-blur-md
```

---

## Próximos Pasos Sugeridos

1. **Integración de Datos:** Conectar `InboxChatView` y `DashboardView` con la API FastAPI.
2. **State Management:** Implementar `Context API` para sesión de usuario y cambio de vistas.
3. **Modales / Overlays:** Crear componentes de modal que respeten el sistema de cristal 3D.
4. **Refinamiento de la franja de marca:** Evaluar si se le añade una fina línea superior/inferior.
5. **Responsive:** Adaptar la sidebar a modo colapsado para pantallas < 1280px.
6. **Performance:** Evaluar `React.memo` en el grid del calendario si el número de eventos crece.

---

*Bitácora generada por Antigravity — Ingeniero Frontend Senior*
*Orus Command Center © 2026*
