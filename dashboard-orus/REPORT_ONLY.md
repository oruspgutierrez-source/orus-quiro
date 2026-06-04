# Informe Estratégico: Integración del Calendario en el Dashboard Orus

## 1. Estrategia de Sincronización (Lectura y Enriquecimiento)
Tal como lo mencionas, recrear toda la lógica de agendamiento, reprogramación y cancelación en el Dashboard es reinventar la rueda (y un foco de bugs innecesario). La mejor práctica para un Command Center operativo es el **Read-Only Inteligente**:

*   **Motor Principal:** Sigues usando tu aplicación de calendario actual (por ejemplo, Google Calendar) para mover, crear o cancelar citas.
*   **Reflejo Inmediato:** Conectamos el backend de Orus a la API de Google Calendar usando Webhooks (Push Notifications). Cuando cancelas o mueves una cita en tu celular, Google le avisa al backend, y el Dashboard se actualiza en tiempo real sin recargar la página.

## 2. ¿Cómo enriquecer la experiencia sin duplicar funciones?
Si el calendario solo es de lectura, su valor real en el Dashboard debe ser **dar contexto profundo que Google Calendar no tiene**. Aquí te propongo 3 funcionalidades clave que aprovecharán todo el ecosistema de Orus (IA + WhatsApp + Base de Datos):

### A. Ficha Biosemiótica Automática (Contexto Pre-Cita)
Cuando hagas clic en un evento del calendario en el Dashboard, no solo verás la hora. El sistema buscará el número de WhatsApp asociado a esa cita y desplegará en un panel lateral (estilo *Glassmorphism* oscuro) el **perfil biosemiótico/astrológico** del usuario y sus datos de onboarding. Sabrás exactamente quién es y cómo abordarlo antes de que empiece la sesión.

### B. Notas Clínicas / Bitácora de Sesión
Podemos crear una tabla en Supabase llamada `session_notes` que se enlace al ID del evento del calendario. 
*   **Uso:** Terminas la cita, abres el evento en el Dashboard y dejas una nota rápida sobre el progreso del paciente o tareas pendientes. 
*   **Ventaja:** Estas notas son estrictamente privadas de Orus y no ensucian la descripción pública del evento en tu Google Calendar.

### C. "Briefing" de IA (Resumen de Chat)
Aprovechando que ya tenemos el historial de chat de WhatsApp en Supabase y a Gemini configurado, podemos añadir un botón de **"Generar Briefing"**. 
*   **Qué hace:** La IA lee las conversaciones de WhatsApp de los últimos 7 días con ese paciente y te da un resumen de 3 viñetas sobre su estado emocional o las dudas que tuvo antes de la cita. 

### D. Indicadores de Confirmación (Estado de Asistencia)
Podemos añadir un pequeño indicador visual (un punto verde o rojo) en la tarjeta de la cita dentro del Dashboard, que cambie automáticamente si el bot de WhatsApp logró que el usuario confirmara su asistencia a la cita 24 horas antes.

## 3. Plan de Acción (Cómo implementarlo)
1.  **Conexión Base:** Crear credenciales de Google Cloud (Service Account) para que el backend de Python pueda leer los eventos de un calendario específico de Orus.
2.  **API de Calendario (Backend):** Crear endpoints `GET /api/calendar` y un webhook para recibir actualizaciones de Google.
3.  **UI del Dashboard:** Conectar los datos reales al diseño actual (`CalendarView.jsx`), añadiendo el panel lateral para las **Notas** y el **Contexto del Paciente**.
4.  **Enlace de Datos:** Modificar la lógica para que al crear la cita, se añada un metadato (ej. el número de teléfono) que permita cruzar la cita de Google con el usuario en Supabase.

---
**Conclusión:**
Tu visión es 100% correcta. Al delegar la gestión del tiempo (agendar/cancelar) a una app experta y usar el Dashboard de Orus exclusivamente para **Contexto, Inteligencia Artificial y Bitácora**, mantienes la arquitectura limpia y elevas la herramienta a un verdadero asistente profesional personalizado. ¿Te parece bien si comenzamos configurando la conexión de solo lectura con tu proveedor de calendario?