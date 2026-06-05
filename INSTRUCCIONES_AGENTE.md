# Instrucciones de Sesion para Agentes

**ESTE ARCHIVO DEBE SER LEIDO POR CUALQUIER AGENTE AL INICIAR UNA SESION.**

## 0. Protocolo de Comunicacion (LECTURA OBLIGATORIA ANTES DE RESPONDER)
> [!IMPORTANT]
> **Skill Activo:** `ultra-concise-chat`
> Antes de generar CUALQUIER respuesta en el chat, lee y aplica este protocolo estrictamente:
> - Si la informacion ya fue guardada en un artefacto o `.md` -> **NO la repitas en el chat.**
> - Task completada -> solo escribe: *"Task #X completada con exito."* o *"Ya complete la tarea."*
> - Si el usuario pide un ajuste -> NO repitas lo que pidió ni le expliques el proceso. Solo di que está completado, EXCEPTO si tomaste una decisión técnica extra que necesite saber.
> - Error encontrado -> solo escribe: *"Error registrado con su correccion en [archivo]."*
> - **Cero texto de relleno. Cero explicaciones de proceso. Solo el resultado.**

---

## 1. CONTEXTO ACTUAL Y PLAN MAESTRO

> [!IMPORTANT]
> **Último Estado:** Infraestructura en Producción (VPS y Vercel).
> - **El flujo completo ya está cargado y operando en la VPS.**
> - **Backend y Dashboard** están alojados en la VPS mediante EasyPanel.
> - **App de Recolección de Datos Biométricos** está alojada en Vercel. El link de esta app se utiliza en el flujo de WhatsApp y se envía por el chat.
> - La integración de Google Calendar, Inbox Chat (Handover manual) y System Logs ya operan contra Supabase y la API de producción.
>
> **Pendientes próxima sesión:**
> - Pruebas en el entorno de producción (ej. el usuario enviando mensajes desde un celular alterno para verificar todo el flujo y recolección biométrica).
> - Corrección de cualquier bug detectado en la VPS o Dashboard.

---

## 2. INFRAESTRUCTURA Y DESPLIEGUE (PRODUCCIÓN)

> [!IMPORTANT]
> **YA NO SE LEVANTAN SERVIDORES LOCALES (ni Uvicorn ni ngrok).** El agente ya no necesita iniciar la secuencia de comandos de terminal locales. Todo corre en la VPS y Vercel.

### Distribución de Servicios:
- **Backend (FastAPI)**: VPS (EasyPanel) -> `https://api.orusquiroterapia.online`
- **Dashboard (Vite/React)**: VPS (EasyPanel) -> `https://dashboard.orusquiroterapia.online`
- **Evolution API (WhatsApp)**: VPS (EasyPanel) -> `https://whatsapp.orusquiroterapia.online`
- **App de Datos Biométricos**: Vercel -> Link enviado dinámicamente al usuario por WhatsApp.

### Flujo de Actualización:
Para aplicar cambios en el código al Backend o Dashboard:
1. Hacer `git commit` y `git push` a la rama `main` de GitHub.
2. (El despliegue se actualiza desde EasyPanel al hacer Deploy de los últimos commits).

---

## 3. DIAGNOSTICO RAPIDO EN PRODUCCION

Dado que los servicios corren en la VPS, si el bot no responde, ejecutar:

```powershell
# Ver ultimos mensajes del usuario en Supabase
python -c "from dotenv import load_dotenv; load_dotenv(); from api.db.supabase_client import supabase; import json; m=supabase.table('orus_messages').select('role,content,created_at').order('created_at',desc=True).limit(5).execute(); [print(json.dumps(x)) for x in m.data]"
```

- Para ver logs internos de sistema, revisar en Supabase la tabla `orus_system_logs`.
- Para revisar errores críticos del servidor, es necesario consultar los logs del contenedor en EasyPanel.


---

## 4. RESET DE USUARIO DE PRUEBA

Para correr el flujo desde cero con el numero de prueba `553798433269`:

```python
from dotenv import load_dotenv; load_dotenv()
from api.db.supabase_client import supabase

jid = '553798433269@s.whatsapp.net'
u = supabase.table('orus_users').select('id').eq('phone_number', jid).execute()
if u.data:
    uid = u.data[0]['id']
    supabase.table('orus_messages').delete().eq('user_id', uid).execute()
    supabase.table('orus_users').update({
        'payment_status': 'pending',
        'appointment_date': None,
        'session_mode': 'AI',
        'admin_notified': False,
        'total_spent': 0.0
    }).eq('id', uid).execute()
    print('Reset OK')
```

---

## 5. REGISTRO Y TRAZABILIDAD (Obligatorio)

- **`bitacoras/BITACORA_SESION.md`**: Actualizar al terminar la sesion con Specs completados.
- **`bitacoras/backend_logs.md`**: Todas las decisiones tecnicas de backend (FastAPI, DB, webhooks).
- **`bitacoras/agents_logs.md`**: Todo lo relacionado a Gemini, system prompts, function calling.

---

## 6. PROTOCOLO DE ARTEFACTOS (REPORT_ONLY)

**REGLA DE ORO:** Prohibido incluir solicitudes de autorizacion para ejecutar codigo dentro de cualquier artefacto.
Toda comunicacion de "permiso para continuar" va UNICAMENTE en el chat principal.

---

## 7. ESTRUCTURA DE TRABAJO ("Spec -> Task -> Execute -> Log -> Commit")

1. **Analisis**: Documentar en `specs/` y dividir en Tasks atomicos. Reportar plan y esperar aprobacion.
2. **Ejecucion**: Un Task a la vez. Si falla 3 veces consecutivas, detener y reportar al usuario.
3. **Integracion**: Al finalizar un Spec completo, actualizar `BITACORA_SESION.md`, hacer `git commit` y `git push`.
