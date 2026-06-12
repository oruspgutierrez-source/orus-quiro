# Spec 48: Reporte de Conversión, Embudo de Flujo y Clientes Estancados

Este documento detalla la especificación técnica y de diseño para el reporte de conversión y el embudo de flujo de clientes en tiempo real implementado en el panel de administración (Orus Dashboard).

---

## 1. Contexto y Objetivos

Con la base de datos real de Supabase conectada, se requiere proveer al administrador de una vista analítica accionable sobre el proceso de conversión de los usuarios desde que inician el chat hasta que agendan su sesión final.

Los objetivos de esta funcionalidad son:
1. **Visualizar el Embudo (Funnel) de 5 Pasos**:
   - **Paso 1: Leads Totales (Chat Iniciado)**: Total de clientes registrados en `orus_users`.
   - **Paso 2: Audio Explicativo Enviado**: Usuarios que han avanzado a la fase de audio (`PHASE_2_AUDIO`, `PHASE_2_IMAGE` o ya pagaron).
   - **Paso 3: Pago Confirmado**: Usuarios con `payment_status` igual a `paid` o `pagado`.
   - **Paso 4: Cita Agendada**: Usuarios con pago confirmado que ya tienen una fecha en `appointment_date`.
   - **Paso 5: Evaluación Biométrica Completada**: Usuarios que cargaron sus datos al bucket y completaron el formulario (registrados en `evaluaciones_completas`).
2. **Presentar Tasas de Conversión Clave**:
   - **Tasa de Conversión General**: Leads Totales que completaron el Pago.
   - **Tasa de Agendamiento**: Pagos confirmados que reservaron cita.
   - **Tasa Biométrica**: Citas agendadas que completaron la evaluación biométrica (cruce con la tabla `evaluaciones_completas`).
   - **Tasa de Atención Humana**: Porcentaje de clientes en modo `HUMAN` respecto a la base total.
3. **Listado de Clientes Estancados (Abandono)**:
   - Identificar a todos los usuarios que iniciaron el proceso pero no completaron su evaluación biométrica final.
   - Indicar la etapa precisa donde quedaron estancados:
     - **Diagnóstico Inicial**: Usuarios en modo `AI` sin pago ni cita.
     - **Audio Explicativo**: Usuarios en modo `PHASE_2_AUDIO` o `PHASE_2_IMAGE` sin pago.
     - **Atención Humana**: Usuarios en modo `HUMAN`.
     - **Proceso de Reserva**: Usuarios con pago confirmado pero sin cita agendada.
     - **Evaluación Biométrica**: Usuarios con pago y cita agendada pero sin completar el formulario biométrico y las fotos.
   - Proveer un enlace directo para abrir el chat del cliente y reactivarlo manualmente.

---

## 2. Detalles Técnicos e Implementación

### A. Cálculo de Estados y Filtros en el Frontend (`DashboardView.jsx`)
Al recuperar los usuarios en `fetchDashboardData`, consultamos también `evaluaciones_completas` y realizamos un cruce de teléfonos en memoria:
```javascript
const cleanPhone = (p) => p ? p.trim().replace('@s.whatsapp.net', '') : '';
const completedEvalPhones = new Set((allEvaluations || []).map(ev => cleanPhone(ev.wa_id)));

const phase1 = allUsers.filter(u => u.session_mode === 'AI' && u.payment_status !== 'paid' && u.payment_status !== 'pagado' && !u.appointment_date).length;
const phase2 = allUsers.filter(u => u.session_mode === 'PHASE_2_AUDIO' || u.session_mode === 'PHASE_2_IMAGE' || u.payment_status === 'paid' || u.payment_status === 'pagado').length;
const paid = allUsers.filter(u => u.payment_status === 'paid' || u.payment_status === 'pagado').length;
const booked = allUsers.filter(u => (u.payment_status === 'paid' || u.payment_status === 'pagado') && u.appointment_date).length;
const biometrics = allUsers.filter(u => completedEvalPhones.has(cleanPhone(u.phone_number))).length;
const human = allUsers.filter(u => u.session_mode === 'HUMAN').length;
```

### B. Mapeo y Clasificación de Etapa Abandonada
Para la lista de clientes estancados, se filtra a quienes no tienen su teléfono en `completedEvalPhones` y se clasifica según su progreso:
- Si ya tiene pago y cita -> **Evaluación Biométrica**
- Si ya tiene pago pero no cita -> **Proceso de Reserva**
- Si es `PHASE_2_AUDIO` o `PHASE_2_IMAGE` -> **Audio Explicativo**
- Si es `HUMAN` -> **Atención Humana**
- De lo contrario -> **Diagnóstico Inicial**

### C. Redirección Proactiva al Chat
El administrador puede hacer clic en "Abrir Chat" dentro de la tabla del modal. Esto cierra el modal y redirige a la ruta `/chat` pasando el identificador del usuario como parámetro de búsqueda (`userId`), abriendo su conversación al instante para intervención directa.

---

## 3. Diseño Visual y UX

El modal mantiene la estética ultra-premium del Dashboard:
- **Fondo de Cristal Oscuro**: `bg-black/75 backdrop-blur-md` para el overlay de pantalla completa.
- **Degradado Sofisticado**: Caja contenedora con bordes redondeados `rounded-3xl` y degradado `from-slate-900 via-zinc-950 to-slate-950` con borde sutil `border-slate-800/80`.
- **Embudo de Progreso Proporcional**: Barras de progreso de color codificado (gris, ámbar, esmeralda, azul) cuyas anchuras cambian de forma fluida usando transiciones CSS y anchos dinámicos en base al porcentaje calculado.
- **Scroll Optimizado**: Soporte para scroll interno con barras de navegación personalizadas (`scrollbar-thin scrollbar-thumb-zinc-700`) para garantizar legibilidad en pantallas portátiles.
