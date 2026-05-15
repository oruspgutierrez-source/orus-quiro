import json
from fastapi import APIRouter, Request, HTTPException

router = APIRouter()

# Cache de deduplicación en memoria (message_id → True)
# Se limpia naturalmente por el GC de Python al no tener referencias
_seen_messages: dict[str, bool] = {}
_MAX_SEEN = 10000  # Evitar crecimiento infinito


@router.post("/webhook")
async def receive_webhook(request: Request):
    """
    Endpoint para recibir eventos de Evolution API.
    Retorna 200 OK inmediatamente.
    
    El debounce se maneja en message_processor con asyncio.Task:
    cada mensaje cancela el timer anterior y pone uno nuevo.
    """
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
