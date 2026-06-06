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
> - **Cero texto de relleno. Cero explicaciones de proceso. Solo el resultado.** (Si olvidas esto, estás rompiendo el flujo).
> - **Protocolo de Logs (SSH) OBLIGATORIO:** Tienes la llave de acceso SSH configurada a la VPS (`root@217.196.61.72`). Ante CUALQUIER error, **ESTÁ PROHIBIDO adivinar o proponer parches a ciegas**. Debes conectarte por SSH, extraer logs reales (ej. `docker logs de9751781d7d`) y consultar Supabase antes de tocar una sola línea de código.

---

## 1. CONTEXTO ACTUAL Y PLAN MAESTRO

> [!IMPORTANT]
> **Último Estado:** Infraestructura en Producción — **Spec 33 Completado**. [NOTA DE CORRECCIÓN: El Dashboard está en la VPS (EasyPanel). Lo único en Vercel es la app de recolección de material biométrico.]
> - **El flujo completo ya está cargado y operando en la VPS.**
> - **Backend y Dashboard** están alojados en la VPS mediante EasyPanel.
> - **App de Datos Biométricos** está alojada en Vercel.
> - **Deduplicación y Routing:** Corriendo en producción con 1 worker de uvicorn para garantizar la deduplicación de mensajes. Routing de LIDs corregido.

> [!NOTE]
> **RUTA PARA LA SIGUIENTE SESIÓN (PROCESO DE AFINACIÓN):**
> Al iniciar la siguiente sesión, se debe seguir un riguroso proceso de afinación:
> 1. **Medir el estrés del sistema:** Realizar pruebas de carga y respuesta rápida directamente desde la interfaz del chat del Dashboard.
> 2. **Simular intervenciones manuales:** Alternar entre los modos `HUMAN` y `AI` para estresar los timers de debounce.
> 3. **Coordinar el flujo con el bot:** Probar exhaustivamente el retorno automático del bot a modo `AI` con instrucciones contextuales (`[SYSTEM_NOTE]`) sin generar alucinaciones ni reprocesar material antiguo.

---

## 2. INFRAESTRUCTURA Y DESPLIEGUE (PRODUCCIÓN)

> [!IMPORTANT]
> **YA NO SE LEVANTAN SERVIDORES LOCALES (ni Uvicorn ni ngrok).** El agente ya no necesita iniciar la secuencia de comandos de terminal locales. Todo corre en la VPS (EasyPanel aloja Backend y Dashboard) y Vercel (SOLO la app Biométrica).

### Distribución de Servicios:
- **Backend (FastAPI)**: VPS (EasyPanel) -> `https://api.orusquiroterapia.online`
- **Dashboard (Vite/React)**: VPS (EasyPanel) -> `https://dashboard.orusquiroterapia.online`
- **Evolution API (WhatsApp)**: VPS (EasyPanel) -> `https://whatsapp.orusquiroterapia.online`
- **App de Datos Biométricos**: Vercel -> Link enviado dinámicamente al usuario por WhatsApp.

### Flujo de Actualización:
Para aplicar cambios en el código al Backend o Dashboard:
1. Hacer `git commit` y `git push` a la rama `main` de GitHub.
2. **Desencadenar el Deploy Programáticamente**: Puedes disparar el despliegue automático desde la VPS (dentro de SSH) haciendo un curl POST al webhook interno de EasyPanel (no es necesario usar el navegador):
   - **Backend (`orus-backend`)**:
     ```bash
     ssh root@217.196.61.72 'curl -X POST "http://localhost:3000/api/deploy/3708f141a74cfb80ca83528659f5148ca13e0adf4f6f3074"'
     ```
   - **Dashboard (`orus-dashboard`)**:
     ```bash
     ssh root@217.196.61.72 'curl -X POST "http://localhost:3000/api/deploy/de486e98ab2722590a5265df777bc44227f2e0e984265cb7"'
     ```
3. El deploy es inmediato. Monitorea los logs de compilación consultando la tabla de acciones en SQLite de EasyPanel `/etc/easypanel/data/data.sdb` o leyendo el archivo de log correspondiente en `/etc/easypanel/actions/<action_id>.log`.

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
