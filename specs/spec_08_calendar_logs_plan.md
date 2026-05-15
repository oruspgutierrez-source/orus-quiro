# Spec 08: Integración Modular (Calendar, Logs y Métricas)

Este documento contiene el plan de arquitectura para extender las capacidades del ecosistema Orus, preparado bajo el protocolo **REPORT_ONLY**.

---

## 🚦 Estado de Tareas (Task Board)

| ID | Tarea | Estado | Notas |
|----|-------|--------|-------|
| 1 | Evolución de Base de Datos | ✅ COMPLETO | `orus_users` y `orus_logs` validados. |
| 2 | Infraestructura Google Calendar | ✅ COMPLETO | `credentials.json` y `calendar_client.py` operativos. |
| 3 | Agente con Superpoderes (FC) | 🟡 EN CURSO | Requiere refactorizar `gemini_client.py`. |
| 4 | API de Métricas para Dashboard | 📋 PENDIENTE | Pendiente creación de `api/routes/metrics.py`. |
| 5 | Prueba E2E WhatsApp -> Calendar | 📋 PENDIENTE | Requiere completar Task 3. |

---

## 1. Evolución de Base de Datos (Supabase)

### 1.1 Estado de la Tabla `orus_users`
La tabla ya cuenta con las columnas:
- `payment_status`
- `appointment_date`
- `total_spent`

### 1.2 Estado de la Tabla `orus_logs`
Ya implementada con soporte para telemetría profunda (`error_message`, `stack_trace`, `severity`, `event_type`).

---

## 2. Integración de Google Calendar (Function Calling)

### 2.1 Herramientas (Tools) de Gemini
El cliente `api/services/calendar_client.py` ya expone:
1. `check_free_slots(start_date, end_date)`
2. `book_appointment(phone_number, date_time, name)`

### 2.2 Refactorización Pendiente (`gemini_client.py`)
Para que Orus use estas herramientas, se debe implementar el bucle de despacho:
- Configurar `tools` en `GenerateContentConfig`.
- Detectar `function_call` en la respuesta de Gemini.
- Ejecutar la función localmente.
- Enviar el resultado a Gemini para que genere la respuesta final al usuario.

---

## 3. Lógica de Métricas (Dashboard API)

### 3.1 Nuevo Endpoint: `GET /api/metrics/summary`
Objetivo: Proveer datos agregados para los widgets del dashboard.
- **Distribución de Citas:** Basado en `appointment_date`.
- **Salud del Sistema:** Basado en la frecuencia de errores en `orus_logs`.
- **Efectividad del Bot:** Proporción de `ai_managed` vs `human_managed`.

---

## 4. Alerta de Seguridad (Prioridad Alta)
Se debe habilitar **RLS (Row Level Security)** en Supabase. 
*Propuesta:* Crear políticas que permitan al `service_role` (usado por el backend) acceso total, mientras que el acceso anónimo sea nulo o restringido a lectura selectiva.
