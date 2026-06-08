"""
Message Processor — Debounce con asyncio.Task (reemplazo de ARQ Worker)

Patrón: Sliding Window Cancel-and-Restart
- Cada mensaje cancela el timer anterior del usuario y crea uno nuevo.
- Cuando nadie escribe en DEBOUNCE_WAIT segundos, se procesa todo junto.
- Equivalente exacto al nodo "Wait" de n8n, pero en Python puro.
"""

import asyncio
import re
import time
import os
from api.db.supabase_client import supabase
from api.services.security import check_rate_limit, sanitize_input, log_security_event
from api.services.gemini_client import generate_response
from api.services.telegram_client import send_telegram_alert
from api.services.wa_client import wa_client

# ── Configuración ──────────────────────────────────────────────────────────────
DEBOUNCE_WAIT = 10  # Segundos de silencio antes de procesar

# ── Estado en memoria ──────────────────────────────────────────────────────────
# Timers activos por usuario (sender_id → asyncio.Task)
_debounce_timers: dict[str, asyncio.Task] = {}
# Buffers de mensajes por usuario (sender_id → lista de dicts)
# Cada item: {"type": "text"|"media", "content": str, "media": dict|None}
_message_buffers: dict[str, list[dict]] = {}
# Lock por usuario para evitar condiciones de carrera en el buffer
_buffer_locks: dict[str, asyncio.Lock] = {}


def _get_lock(sender_id: str) -> asyncio.Lock:
    """Obtiene o crea un lock asyncio para un sender_id específico."""
    if sender_id not in _buffer_locks:
        _buffer_locks[sender_id] = asyncio.Lock()
    return _buffer_locks[sender_id]


async def buffer_message(sender_id: str, text: str | None, media_info: dict | None, payload: dict):
    """
    Punto de entrada principal. Llamado desde el webhook.
    Acumula el mensaje (texto y/o media) y resetea el timer de debounce.
    
    Args:
        sender_id: JID del remitente
        text: Texto del mensaje o caption (puede ser None si es media sin caption)
        media_info: Dict con {type, mime_type, bytes, caption, file_name} o None
        payload: Payload original del webhook
    """
    lock = _get_lock(sender_id)
    async with lock:
        # Acumular mensaje en el buffer
        if sender_id not in _message_buffers:
            _message_buffers[sender_id] = []
        
        # Agregar texto si existe
        if text:
            _message_buffers[sender_id].append({
                "type": "text",
                "content": text,
                "media": None
            })
        
        # Agregar media si existe (como entrada separada)
        if media_info:
            _message_buffers[sender_id].append({
                "type": "media",
                "content": media_info.get("caption"),
                "media": media_info
            })
        
        buffer_size = len(_message_buffers[sender_id])
        media_label = f" [{media_info['type']}]" if media_info else ""
        print(f"[Buffer] {sender_id}: +1 msg{media_label} (total={buffer_size})", flush=True)

        # Cancelar timer anterior si existe (sliding window)
        if sender_id in _debounce_timers:
            _debounce_timers[sender_id].cancel()
            print(f"[Debounce] Timer cancelado para {sender_id}, reiniciando...", flush=True)

        # Crear nuevo timer
        task = asyncio.create_task(
            _debounce_then_process(sender_id, payload)
        )
        _debounce_timers[sender_id] = task


async def _debounce_then_process(sender_id: str, payload: dict):
    """
    Fase 1 (cancelable): Espera DEBOUNCE_WAIT segundos.
    Fase 2 (NO cancelable): Procesa el buffer completo.
    
    Si es cancelado durante la espera → no hace nada (otro mensaje llegó).
    Si la espera completa → se des-registra del dict y procesa sin interrupción.
    """
    # ── Fase 1: Espera (cancelable) ──────────────────────────────────────
    try:
        await asyncio.sleep(DEBOUNCE_WAIT)
    except asyncio.CancelledError:
        # Timer cancelado porque llegó un mensaje nuevo — comportamiento esperado
        return

    # ── Fase 2: Procesar (NO cancelable) ─────────────────────────────────
    # Quitar referencia del timer ANTES de procesar para que nuevos
    # mensajes durante el procesamiento creen su propio timer limpio.
    if _debounce_timers.get(sender_id) is asyncio.current_task():
        del _debounce_timers[sender_id]

    await _process_buffer(sender_id, payload)


async def _process_buffer(sender_id: str, payload: dict):
    """
    Toma todos los mensajes acumulados del buffer y ejecuta el pipeline completo:
    LID → Firewall → Rate Limit → Sanitización → Gemini (multimodal) → Envío fragmentado.
    """
    lock = _get_lock(sender_id)
    async with lock:
        buffer_items = _message_buffers.pop(sender_id, [])
    
    if not buffer_items:
        return

    # ── Reconstruir flujo secuencial de media y texto ──────────────────────
    text_parts = []
    media_list = []
    media_counter = 1
    
    print(f"[Processor] Analizando buffer multimedia de {sender_id}...", flush=True)
    
    for item in buffer_items:
        if item["type"] == "text" and item.get("content"):
            text_parts.append(f"\n[Mensaje de texto independiente]: {item['content']}")
            
        elif item["type"] == "media" and item.get("media"):
            media_meta = item["media"]
            message_key = media_meta.get("message_key")
            message_obj = media_meta.get("message_obj")
            
            if not message_key or not message_obj:
                continue
                
            media_bytes = None
            if media_meta.get("base64"):
                import base64
                print("[Processor] Usando base64 directamente del webhook", flush=True)
                b64_string = media_meta["base64"]
                if "," in b64_string:
                    b64_string = b64_string.split(",", 1)[1]
                try:
                    media_bytes = base64.b64decode(b64_string)
                except Exception as e:
                    print(f"[Processor] Error decodificando base64 directo: {e}", flush=True)
            
            if not media_bytes:
                media_bytes = await wa_client.download_media(message_key, message_obj)
                
            if media_bytes:
                # ── CONVERSIÓN DE AUDIO OGG A MP3 ──
                if "audio" in media_meta["type"]:
                    try:
                        import tempfile
                        import subprocess
                        import os
                        
                        print(f"[Processor] Convirtiendo audio a MP3...", flush=True)
                        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f_in:
                            f_in.write(media_bytes)
                            temp_ogg = f_in.name
                            
                        temp_mp3 = temp_ogg.replace(".ogg", ".mp3")
                        
                        # Ejecutar ffmpeg sin mostrar output
                        subprocess.run([
                            "ffmpeg", "-y", "-i", temp_ogg, 
                            "-ar", "16000", "-ac", "1", "-map", "a", temp_mp3
                        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        
                        with open(temp_mp3, "rb") as f_out:
                            media_bytes = f_out.read()
                            
                        media_meta["mime_type"] = "audio/mp3"
                        
                        os.remove(temp_ogg)
                        os.remove(temp_mp3)
                        print(f"[Processor] Audio convertido a MP3 exitosamente", flush=True)
                    except Exception as e:
                        print(f"[Processor] Error convirtiendo audio: {e}", flush=True)
                        # Si falla, intentamos mandar el original de todos modos

                media_list.append({
                    "bytes": media_bytes,
                    "mime_type": media_meta["mime_type"],
                    "media_type": media_meta["type"],
                    "file_name": media_meta.get("file_name")
                })
                
                caption = item.get("content")
                if "audio" in media_meta["type"]:
                    text_parts.append(f"\n[Adjunto {media_counter}: NOTA DE VOZ. ATENCIÓN ORUS: DEBES procesar el audio adjunto {media_counter}. El texto a continuación NO es el audio]")
                elif caption:
                    text_parts.append(f"\n[Adjunto {media_counter}: {media_meta['type']} con texto/caption]: {caption}")
                else:
                    text_parts.append(f"\n[Adjunto {media_counter}: {media_meta['type']} sin texto]")
                
                print(f"[Processor] {media_meta['type']} descargado: {len(media_bytes)} bytes", flush=True)
                media_counter += 1
            else:
                print(f"[Processor] Fallo descarga de {media_meta['type']}", flush=True)
                text_parts.append(f"[Intento de enviar {media_meta['type']} pero falló la descarga]")

    # Detectar si son mensajes muy cortos (posible ráfaga incompleta)
    all_short = len(text_parts) == 1 and len(text_parts[0]) < 10 and not media_list
    many_short = len(text_parts) > 1 and all(len(m) < 10 for m in text_parts) and not media_list
    hint = "\n[NOTA: el usuario puede haber enviado un mensaje incompleto]" if (all_short or many_short) else ""
    text_body = "\n".join(text_parts) + hint

    media_label = f" + {len(media_list)} archivo(s) multimedia" if media_list else ""
    print(f"[Processor] Procesando {len(buffer_items)} item(s) de {sender_id}{media_label}:\n{text_body}", flush=True)

    try:
        # ── 1. Usar sender_id directo (ya resuelto en webhook, o LID que WA enruta OK) ─
        # [Spec 34-B2] resolve_lid via /chat/findContacts devuelve números INCORRECTOS.
        # La resolución LID→JID ocurre en webhooks.py desde la tabla _lid_to_jid.
        real_sender_id = sender_id

        # ── 2. Persistir payload ───────────────────────────────────────────────
        try:
            supabase.table('orus_webhooks_buffer').insert({
                'sender_id': real_sender_id,
                'payload': payload
            }).execute()
        except Exception as e:
            print(f"Error guardando payload en buffer: {e}", flush=True)

        # ── 3. Firewall: verificar usuario ─────────────────────────────────────
        user_uuid = None
        session_mode = 'AI'
        payment_status = 'pending'
        appointment_date = None
        try:
            user_check = supabase.table('orus_users').select('id, is_blocked, session_mode, payment_status, appointment_date').eq('phone_number', real_sender_id).execute()
            if user_check.data:
                user_data = user_check.data[0]
                if user_data.get('is_blocked'):
                    print(f"[Processor] Usuario bloqueado: {real_sender_id}", flush=True)
                    return
                user_uuid = user_data.get('id')
                session_mode = user_data.get('session_mode') or 'AI'
                payment_status = user_data.get('payment_status') or 'pending'
                appointment_date = user_data.get('appointment_date')
            else:
                new_user = supabase.table('orus_users').insert({'phone_number': real_sender_id}).execute()
                user_uuid = new_user.data[0].get('id')
        except Exception as e:
            print(f"Error en validación de usuario: {e}", flush=True)

        # ── 4. Rate Limiter ────────────────────────────────────────────────────
        if check_rate_limit(real_sender_id):
            try:
                supabase.table('orus_users').update({'is_blocked': True}).eq('phone_number', real_sender_id).execute()
                log_security_event('WARNING', 'SPAM_AUTOBLOCK', real_sender_id, 'Bloqueado por spam', text_body)
                await send_telegram_alert(f"🚨 SPAM detectado.\nUsuario bloqueado: {real_sender_id}")
            except Exception:
                pass
            return

        # ── 5. Sanitización ────────────────────────────────────────────────────
        cleaned_text, is_threat, threat_type = sanitize_input(text_body)
        if is_threat:
            log_security_event('WARNING', threat_type, real_sender_id, f'Amenaza: {threat_type}', text_body)
            return

        # ── 5.5. Máquina de Estados: Handover & Quejas ─────────────────────────
        text_lower = cleaned_text.lower()
        
        async def escalate_to_human(reason=""):
            if user_uuid:
                supabase.table('orus_users').update({'session_mode': 'HUMAN', 'admin_notified': True}).eq('id', user_uuid).execute()
            alert_msg = f"🚨 URGENTE: Atención requerida.\nUsuario: {real_sender_id}\nMotivo: {reason}\nÚltimo mensaje: {cleaned_text}"
            await send_telegram_alert(alert_msg)
            
            admin_whatsapp = os.getenv("ADMIN_WHATSAPP_NUMBER")
            if admin_whatsapp:
                if not admin_whatsapp.endswith("@s.whatsapp.net"):
                    admin_whatsapp += "@s.whatsapp.net"
                try:
                    await wa_client.send_message(to=admin_whatsapp, text=alert_msg)
                except Exception as e:
                    print(f"Error enviando alerta a WhatsApp Admin: {e}", flush=True)

        if session_mode == 'HUMAN':
            print(f"[Processor] Mensaje ignorado, el usuario {real_sender_id} está en modo HUMAN.", flush=True)
            if user_uuid:
                import uuid
                import mimetypes
                
                final_content = text_body
                if media_list:
                    print(f"[Processor] Procesando {len(media_list)} archivos multimedia para modo HUMAN...", flush=True)
                    for media in media_list:
                        ext = mimetypes.guess_extension(media['mime_type']) or ""
                        # Ajuste para audios ogg (guess_extension a veces no es exacto)
                        if media['mime_type'] == 'audio/mp3' and ext != '.mp3':
                            ext = '.mp3'
                        filename = f"inbox_media/{user_uuid}/{uuid.uuid4()}{ext}"
                        
                        try:
                            # Subir a supabase (inbox_media)
                            supabase.storage.from_('inbox_media').upload(
                                path=filename,
                                file=media['bytes'],
                                file_options={"content-type": media['mime_type']}
                            )
                            # Obtener URL publica
                            public_url = supabase.storage.from_('inbox_media').get_public_url(filename)
                            
                            if "image" in media['media_type']:
                                final_content += f"\n\n![Imagen Adjunta]({public_url})"
                            elif "audio" in media['media_type']:
                                final_content += f"\n\n[Audio Adjunto]({public_url})"
                            else:
                                final_content += f"\n\n[Documento Adjunto]({public_url})"
                                
                        except Exception as e:
                            print(f"[Processor] Error subiendo media a Supabase en modo HUMAN: {e}", flush=True)
                            
                supabase.table('orus_messages').insert({'user_id': user_uuid, 'role': 'user', 'content': final_content}).execute()
            return
            
        elif session_mode == 'CONFIRMING_HANDOVER':
            if any(word in text_lower for word in ['sí', 'si', 'claro', 'por favor', 'ok', 'yes', 'confirm', 'quiero']):
                await escalate_to_human("Confirmó transferencia a humano")
                msg_text = "Perfecto, te transferiré con un especialista. Un humano se pondrá en contacto contigo pronto por este mismo medio."
                await wa_client.send_message(to=real_sender_id, text=msg_text)
                if user_uuid:
                    supabase.table('orus_messages').insert({'user_id': user_uuid, 'role': 'assistant', 'content': msg_text}).execute()
            elif any(word in text_lower for word in ['no', 'cancelar', 'nunca', 'falso']):
                if user_uuid:
                    supabase.table('orus_users').update({'session_mode': 'AI'}).eq('id', user_uuid).execute()
                msg_text = "Entiendo. Entonces, ¿cómo puedo ayudarte? Mi propósito es realizar el diagnóstico de tu hardware biológico mediante la Auditoría Biosemiótica y esto es lo que podemos hacer. ¿Deseas continuar con el proceso?"
                await wa_client.send_message(to=real_sender_id, text=msg_text)
                if user_uuid:
                    supabase.table('orus_messages').insert({'user_id': user_uuid, 'role': 'assistant', 'content': msg_text}).execute()
            else:
                if user_uuid:
                    supabase.table('orus_users').update({'session_mode': 'COMPLAINT_MODE'}).eq('id', user_uuid).execute()
                msg_text = "Por favor, dime detalladamente cuál es tu inconveniente o queja para poder ayudarte mejor."
                await wa_client.send_message(to=real_sender_id, text=msg_text)
                if user_uuid:
                    supabase.table('orus_messages').insert({'user_id': user_uuid, 'role': 'assistant', 'content': msg_text}).execute()
            
            if user_uuid:
                supabase.table('orus_messages').insert({'user_id': user_uuid, 'role': 'user', 'content': text_body}).execute()
            return

        elif session_mode == 'COMPLAINT_MODE':
            await escalate_to_human("Queja registrada")
            msg_text = "Tu incomodidad fue enviada y será evaluada por nuestro equipo. Se te enviará un mensaje cuando haya una respuesta. ¡Hasta pronto!"
            await wa_client.send_message(to=real_sender_id, text=msg_text)
            if user_uuid:
                supabase.table('orus_messages').insert({'user_id': user_uuid, 'role': 'user', 'content': text_body}).execute()
                supabase.table('orus_messages').insert({'user_id': user_uuid, 'role': 'assistant', 'content': msg_text}).execute()
            return

        else:
            handover_keywords = ['humano', 'asesor', 'persona', 'alguien', 'queja', 'estafa', 'fraude', 'no sirve', 'mal servicio', 'ayuda humana']
            if any(kw in text_lower for kw in handover_keywords):
                if user_uuid:
                    supabase.table('orus_users').update({'session_mode': 'CONFIRMING_HANDOVER'}).eq('id', user_uuid).execute()
                msg_text = "He detectado que deseas hablar con un humano o reportar un inconveniente. ¿Deseas que te transfiera con un especialista humano para resolver esto? (Responde SÍ o NO)"
                await wa_client.send_message(to=real_sender_id, text=msg_text)
                if user_uuid:
                    supabase.table('orus_messages').insert({'user_id': user_uuid, 'role': 'user', 'content': text_body}).execute()
                    supabase.table('orus_messages').insert({'user_id': user_uuid, 'role': 'assistant', 'content': msg_text}).execute()
                return

        # ── 5.6. Switch Determinista de Estados ─────────────────────────────────
        is_payment_paid = (payment_status == 'paid')
        
        if not is_payment_paid:
            desvio_keywords = ['?', '¿', 'quien es', 'quien eres', 'quién es', 'quién eres', 'quiromancia', 'magia', 'estudio', 'donde estan', 'dónde están', 'costo', 'precio', 'cuanto cuesta', 'cuánto cuesta', 'neuro', 'biosemiotica', 'metodo', 'metodologia', 'cómo es', 'como es']
            es_desvio = any(kw in text_lower for kw in desvio_keywords) or ('?' in cleaned_text)
            
            # Caso 1: ACOGIDA / AI Inicial
            if session_mode == 'AI':
                msg_text = (
                    "Bienvenido al taller. Lo que hacemos aquí no se basa en adivinación ni en interpretación subjetiva. "
                    "Trabajamos con el hardware biológico: las señales que tu cuerpo ya registró y que definen tus patrones de "
                    "comportamiento, decisión y relación. El proceso se llama Auditoría Biosemiótica, y está fundamentado en la "
                    "intersección entre la tradición del Hasta Samudrika Shastra y las ciencias del comportamiento humano. "
                    "¿Te gustaría que te explique en detalle cómo funciona este diagnóstico?"
                )
                if user_uuid:
                    supabase.table('orus_users').update({'session_mode': 'PHASE_1_ACOGIDA'}).eq('id', user_uuid).execute()
                    supabase.table('orus_messages').insert({'user_id': user_uuid, 'role': 'user', 'content': text_body}).execute()
                    supabase.table('orus_messages').insert({'user_id': user_uuid, 'role': 'assistant', 'content': msg_text}).execute()
                await wa_client.send_message(to=real_sender_id, text=msg_text)
                return

            # Caso 2: PHASE_1_ACOGIDA
            elif session_mode == 'PHASE_1_ACOGIDA':
                affirmative_keywords = ['sí', 'si', 'claro', 'por favor', 'ok', 'yes', 'quiero', 'dale', 'dale una', 'explicame', 'cómo funciona', 'continua', 'continuemos', 'explicación', 'audio', 'explicacion']
                es_afirmativo = any(kw in text_lower for kw in affirmative_keywords)
                
                if es_afirmativo and not es_desvio:
                    from api.services.gemini_client import send_introductory_audio
                    await send_introductory_audio(real_sender_id)
                    if user_uuid:
                        supabase.table('orus_users').update({'session_mode': 'PHASE_2_AUDIO'}).eq('id', user_uuid).execute()
                        supabase.table('orus_messages').insert({'user_id': user_uuid, 'role': 'user', 'content': text_body}).execute()
                        supabase.table('orus_messages').insert({'user_id': user_uuid, 'role': 'assistant', 'content': '[AUDIO_ENVIADO]'}).execute()
                    return
                elif es_desvio:
                    cleaned_text += "\n[INSTRUCCIÓN INTERNA: El usuario está en la fase de Acogida (Fase 1) y tiene una duda. Responde de forma clínica y autoritaria a su duda. Al final de tu respuesta, pregúntale explícitamente si tiene alguna otra pregunta o si desea proceder con el protocolo de atendimiento enviándole la explicación técnica mediante el audio de 3 minutos (respondiendo SÍ).]"
                else:
                    msg_text = "¿Te gustaría que te explique en detalle cómo funciona el diagnóstico de Auditoría Biosemiótica? Responde SÍ para compartirte la explicación técnica."
                    if user_uuid:
                        supabase.table('orus_messages').insert({'user_id': user_uuid, 'role': 'user', 'content': text_body}).execute()
                        supabase.table('orus_messages').insert({'user_id': user_uuid, 'role': 'assistant', 'content': msg_text}).execute()
                    await wa_client.send_message(to=real_sender_id, text=msg_text)
                    return

            # Caso 3: PHASE_2_AUDIO
            elif session_mode == 'PHASE_2_AUDIO':
                purchase_keywords = ['quiero comprar', 'quiero iniciar', 'sí', 'si', 'cómo pago', 'link', 'enlace', 'pagar', 'comprar', 'continuar', 'continuemos', 'iniciar', 'empezar', 'comenzar', 'listo', 'lista', 'adquirir', 'stripe']
                es_compra = any(kw in text_lower for kw in purchase_keywords)
                
                if es_compra and not es_desvio:
                    from api.services.gemini_client import generate_payment_link
                    await generate_payment_link(real_sender_id)
                    if user_uuid:
                        supabase.table('orus_users').update({'session_mode': 'PHASE_3_COBRO'}).eq('id', user_uuid).execute()
                        supabase.table('orus_messages').insert({'user_id': user_uuid, 'role': 'user', 'content': text_body}).execute()
                        supabase.table('orus_messages').insert({'user_id': user_uuid, 'role': 'assistant', 'content': '[COBRO_ENVIADO]'}).execute()
                    return
                elif es_desvio:
                    cleaned_text += "\n[INSTRUCCIÓN INTERNA: El usuario ya recibió el audio explicativo y tiene una duda. Responde de forma clínica y autoritaria a su duda. Al final de tu respuesta, pregúntale explícitamente si tiene alguna otra pregunta o si desea proceder con el protocolo de atendimiento enviándole el enlace seguro de pago de Stripe (49 USD) para iniciar su proceso.]"
                else:
                    msg_text = "¿Deseas iniciar tu proceso de Auditoría Biosemiótica? Si estás listo, respóndeme con un sí o pídeme el enlace de pago seguro para comenzar."
                    if user_uuid:
                        supabase.table('orus_messages').insert({'user_id': user_uuid, 'role': 'user', 'content': text_body}).execute()
                        supabase.table('orus_messages').insert({'user_id': user_uuid, 'role': 'assistant', 'content': msg_text}).execute()
                    await wa_client.send_message(to=real_sender_id, text=msg_text)
                    return

            # Caso 4: PHASE_3_COBRO
            elif session_mode == 'PHASE_3_COBRO':
                link_keywords = ['enlace', 'link', 'pago', 'pagar', 'volver a enviar', 'mandar', 'enviar', 'no me llego', 'no me llegó', 'stripe']
                es_pedido_link = any(kw in text_lower for kw in link_keywords)
                
                if es_pedido_link and not es_desvio:
                    from api.services.gemini_client import generate_payment_link
                    await generate_payment_link(real_sender_id)
                    if user_uuid:
                        supabase.table('orus_messages').insert({'user_id': user_uuid, 'role': 'user', 'content': text_body}).execute()
                        supabase.table('orus_messages').insert({'user_id': user_uuid, 'role': 'assistant', 'content': '[COBRO_ENVIADO]'}).execute()
                    return
                elif es_desvio:
                    cleaned_text += "\n[INSTRUCCIÓN INTERNA: El enlace de pago ya fue enviado (Fase 3). El usuario tiene una duda o objeción. Responde de forma clínica y autoritaria a su duda. Al final de tu respuesta, pregúntale explícitamente si tiene alguna otra pregunta o si desea proceder con el protocolo de atendimiento realizando el pago mediante el enlace seguro que le enviaste para poder agendar su sesión.]"
                else:
                    msg_text = "El enlace de pago seguro de Stripe (49 USD) ya fue generado y enviado a este chat. Una vez completado el pago, el sistema te permitirá agendar tu sesión de forma inmediata. ¿Deseas que te lo envíe nuevamente?"
                    if user_uuid:
                        supabase.table('orus_messages').insert({'user_id': user_uuid, 'role': 'user', 'content': text_body}).execute()
                        supabase.table('orus_messages').insert({'user_id': user_uuid, 'role': 'assistant', 'content': msg_text}).execute()
                    await wa_client.send_message(to=real_sender_id, text=msg_text)
                    return

        # ── 6. LLM con Memoria ────────────────────────────────────────────────
        history_msgs = []
        if user_uuid:
            try:
                history = supabase.table('orus_messages').select('role, content').eq('user_id', user_uuid).order('created_at', desc=True).limit(8).execute()
                if history.data:
                    has_assistant_responded = False
                    for msg in history.data:
                        if "[SYSTEM_NOTE]" in msg['content']:
                            # Si ya hubo una respuesta del asistente posterior a esta nota, significa que fue procesada/resuelta
                            if has_assistant_responded:
                                # Cortamos el historial aquí pero NO inyectamos la nota interna como instrucción activa
                                break
                            else:
                                # Nota interna activa: la insertamos como contexto del LLM y cortamos la memoria
                                note = msg['content'].replace('[SYSTEM_NOTE]', '').strip()
                                history_msgs.append({"role": "model", "text": f"[Instrucción Interna del Administrador]: {note}. Retoma la conversación a partir de aquí."})
                                break
                        
                        if msg['role'] == 'assistant':
                            has_assistant_responded = True
                        
                        gemini_role = "model" if msg['role'] == 'assistant' else "user"
                        history_msgs.append({"role": gemini_role, "text": msg['content']})
                    
                    history_msgs.reverse() # Invertir para que queden cronológicos
                
                supabase.table('orus_messages').insert({
                    'user_id': user_uuid,
                    'role': 'user',
                    'content': text_body
                }).execute()
            except Exception as e:
                print(f"Error con historial/persistencia: {e}", flush=True)

        prompt_with_context = f"[Metadatos del Remitente: JID={real_sender_id}]\nUsuario: {cleaned_text}"

        # ── 7. Llamar a Gemini (con media si existe) ───────────────────────────
        gemini_media = media_list if media_list else None
        print(f"[Processor] Llamando a Gemini para {real_sender_id}...{' (multimodal)' if gemini_media else ''}", flush=True)
        try:
            response_dict = await asyncio.wait_for(
                generate_response(
                    prompt_with_context, 
                    media=gemini_media, 
                    history=history_msgs,
                    payment_status=payment_status,
                    appointment_date=appointment_date,
                    session_mode=session_mode
                ),
                timeout=90.0  # Más tiempo para permitir Function Calling y media
            )
        except asyncio.TimeoutError:
            print(f"[Processor] Timeout: Gemini tardó demasiado para {real_sender_id}", flush=True)
            return

        reply = response_dict.get('reply', '')
        sentiment = response_dict.get('sentiment', 'Neutral')
        requires_human = response_dict.get('requires_human', False)
        print(f"[Processor] Gemini respondió ({len(reply)} chars)", flush=True)

        # Persistir respuesta del asistente
        if user_uuid:
            try:
                supabase.table('orus_messages').insert({
                    'user_id': user_uuid,
                    'role': 'assistant',
                    'content': reply,
                    'sentiment_flag': sentiment,
                    'requires_human': requires_human
                }).execute()
            except Exception as e:
                print(f"Error guardando respuesta: {e}", flush=True)

        # ── 8. Fragmentar y enviar ─────────────────────────────────────────────
        reply_clean = reply.replace("[##EOS##]", "").strip()

        if "[AGENDA_COMPLETA]" in reply_clean or "[AUDIO_ENVIADO]" in reply_clean or "[COBRO_ENVIADO]" in reply_clean or "[SILENT_FALLBACK]" in reply_clean:
            print("[Processor] Intercepción silenciosa de Gemini. Delegando envío visual al sistema.", flush=True)
            return

        raw_chunks = re.split(r'\|{2,}', reply_clean)
        clean_chunks = [chunk.strip() for chunk in raw_chunks if len(chunk.strip()) > 1]
        if not clean_chunks:
            clean_chunks = [reply_clean] if reply_clean else []

        for i, chunk in enumerate(clean_chunks):
            try:
                response = await wa_client.send_message(to=real_sender_id, text=chunk)
            except Exception as e:
                print(f"Error enviando fragmento {i+1}/{len(clean_chunks)}: {e}", flush=True)
                try:
                    supabase.table('orus_logs').insert({
                        'event_type': 'OUTBOUND_MESSAGE_ERROR',
                        'severity': 'ERROR',
                        'source_identifier': real_sender_id,
                        'error_message': f"Error enviando fragmento: {str(e)}",
                        'raw_payload': chunk[:500]
                    }).execute()
                except Exception as log_err:
                    print(f"Error escribiendo en logs: {log_err}", flush=True)

            # Pausa entre fragmentos para simular escritura natural
            if i < len(clean_chunks) - 1:
                delay = max(2, len(chunk) // 20)
                await asyncio.sleep(delay)

    except Exception as e:
        print(f"[Processor] Error crítico en pipeline: {e}", flush=True)
