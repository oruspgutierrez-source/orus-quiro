import json
import os
from fastapi import APIRouter, Request, HTTPException, Query

router = APIRouter()

# Cache de deduplicación en memoria (message_id → True)
# Se limpia naturalmente por el GC de Python al no tener referencias
_seen_messages: dict[str, bool] = {}
_MAX_SEEN = 10000  # Evitar crecimiento infinito


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

    event_type = payload.get("event")

    # DEBUG TEMPORAL — ver qué llega al webhook
    data_debug = payload.get("data", {})
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

    if event_type == "messages.upsert":
        data = payload.get("data", {})
        key = data.get("key", {})

        if key.get("fromMe") is True:
            return {"status": "ignored", "reason": "fromMe=true"}

        sender_id = key.get("remoteJid")

        if not sender_id or "@broadcast" in sender_id:
            return {"status": "ignored"}

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
                media_info = {
                    "type": media_type,
                    "mime_type": mime_type.split(";")[0].strip(),
                    "message_key": key,  # Para descargar después
                    "message_obj": message,  # Contiene llaves criptográficas
                    "caption": caption,
                    "file_name": file_name
                }
                print(f"[Webhook] Media detectado: {media_type} ({mime_type}), caption={caption}", flush=True)
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

