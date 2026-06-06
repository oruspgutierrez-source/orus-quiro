import json
import os
from fastapi import APIRouter, Request, HTTPException, Query

router = APIRouter()

# Cache de deduplicación en memoria (message_id → True)
# Se limpia naturalmente por el GC de Python al no tener referencias
_seen_messages: dict[str, bool] = {}
_MAX_SEEN = 10000  # Evitar crecimiento infinito


def _recursive_find(data, target_key):
    """Busca recursivamente una llave en un diccionario o lista anidada."""
    if isinstance(data, dict):
        if target_key in data:
            return data[target_key]
        for v in data.values():
            result = _recursive_find(v, target_key)
            if result is not None:
                return result
    elif isinstance(data, list):
        for item in data:
            result = _recursive_find(item, target_key)
            if result is not None:
                return result
    return None

def normalize_evolution_payload(payload: dict) -> tuple[str, dict]:
    """
    Intenta extraer el 'event', 'data', 'key' y 'message' sin importar 
    si Evolution API los empaquetó en una lista o un objeto directo.
    """
    event_type = payload.get("event", "UNKNOWN")
    
    # Extraer data (puede ser lista o dict)
    raw_data = payload.get("data", {})
    if isinstance(raw_data, list) and len(raw_data) > 0:
        data_node = raw_data[0]
    elif isinstance(raw_data, dict):
        data_node = raw_data
    else:
        data_node = {}

    # Si aún así no tiene 'key' ni 'message', buscar recursivamente (por si la estructura mutó fuerte)
    if "key" not in data_node and "message" not in data_node:
        found_key = _recursive_find(payload, "key")
        found_message = _recursive_find(payload, "message")
        if found_key and found_message:
            data_node = {"key": found_key, "message": found_message}
            
    return event_type, data_node


@router.post("/webhook")
async def receive_webhook(request: Request, token: str = Query(None)):
    """
    Endpoint para recibir eventos de Evolution API.
    Retorna 200 OK inmediatamente.
    
    El debounce se maneja en message_processor con asyncio.Task:
    cada mensaje cancela el timer anterior y pone uno nuevo.
    """
    expected_token = os.getenv("EVOLUTION_WEBHOOK_SECRET")
    if expected_token and token != expected_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    try:
        # Usamos el normalizador blindado
        event_type, data_debug = normalize_evolution_payload(payload)

        key_debug = data_debug.get("key", {})
        msg_debug = data_debug.get("message", {})
        msg_keys = list(msg_debug.keys()) if isinstance(msg_debug, dict) else str(type(msg_debug))
        print(f"[DEBUG WEBHOOK] event={event_type}, fromMe={key_debug.get('fromMe')}, remoteJid={key_debug.get('remoteJid', 'N/A')}, msg_keys={msg_keys}", flush=True)

        # ── DEBUG MEDIA TEMPORAL — Captura completa de payloads multimedia ──
        if event_type == "messages.upsert":
            msg = data_debug.get("message", {})
            media_keys = [k for k in msg.keys() if k not in ("conversation", "extendedTextMessage", "messageContextInfo")]
            if media_keys:
                print(f"\n{'='*60}", flush=True)
                print(f"[DEBUG MEDIA] >>> PAYLOAD MULTIMEDIA DETECTADO <<<", flush=True)
                print(f"[DEBUG MEDIA] Tipos: {media_keys}", flush=True)
                for mk in media_keys:
                    content = msg[mk]
                    if isinstance(content, dict):
                        print(f"[DEBUG MEDIA] {mk} keys: {list(content.keys())}", flush=True)
                        # Imprimir todo EXCEPTO base64 (muy largo)
                        preview = {k: v for k, v in content.items() if k != "base64"}
                        print(f"[DEBUG MEDIA] {mk} data:\n{json.dumps(preview, indent=2, default=str)}", flush=True)
                    else:
                        print(f"[DEBUG MEDIA] {mk} = {content}", flush=True)
                print(f"{'='*60}\n", flush=True)
    
        if event_type == "connection.update":
            state = data_debug.get("state", "UNKNOWN")
            reason = data_debug.get("statusReason", "")
            severity = 'INFO' if state in ['open', 'connecting'] else 'ERROR'
            
            try:
                from api.db.supabase_client import supabase
                from api.services.telegram_client import send_telegram_alert
                
                error_msg = f"WhatsApp Connection: {state.upper()}"
                stack_trace = f"State: {state}\nReason: {reason}\nPayload: {json.dumps(data_debug)}"
                
                supabase.table('orus_logs').insert({
                    'event_type': 'EVOLUTION_CONNECTION_UPDATE',
                    'severity': severity,
                    'error_message': error_msg,
                    'source_identifier': 'Evolution API',
                    'stack_trace': stack_trace
                }).execute()
                
                if severity == 'ERROR':
                    alert_text = f"🚨 *ALERTA CRÍTICA ORUS* 🚨\nFalla en Evolution API:\n*Estado:* {state}\n*Razón:* {reason}\n*Acción:* Revisa el celular o la instancia de EasyPanel de inmediato."
                    import asyncio
                    # El webhook es async, podemos enviarlo directo
                    asyncio.create_task(send_telegram_alert(alert_text))
                    
            except Exception as e:
                print(f"Error logging connection update: {e}", flush=True)
                
            return {"status": "logged"}
    
        if event_type == "messages.upsert":
            data = data_debug  # Ya manejamos si era lista arriba
            key = data.get("key", {})
    
            if key.get("fromMe") is True:
                return {"status": "ignored", "reason": "fromMe=true"}
    
            sender_id = key.get("remoteJid", "")
            
            # Resolver @lid al JID real inmediatamente para todo el sistema
            if sender_id.endswith("@lid"):
                from api.services.wa_client import wa_client
                real_jid = await wa_client.resolve_lid(sender_id)
                if real_jid != sender_id:
                    print(f"[Webhook] LID {sender_id} resuelto a {real_jid} exitosamente.", flush=True)
                    sender_id = real_jid
                else:
                    print(f"[Webhook] ADVERTENCIA: No se pudo resolver el LID {sender_id}", flush=True)
    
            participant = key.get("participant")
            if participant and not sender_id.endswith("@g.us"):
                sender_id = participant
    
            # ── Tipos de media soportados ──────────────────────────────────────
            MEDIA_TYPES = {
                "imageMessage": "image",
                "audioMessage": "audio",
                "documentMessage": "document",
                "videoMessage": "video"
            }
    
            message = data.get("message", {})
            text_body = None
            media_info = None  # Se llena si hay contenido multimedia
    
            # 1. Intentar extraer texto plano
            if "conversation" in message:
                text_body = message["conversation"]
            elif "extendedTextMessage" in message:
                text_body = message["extendedTextMessage"].get("text")
    
            # 2. Detectar contenido multimedia
            for msg_key, media_type in MEDIA_TYPES.items():
                if msg_key in message:
                    media_msg = message[msg_key]
                    caption = media_msg.get("caption")  # Puede ser None
                    mime_type = media_msg.get("mimetype", "")
                    file_name = media_msg.get("fileName")  # Solo documentMessage
                    
                    # NO descargar aquí — solo guardar metadata + message_key
                    # La descarga se hace en _process_buffer después del debounce
                    # (le da tiempo a Evolution API para almacenar el mensaje)
                    
                    # A veces Evolution API ya envía el base64 en el webhook si está configurado
                    # Puede venir en data["base64"] o message["base64"] o en media_msg
                    direct_base64 = payload.get("base64") or data.get("base64") or message.get("base64")
                    if not direct_base64 and isinstance(media_msg, dict):
                        direct_base64 = media_msg.get("base64")
                    
                    media_info = {
                        "type": media_type,
                        "mime_type": mime_type.split(";")[0].strip(),
                        "message_key": key,  # Para descargar después
                        "message_obj": message,  # Contiene llaves criptográficas
                        "caption": caption,
                        "file_name": file_name,
                        "base64": direct_base64  # Puede ser None, si lo es, se descarga
                    }
                    print(f"[Webhook] Media detectado: {media_type} ({mime_type}), caption={caption}, tiene_base64={bool(direct_base64)}", flush=True)
                    break  # Solo procesar el primer tipo de media encontrado
    
            # Si no hay texto NI media, ignorar
            if not text_body and not media_info:
                print(f"[DEBUG] Mensaje sin texto ni media. msg_keys={list(message.keys())}", flush=True)
                return {"status": "ignored", "reason": "no text or media"}
    
            # ── Deduplicación por ID de mensaje ────────────────────────────────
            message_id = key.get("id")
            if message_id:
                if message_id in _seen_messages:
                    return {"status": "ignored", "reason": "duplicate_message"}
                # Limpiar cache si crece demasiado
                if len(_seen_messages) > _MAX_SEEN:
                    _seen_messages.clear()
                _seen_messages[message_id] = True
    
            # ── Acumular y debounce ────────────────────────────────────────────
            from api.services.message_processor import buffer_message
            await buffer_message(sender_id, text_body, media_info, payload)
            media_label = f" + {media_info['type']}" if media_info else ""
            print(f"[Webhook] Mensaje de {sender_id} bufferizado{media_label}", flush=True)
    
    except Exception as general_exc:
        # [Task 34] Blindaje y Telemetría: Si el payload mutó y crasheó, lo atrapamos
        import traceback
        import asyncio
        from api.db.supabase_client import supabase
        from api.services.telegram_client import send_telegram_alert
        
        stack = traceback.format_exc()
        print(f"[CRITICAL_PAYLOAD_ANOMALY] Error procesando webhook:\n{stack}", flush=True)
        
        try:
            # Guardamos el payload crudo en DB para inspección
            payload_str = json.dumps(payload) if 'payload' in locals() else "UNKNOWN_PAYLOAD"
            keys_preview = list(payload.keys()) if 'payload' in locals() and isinstance(payload, dict) else "N/A"
            
            supabase.table('orus_logs').insert({
                'event_type': 'CRITICAL_PAYLOAD_ANOMALY',
                'severity': 'ERROR',
                'error_message': f"Fallo al normalizar Payload. Exception: {str(general_exc)}",
                'source_identifier': 'Evolution API Webhook',
                'stack_trace': f"Keys encontradas: {keys_preview}\n{stack}\n\nRAW PAYLOAD:\n{payload_str[:2000]}"
            }).execute()
            
            # Alarma en Telegram
            alert_msg = (
                f"🚨 *ALERTA DE MUTACIÓN DE PAYLOAD* 🚨\n"
                f"Evolution API ha enviado una estructura desconocida o ha ocurrido un fallo grave.\n"
                f"*Keys:* `{keys_preview}`\n"
                f"*Error:* `{str(general_exc)}`\n"
                f"Revisa la tabla `orus_logs` en el Dashboard para ver el payload intacto."
            )
            asyncio.create_task(send_telegram_alert(alert_msg))
        except Exception as db_exc:
            print(f"[ERROR_EN_ALERTA] No se pudo guardar el log de anomalía: {db_exc}", flush=True)
            
        # Devolvemos 200 OK de todas formas a Evolution API para evitar que reintente infinitamente
        return {"status": "anomaly_handled_silently"}

    return {"status": "ok"}


@router.post("/api/biometrics/completed")
async def biometrics_completed(request: Request):
    """
    Endpoint para recibir la notificación de Supabase Database Webhook
    cuando el usuario completa la carga de fotos biométricas.
    """
    from api.db.supabase_client import supabase
    from api.services.wa_client import wa_client

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    print(f"[Supabase Webhook] Payload recibido: {json.dumps(payload, indent=2)}", flush=True)

    record = payload.get("record")
    if not record:
        if "wa_id" in payload:
            record = payload
        else:
            return {"status": "ignored", "reason": "no_record"}

    # Opción B: Fotos completadas debe ser True
    if not record.get("fotos_completadas"):
        return {"status": "ignored", "reason": "fotos_completadas_not_true"}

    wa_id = record.get("wa_id")
    nombre = record.get("nombre") or "Consultante"

    if not wa_id:
        return {"status": "ignored", "reason": "no_wa_id"}

    # Formatear a JID compatible con WhatsApp
    to_jid = str(wa_id).strip()
    if "@" not in to_jid:
        to_jid = f"{to_jid}@s.whatsapp.net"

    msg_text = f"¡Excelente, *{nombre}*! Hemos recibido tus fotografías biométricas con total éxito. Con esto completamos oficialmente todo tu proceso de preparación.\n\nTu hardware biológico ha sido registrado y el ciclo de configuración de tu Auditoría Biosemiótica está cerrado. Te deseo el mayor de los éxitos en tu camino de Re-Ingeniería de aquí hasta el día de nuestra charla de Revelación. ¡Nos vemos pronto!"

    try:
        # Buscar usuario para registrar en orus_messages
        user_check = supabase.table('orus_users').select('id').eq('phone_number', to_jid).execute()
        if user_check.data:
            user_uuid = user_check.data[0].get('id')
            supabase.table('orus_messages').insert({
                'user_id': user_uuid,
                'role': 'assistant',
                'content': msg_text
            }).execute()
            print(f"[Supabase Webhook] Mensaje registrado en orus_messages para user_uuid={user_uuid}", flush=True)
        else:
            # Si no existe, crear usuario e insertar mensaje
            new_user = supabase.table('orus_users').insert({'phone_number': to_jid}).execute()
            if new_user.data:
                user_uuid = new_user.data[0].get('id')
                supabase.table('orus_messages').insert({
                    'user_id': user_uuid,
                    'role': 'assistant',
                    'content': msg_text
                }).execute()
                print(f"[Supabase Webhook] Usuario creado y mensaje registrado para user_uuid={user_uuid}", flush=True)

        # Enviar notificación WhatsApp
        await wa_client.send_message(to=to_jid, text=msg_text)
        print(f"[Supabase Webhook] Notificación enviada a {to_jid}", flush=True)

        return {"status": "success", "message": "notification_sent", "to": to_jid}

    except Exception as e:
        print(f"[Supabase Webhook] Error procesando notificación: {e}", flush=True)
        # Registrar log del error en orus_logs
        try:
            supabase.table('orus_logs').insert({
                'event_type': 'WEBHOOK_BIOMETRICS_ERROR',
                'source_identifier': to_jid,
                'error_message': str(e)
            }).execute()
        except Exception as db_exc:
            print(f"Fallo al registrar log de error: {db_exc}", flush=True)
        
        raise HTTPException(status_code=500, detail=str(e))

