# Spec 44: Real-Time Dashboard Activity Metrics Integration

Este documento describe la especificación técnica y la implementación realizada para conectar la gráfica de **"Actividad de Usuarios Esta Semana"** con los datos reales en tiempo real desde la base de datos de Supabase.

---

## 1. Contexto y Objetivos

El panel de administración (Orus Dashboard) contaba con un gráfico de barras que mostraba la actividad semanal (`Actividad de Usuarios Esta Semana`) utilizando valores estáticos tipo mockup. 
Los objetivos principales de esta actualización son:
1. **Conexión Real:** Sustituir los datos mockup por datos reales consultados dinámicamente desde la tabla `orus_messages`.
2. **Cálculo de Altura Dinámico:** Calcular el porcentaje de altura (`h`) de las barras de forma proporcional y adaptativa al día de mayor actividad de la semana actual.
3. **Resaltado Dinámico:** Identificar y resaltar visualmente la barra correspondiente al día de hoy en lugar de tener un resaltado estático fijo en el día miércoles.
4. **Suscripción Real-time:** Escuchar inserciones de nuevos mensajes para refrescar la gráfica al instante sin necesidad de recargar la página.

---

## 2. Detalles de Implementación

### A. Cálculo del Rango de la Semana Actual
Calculamos la fecha y hora de inicio de la semana actual (Lunes a las 00:00) en tiempo local:
```javascript
const now = new Date();
const day = now.getDay(); // 0: Domingo, 1: Lunes, etc.
const diffToMonday = day === 0 ? -6 : 1 - day; // Determinar desfase al lunes
const monday = new Date(now);
monday.setDate(now.getDate() + diffToMonday);
monday.setHours(0, 0, 0, 0);
```

### B. Consulta y Agrupamiento
Consultamos la tabla `orus_messages` filtrando por el campo `created_at` desde el lunes calculado:
```javascript
const { data: weekMessages } = await supabase
  .from('orus_messages')
  .select('created_at')
  .gte('created_at', monday.toISOString());

const counts = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 0: 0 };
if (weekMessages) {
  weekMessages.forEach(msg => {
    const date = new Date(msg.created_at);
    const msgDay = date.getDay();
    counts[msgDay] = (counts[msgDay] || 0) + 1;
  });
}
```

### C. Normalización y Actualización de Estado
Para que la interfaz escale correctamente independientemente del volumen de mensajes, determinamos el máximo valor registrado en un único día (`maxVal`) y asignamos la proporción de la altura sobre el 100%:
```javascript
const maxVal = Math.max(...Object.values(counts), 1);
const updatedBars = [
  { label: 'Lun', val: counts[1], h: Math.round((counts[1] / maxVal) * 100) },
  { label: 'Mar', val: counts[2], h: Math.round((counts[2] / maxVal) * 100) },
  { label: 'Mié', val: counts[3], h: Math.round((counts[3] / maxVal) * 100) },
  { label: 'Jue', val: counts[4], h: Math.round((counts[4] / maxVal) * 100) },
  { label: 'Vie', val: counts[5], h: Math.round((counts[5] / maxVal) * 100) },
  { label: 'Sáb', val: counts[6], h: Math.round((counts[6] / maxVal) * 100) },
  { label: 'Dom', val: counts[0], h: Math.round((counts[0] / maxVal) * 100) },
];
setBars(updatedBars);
```

### D. Resaltado de Día de la Semana Dinámico
En lugar de resaltar estáticamente el día Miércoles (índice 2), definimos el índice correspondiente al día actual de la semana en la UI:
```javascript
const currentDay = new Date().getDay();
const currentDayIdx = currentDay === 0 ? 6 : currentDay - 1;
```
En la plantilla, la clase de resaltado de gradiente esmeralda ahora se aplica con la condición: `i === currentDayIdx`.

### E. Suscripciones Real-time Multicanal
Modificamos el bloque `useEffect` para escuchar tanto cambios en `orus_users` como nuevas inserciones de mensajes en `orus_messages`:
```javascript
const channel = supabase
  .channel('dashboard-realtime')
  .on('postgres_changes', { event: '*', schema: 'public', table: 'orus_users' }, () => {
    fetchDashboardData();
  })
  .on('postgres_changes', { event: 'insert', schema: 'public', table: 'orus_messages' }, () => {
    fetchDashboardData();
  })
  .subscribe();

return () => {
  supabase.removeChannel(channel);
};
```

---

## 3. Pruebas y Validación

1. **Compilación de Producción exitosa:** Se ejecutó `npm run build` en el directorio de `dashboard-orus` completándose sin errores de JSX o tipos.
2. **Adaptabilidad de UI:** Los tooltips fueron actualizados para mostrar `{b.val} mensajes` reflejando de forma precisa la métrica de interacciones procesadas.
3. **Remoción de Etiquetas Demo:** Se eliminó la etiqueta "(Demo)" del título de la sección para dar un acabado 100% profesional e integrado.
