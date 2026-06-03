import os
import json
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
import stripe
from api.db.supabase_client import supabase
from api.services.telegram_client import send_telegram_alert
from api.services.wa_client import wa_client
from api.services.billing import generate_invoice_pdf, send_invoice_by_whatsapp

router = APIRouter(prefix="/payments", tags=["payments"])

# Inicializar clave de Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

def get_next_5_business_days() -> list[str]:
    """Calcula los siguientes 5 días hábiles (lunes a viernes) a partir de mañana.
    Retorna una lista de strings con formato 'YYYY-MM-DD'.
    """
    import datetime as dt
    days = []
    current = dt.date.today() + dt.timedelta(days=1)
    while len(days) < 5:
        # 0 = lunes, ..., 4 = viernes, 5 = sábado, 6 = domingo
        if current.weekday() < 5:
            days.append(current.strftime("%Y-%m-%d"))
        current += dt.timedelta(days=1)
    return days

async def process_successful_payment(session: dict):
    """
    Pipeline asíncrono para procesar el pago exitoso:
    1. Actualizar el estado del usuario en Supabase a 'paid'.
    2. Notificar al canal de Telegram (Auditoría).
    3. (En Tasks siguientes: Registrar en orus_payments, generar y enviar Factura PDF).
    """
    metadata = session.get("metadata", {})
    jid = metadata.get("jid")
    client_name = metadata.get("client_name", "Consultante")
    client_email = session.get("customer_details", {}).get("email") or metadata.get("client_email", "")
    
    amount_total = session.get("amount_total", 0) / 100.0
    currency = session.get("currency", "usd").upper()
    transaction_id = session.get("payment_intent") or session.get("id")

    print(f"[Payments Webhook] Procesando pago exitoso para JID={jid}, Monto={amount_total} {currency}, Transacción={transaction_id}", flush=True)

    if not jid:
        print("[Payments Webhook] Error: JID no encontrado en los metadatos de la sesión.", flush=True)
        return

    try:
        # 1. Actualizar Supabase (orus_users)
        # Buscar usuario por el número de teléfono (JID)
        user_res = supabase.table('orus_users').select('id').eq('phone_number', jid).execute()
        if user_res.data:
            user_id = user_res.data[0]['id']
            # Actualizar el estado de pago del usuario
            supabase.table('orus_users').update({
                'payment_status': 'paid'
            }).eq('id', user_id).execute()
            print(f"[Payments Webhook] Estado de pago del usuario {jid} actualizado a 'paid' en Supabase.", flush=True)
        else:
            # Fallback si el usuario no existía (raro, pero preventivo)
            new_user = supabase.table('orus_users').insert({
                'phone_number': jid,
                'payment_status': 'paid'
            }).execute()
            print(f"[Payments Webhook] Usuario {jid} no existía. Creado y marcado como 'paid'.", flush=True)

        # 2. Alerta de Auditoría en Telegram
        alert_msg = (
            f"💳 **¡NUEVO PAGO CONFIRMADO!** 💳\n\n"
            f"👤 **Consultante:** {client_name}\n"
            f"📞 **WhatsApp:** {jid}\n"
            f"📧 **Correo:** {client_email or 'No proporcionado'}\n"
            f"💰 **Monto:** {amount_total:.2f} {currency}\n"
            f"🆔 **ID Transacción:** {transaction_id}\n"
            f"✅ **Estado:** Completado"
        )
        await send_telegram_alert(alert_msg)
        print("[Payments Webhook] Alerta de Telegram despachada exitosamente.", flush=True)

        # 4. Generar y enviar Factura Simplificada en PDF de manera robusta
        try:
            print(f"[Payments Webhook] Generando factura PDF para {client_name}...", flush=True)
            pdf_path = generate_invoice_pdf(
                transaction_id=transaction_id,
                client_name=client_name,
                client_email=client_email,
                amount=amount_total,
                currency=currency
            )
            print(f"[Payments Webhook] Enviando factura PDF a JID={jid}...", flush=True)
            await send_invoice_by_whatsapp(
                jid=jid,
                pdf_path=pdf_path,
                client_name=client_name,
                transaction_id=transaction_id
            )
            print("[Payments Webhook] Factura PDF enviada exitosamente por WhatsApp.", flush=True)
        except Exception as billing_err:
            print(f"[Payments Webhook] Error no bloqueante en el pipeline de facturación: {billing_err}", flush=True)
            try:
                supabase.table('orus_logs').insert({
                    'event_type': 'BILLING_PIPELINE_ERROR',
                    'source_identifier': jid,
                    'error_message': f"Error en facturación asíncrona para pago {transaction_id}: {str(billing_err)}"
                }).execute()
            except Exception as db_log_err:
                print(f"Error escribiendo log de facturación en Supabase: {db_log_err}", flush=True)

        # 5. Activar proactivamente el Flujo de Agendamiento (Spec 13)
        # Gemini recibe un trigger interno post-pago para iniciar el protocolo
        # sin esperar a que el consultante escriba un nuevo mensaje.
        try:
            from api.services.gemini_client import generate_response
            from api.services.calendar_client import get_free_slots_data, BUSINESS_HOURS, format_availability_table
            import re
            import datetime as dt

            # 5.1. Calcular disponibilidad de los siguientes 5 días hábiles en el servidor
            next_days = get_next_5_business_days()
            slots_per_day = {}

            for day_str in next_days:
                free_slots = get_free_slots_data(day_str)
                slots_per_day[day_str] = sorted(free_slots)
            
            availability_str = format_availability_table(next_days, slots_per_day)
            print(f"[Payments Webhook] Disponibilidad estructurada precalculada:\n{availability_str}", flush=True)

            # Recuperar historial reciente del consultante para mantener contexto
            history_msgs = []
            try:
                user_res_hist = supabase.table('orus_users').select('id').eq('phone_number', jid).execute()
                if user_res_hist.data:
                    user_id_hist = user_res_hist.data[0]['id']
                    hist = supabase.table('orus_messages').select('role, content').eq('user_id', user_id_hist).order('created_at', desc=True).limit(6).execute()
                    if hist.data:
                        for msg in reversed(hist.data):
                            gemini_role = "model" if msg['role'] == 'assistant' else "user"
                            history_msgs.append({"role": gemini_role, "text": msg['content']})
            except Exception as hist_err:
                print(f"[Payments Webhook] Error cargando historial para agendamiento: {hist_err}", flush=True)

            # Prompt de trigger interno: informa a Gemini que el pago se completó
            # y le inyecta directamente la disponibilidad precalculada del servidor.
            trigger_prompt = (
                f"[Metadatos del Remitente: JID={jid}]\n"
                f"[SISTEMA — EVENTO INTERNO]: El pago de {client_name} por {amount_total:.2f} {currency} "
                f"fue confirmado exitosamente por Stripe (ID: {transaction_id}). "
                f"La factura PDF ya fue enviada y el cliente notificado.\n\n"
                f"INFORME DE DISPONIBILIDAD OBTENIDO DIRECTAMENTE DEL SERVIDOR:\n"
                f"{availability_str}\n\n"
                f"INSTRUCCIONES CLÍNICAS OBLIGATORIAS:\n"
                f"1. DEBES presentarle directamente estos horarios al consultante de forma estructurada para agendar su primera sesión (el Mapeo).\n"
                f"2. NO debes saludar, felicitar, agradecer ni hacer mención alguna al pago o la factura. El cliente ya vio y recibió el PDF de la factura, y tu pie de factura ya hizo la transición.\n"
                f"3. Tu mensaje debe comenzar directamente con la propuesta clínica en el tono sobrio de El Escultor, ofreciendo estos días y horas específicos de forma limpia y directa.\n"
                f"4. NO invoques ninguna herramienta como check_free_slots() ni book_appointment() en esta respuesta, ya que la información de disponibilidad ha sido precalculada e inyectada por el servidor. Simplemente presenta las opciones al usuario y espera su elección.\n"
                f"5. CRÍTICO: Presenta TODAS las fechas y horarios disponibles juntos en UN SOLO BLOQUE de texto. NO dividas los días usando barras (|||). Las barras (|||) solo deben usarse si el mensaje en su totalidad es extremadamente largo, pero la lista de horarios COMPLETA debe ir en el mismo fragmento."
            )

            print(f"[Payments Webhook] Activando flujo de agendamiento proactivo para {jid}...", flush=True)
            sched_response = await generate_response(
                prompt=trigger_prompt,
                history=history_msgs
            )

            sched_reply = sched_response.get('reply', '')
            if sched_reply:
                reply_clean = sched_reply.replace("[##EOS##]", "").strip()
                chunks = [c.strip() for c in re.split(r'\|{2,}', reply_clean) if len(c.strip()) > 1]
                if not chunks:
                    chunks = [reply_clean] if reply_clean else []

                for i, chunk in enumerate(chunks):
                    await wa_client.send_message(to=jid, text=chunk)
                    print(f"[Payments Webhook] Fragmento agendamiento {i+1}/{len(chunks)} enviado a {jid}.", flush=True)
                    if i < len(chunks) - 1:
                        import asyncio
                        await asyncio.sleep(max(2, len(chunk) // 20))

            print("[Payments Webhook] Flujo de agendamiento proactivo completado.", flush=True)

        except Exception as sched_err:
            safe_err = str(sched_err).encode('ascii', 'replace').decode('ascii')
            print(f"[Payments Webhook] Error no bloqueante en el flujo de agendamiento: {safe_err}", flush=True)

    except Exception as e:
        print(f"[Payments Webhook] Error crítico en process_successful_payment: {e}", flush=True)
        # Registrar error en orus_logs
        try:
            supabase.table('orus_logs').insert({
                'event_type': 'PAYMENT_PROCESSING_ERROR',
                'source_identifier': jid or "unknown",
                'error_message': f"Error procesando pago {transaction_id}: {str(e)}"
            }).execute()
        except Exception as log_err:
            print(f"Error escribiendo en logs de Supabase: {log_err}", flush=True)

@router.post("/webhook")
async def receive_stripe_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint que escucha los webhooks de Stripe.
    Valida la firma criptográfica y enruta el evento de manera asíncrona.
    """
    sig_header = request.headers.get("stripe-signature")
    if not sig_header:
        print("[Payments Webhook] Error: Cabecera stripe-signature ausente.", flush=True)
        raise HTTPException(status_code=400, detail="Falta cabecera stripe-signature")

    try:
        payload = await request.body()
    except Exception as e:
        print(f"[Payments Webhook] Error leyendo el cuerpo del request: {e}", flush=True)
        raise HTTPException(status_code=400, detail="Cuerpo de petición inválido")

    # 1. Validar la autenticidad del webhook
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Payload inválido
        print(f"[Payments Webhook] Error de formato en payload: {e}", flush=True)
        raise HTTPException(status_code=400, detail="Formato de payload inválido")
    except stripe.SignatureVerificationError as e:
        # Firma inválida
        print(f"[Payments Webhook] Error de firma criptográfica: {e}", flush=True)
        raise HTTPException(status_code=400, detail="Firma de webhook inválida")
    except Exception as e:
        print(f"[Payments Webhook] Error de validación inesperado: {e}", flush=True)
        raise HTTPException(status_code=400, detail=f"Error validando webhook: {str(e)}")

    # Convertir el objeto Stripe a un diccionario nativo de Python para evitar incompatibilidades de métodos
    event_dict = event.to_dict()
    event_type = event_dict.get("type")
    print(f"[Payments Webhook] Evento recibido desde Stripe: {event_type}", flush=True)

    # 2. Enrutar el evento
    if event_type == "checkout.session.completed":
        session = event_dict.get("data", {}).get("object", {})
        # Enrutar el procesamiento pesado a un proceso de background
        background_tasks.add_task(process_successful_payment, session)
        return {"status": "processing", "message": "checkout.session.completed enrutado a background"}

    return {"status": "ignored", "message": f"Evento {event_type} no requiere procesamiento"}
