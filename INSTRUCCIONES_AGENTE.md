# Instrucciones de Sesion para Agentes

**ESTE ARCHIVO DEBE SER LEIDO POR CUALQUIER AGENTE AL INICIAR UNA SESION.**

## 0. Protocolo de Comunicacion (LECTURA OBLIGATORIA ANTES DE RESPONDER)
> [!IMPORTANT]
> **Skill Activo:** `ultra-concise-chat`
> Antes de generar CUALQUIER respuesta en el chat, lee y aplica este protocolo estrictamente:
> - Si la informacion ya fue guardada en un artefacto o `.md` -> **NO la repitas en el chat.**
> - Task completada -> solo escribe: *"Task #X completada con exito."* o *"Ya complete la tarea. OK."*
> - Si el usuario pide un ajuste -> NO repitas lo que pidió ni le expliques el proceso. Solo di que está completado, EXCEPTO si tomaste una decisión técnica extra que necesite saber.
> - Error encontrado -> solo escribe: *"Error registrado con su correccion en [archivo]."*
> - **Cero texto de relleno. Cero explicaciones de proceso. Solo el resultado.**

---

## 1. CONTEXTO ACTUAL Y PLAN MAESTRO

> [!IMPORTANT]
> **Último Estado (2026-06-04 - Tarde):** Integración de Datos Dinámicos y Hardening VPS (Spec 27).
> - La pestaña "System Logs" ahora consume los logs reales de Supabase (`orus_system_logs`) con una UI glass-minimalista. Se añadió funcionalidad de marcarlos como resueltos.
> - Se integró **Google Calendar** en el Dashboard mediante una credencial en variable de entorno (`GOOGLE_CREDENTIALS_JSON`) permitiendo ver las próximas citas reales.
> - Se implementó un panel de **Notas de Sesión (Bitácora Clínica)** vinculado a los eventos del calendario que se guardan en la tabla `orus_session_notes`.
> - Se reforzó la arquitectura de despliegue en **EasyPanel**, confirmando que todo el backend y frontend operan desde GitHub y usan variables de entorno.
>
> **Pendientes próxima sesión:**
> - Modificar "Inbox Chat" en el Dashboard para responder manualmente a los Handovers directamente desde la interfaz web.
> - El usuario hará pruebas físicas enviando mensajes desde un celular alterno para verificar todo el flujo del Handover.
> - Seguir afinando y optimizando el entorno VPS.

---

## 2. ARRANQUE DE SERVIDORES (DIVISION DE RESPONSABILIDADES)

> [!IMPORTANT]
> **EL AGENTE ejecuta los 3 pasos de forma autonoma. El usuario NO opera la terminal.**

### Secuencia de arranque (orden exacto):

**Paso 1 — Levantar Uvicorn** (el agente lo hace con `Start-Process`):
```powershell
Start-Process powershell -ArgumentList '-NoExit', '-Command', '$env:PYTHONUTF8=1; cd "c:\Users\Fernando\proyecto orus-quiro\proyecto orus-quiro"; uvicorn main:app --host 0.0.0.0 --port 8000 --reload' -WindowStyle Normal
```
Esperar 5 segundos y verificar con:
```powershell
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/').read())"
```
Resultado esperado: `{"message":"Servidor base activo"}`

**Paso 2 — Levantar ngrok** (el agente lo hace con `Start-Process`):
```powershell
Start-Process powershell -ArgumentList '-NoExit', '-Command', 'ngrok http 8000 --url=annually-murmuring-reuse.ngrok-free.dev' -WindowStyle Normal
```
> [!WARNING]
> Si `annually-murmuring-reuse.ngrok-free.dev` falla (URL reservada puede cambiar), omitir el flag `--url` y dejar que ngrok genere una URL dinamica. El Paso 3 la detecta automaticamente.

**Paso 3 — Registrar webhooks** (Evolution API + Stripe simultaneamente):
```powershell
python register_webhook.py
```
Resultado esperado:
```
[1/2] Evolution API -> https://<ngrok-url>/webhook ... Status: 201
[2/2] Stripe -> https://<ngrok-url>/payments/webhook ... Status: enabled
=== REGISTRO COMPLETO ===
```

> [!CAUTION]
> **Cada vez que ngrok se reinicia, los webhooks pierden sincronizacion.**
> SIEMPRE ejecutar `python register_webhook.py` despues de cualquier reinicio de ngrok.
> Stripe y Evolution API deben apuntar a la misma URL ngrok activa — si no, el pago llega pero el bot no responde post-pago.

---

## 3. DIAGNOSTICO RAPIDO SI EL BOT NO RESPONDE

Ejecutar en orden:

```powershell
# 1. Verificar Uvicorn activo
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/').read())"

# 2. Ver ultimos webhooks recibidos por ngrok (deben ser recientes)
python -c "import urllib.request, json; res=json.loads(urllib.request.urlopen('http://127.0.0.1:4040/api/requests/http').read().decode()); [print(r['start'], r['uri'], r['response']['status']) for r in res['requests'][:5]]"

# 3. Ver URL ngrok activa
python -c "import urllib.request, json; r=json.loads(urllib.request.urlopen('http://127.0.0.1:4040/api/tunnels').read().decode()); [print(t['public_url']) for t in r['tunnels']]"

# 4. Re-registrar webhooks si hay discrepancia
python register_webhook.py

# 5. Ver ultimos mensajes del usuario en Supabase
python -c "from dotenv import load_dotenv; load_dotenv(); from api.db.supabase_client import supabase; import json; m=supabase.table('orus_messages').select('role,content,created_at').order('created_at',desc=True).limit(5).execute(); [print(json.dumps(x)) for x in m.data]"
```

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
