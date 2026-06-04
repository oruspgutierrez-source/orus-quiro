# Spec 27: Integración de Logs de Agente, Intervenciones y Nuevas Tablas en Supabase

## 1. Objetivo
Establecer el plan técnico para desacoplar y reemplazar las capas de datos simulados (mocks) del frontend del **Orus Command Center** por flujos de base de datos en tiempo real de **Supabase**. Además, se propone la creación de estructuras para auditar las intervenciones humanas y registrar la telemetría detallada del agente inteligente (como logs de error e interacciones críticas).

---

## 🚦 Estado de Tareas (Task Board)

| ID | Tarea | Estado | Notas |
|----|-------|--------|-------|
| 1 | Definición de Nueva Tabla de Intervenciones | 📋 PENDIENTE | Crear estructura de base de datos para auditoría de handovers. |
| 2 | Endpoint de Logs Reales en Backend (`GET /api/logs`) | 📋 PENDIENTE | Implementar paginación y filtros para la tabla `orus_logs`. |
| 3 | Integración del Frontend de Logs (`SystemLogsView`) | 📋 PENDIENTE | Reemplazar array `logs` estático por peticiones al backend. |
| 4 | Conexión Real de Chats Activos y Handovers (`InboxChatView`) | 📋 PENDIENTE | Usar real-time para suscripción a solicitudes de intervención humana. |
| 5 | Automatización de Logs en el Core del Agente | 📋 PENDIENTE | Asegurar que los errores críticos en la lógica del bot se escriban en `orus_logs`. |

---

## 2. Diseño de Base de Datos (Supabase)

Actualmente existen `orus_users` (con `session_mode`) y `orus_logs`. Para registrar y visualizar de forma óptima el rendimiento de la IA y el equipo humano, se proponen las siguientes estructuras:

### 2.1 Nueva Tabla: `orus_agent_interventions`
Permite auditar cuándo el bot transfirió la conversación a un humano, cuánto tardó en resolverse y la causa de la transferencia.

```sql
CREATE TABLE public.orus_agent_interventions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.orus_users(id) ON DELETE CASCADE,
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    resolved_at TIMESTAMP WITH TIME ZONE,
    reason TEXT, -- Ej: "Usuario frustrado", "Pregunta compleja sobre pagos", "Forzado por admin"
    resolved_by TEXT DEFAULT 'admin',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Habilitar RLS
ALTER TABLE public.orus_agent_interventions ENABLE ROW LEVEL SECURITY;
```

### 2.2 Políticas de Seguridad (RLS)
Para proteger la integridad de los logs y registros de intervención:
* El rol `service_role` (utilizado por el backend de FastAPI) posee acceso completo.
* Las lecturas directas desde el frontend (si usa la API de Supabase) deben estar restringidas al token de autenticación del administrador.

---

## 3. Especificación de la API (FastAPI)

Para nutrir al Dashboard de forma segura y centralizada, se extenderá el backend con los siguientes endpoints en `api/routes/dashboard.py` y `api/routes/metrics.py`:

### 3.1 Logs del Sistema (`GET /api/logs`)
Expone los eventos registrados por la aplicación.

* **Parámetros de consulta (Query params):**
  * `severity`: `ERROR` | `WARNING` | `INFO` (opcional)
  * `page`: int (default: 1)
  * `limit`: int (default: 50)
  * `search`: str (opcional, busca en `error_message` o `event_type`)

* **Respuesta esperada:**
  ```json
  {
    "data": [
      {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "created_at": "2026-06-04T12:00:00Z",
        "severity": "ERROR",
        "event_type": "META_API_TIMEOUT",
        "error_message": "Timeout connecting to WhatsApp gateway",
        "stack_trace": "..."
      }
    ],
    "total": 1245,
    "page": 1,
    "pages": 25
  }
  ```

### 3.2 Registro de Intervención (`POST /api/interventions/request`)
Permite que el agente o el webhook de mensajes marque la necesidad de intervención.

* **Payload:**
  ```json
  {
    "user_id": "uuid-del-usuario",
    "reason": "Frustración detectada"
  }
  ```

---

## 4. Integración en el Frontend (Vite + React)

### 4.1 Pantalla de Logs (`SystemLogsView.jsx`)
Se reemplazará el hook estático para consumir el nuevo endpoint de logs:

```javascript
useEffect(() => {
  async function fetchLogs() {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/logs?page=${page}&severity=${severityFilter}`, {
        headers: { 'Authorization': `Bearer ${API_KEY}` }
      });
      const res = await response.json();
      setLogsData(res.data);
      setTotalPages(res.pages);
    } catch (err) {
      console.error("Error al obtener logs:", err);
    } finally {
      setLoading(false);
    }
  }
  fetchLogs();
}, [page, severityFilter]);
```

### 4.2 Dashboard y Inbox en Tiempo Real
Mediante los canales de suscripción de Supabase (`supabase.channel`), el frontend escuchará en tiempo real cuando se cree un registro en `orus_agent_interventions` o cuando `orus_users.session_mode` cambie a `HUMAN`, disparando notificaciones visuales y auditivas en el Command Center.

---

> [!TIP]
> **Optimización de Almacenamiento:** Debido a que el backend de producción registra gran cantidad de eventos, implementaremos un cron-job mensual en PostgreSQL para purgar logs de severidad `INFO` con más de 15 días de antigüedad, reteniendo únicamente los logs de tipo `ERROR` y `WARNING` durante 90 días.
