# Spec 48: Reporte de Conversión, Embudo de Flujo y Clientes Estancados

Este documento detalla la especificación técnica y de diseño para el reporte de conversión y el embudo de flujo de clientes en tiempo real implementado en el panel de administración (Orus Dashboard).

---

## 1. Contexto y Objetivos

Con la base de datos real de Supabase conectada, se requiere proveer al administrador de una vista analítica accionable sobre el proceso de conversión de los usuarios desde que inician el chat hasta que agendan su sesión final.

Los objetivos de esta funcionalidad son:
1. **Visualizar el Embudo (Funnel) de 4 Pasos**:
   - **Paso 1: Leads Totales**: Total de clientes registrados en `orus_users`.
   - **Paso 2: Diagnóstico Biométrico**: Usuarios que han avanzado a fase 2 (`PHASE_2_AUDIO`, `PHASE_2_IMAGE` o ya pagaron).
   - **Paso 3: Pago Confirmado**: Usuarios con `payment_status` igual a `paid` o `pagado`.
   - **Paso 4: Cita Agendada**: Usuarios con pago confirmado que ya tienen una fecha en `appointment_date`.
2. **Presentar Tasas de Conversión Clave**:
   - **Tasa de Conversión General**: Leads Totales que completaron el Pago.
   - **Tasa de Agendamiento**: Pagos confirmados que reservaron cita.
   - **Tasa de Atención Humana**: Porcentaje de clientes en modo `HUMAN` respecto a la base total.
3. **Listado de Clientes Estancados (Abandono)**:
   - Identificar a todos los usuarios que iniciaron el proceso pero no lo completaron (sin pago).
   - Indicar la etapa precisa donde quedaron estancados (Diagnóstico Inicial, Evaluación Biométrica, Atención Humana, Proceso de Reserva).
   - Proveer un enlace directo para abrir el chat del cliente y reactivarlo manualmente.

---

## 2. Detalles Técnicos e Implementación

### A. Cálculo de Estados y Filtros en el Frontend (`DashboardView.jsx`)
Al recuperar los usuarios en `fetchDashboardData`, calculamos dinámicamente cada paso del funnel en memoria:
```javascript
const phase1 = allUsers.filter(u => u.session_mode === 'AI' && u.payment_status !== 'paid' && u.payment_status !== 'pagado' && !u.appointment_date).length;
const phase2 = allUsers.filter(u => u.session_mode === 'PHASE_2_AUDIO' || u.session_mode === 'PHASE_2_IMAGE' || u.payment_status === 'paid' || u.payment_status === 'pagado').length;
const paid = allUsers.filter(u => u.payment_status === 'paid' || u.payment_status === 'pagado').length;
const booked = allUsers.filter(u => (u.payment_status === 'paid' || u.payment_status === 'pagado') && u.appointment_date).length;
const human = allUsers.filter(u => u.session_mode === 'HUMAN').length;
```

### B. Mapeo y Clasificación de Etapa Abandonada
Para la lista de clientes estancados, analizamos el `session_mode` del registro:
- Si es `AI` (y no ha pagado) -> **Diagnóstico Inicial**
- Si es `PHASE_2_AUDIO` o `PHASE_2_IMAGE` -> **Evaluación Biométrica**
- Si es `HUMAN` -> **Atención Humana**
- Si empieza con `BOOKING_` -> **Proceso de Reserva**

### C. Redirección Proactiva al Chat
El administrador puede hacer clic en "Abrir Chat" dentro de la tabla del modal. Esto cierra el modal y redirige a la ruta `/chat` pasando el identificador del usuario como parámetro de búsqueda (`userId`), abriendo su conversación al instante para intervención directa.

---

## 3. Diseño Visual y UX

El modal mantiene la estética ultra-premium del Dashboard:
- **Fondo de Cristal Oscuro**: `bg-black/75 backdrop-blur-md` para el overlay de pantalla completa.
- **Degradado Sofisticado**: Caja contenedora con bordes redondeados `rounded-3xl` y degradado `from-slate-900 via-zinc-950 to-slate-950` con borde sutil `border-slate-800/80`.
- **Embudo de Progreso Proporcional**: Barras de progreso de color codificado (gris, ámbar, esmeralda, azul) cuyas anchuras cambian de forma fluida usando transiciones CSS y anchos dinámicos en base al porcentaje calculado.
- **Scroll Optimizado**: Soporte para scroll interno con barras de navegación personalizadas (`scrollbar-thin scrollbar-thumb-zinc-700`) para garantizar legibilidad en pantallas portátiles.
