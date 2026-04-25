import asyncio
from api.services.gemini_client import generate_response
from api.services.meta_client import send_humanized_response
from api.services.telegram_client import send_telegram_alert
from api.db.supabase_client import supabase

# Diccionario global para manejar el estado en memoria de los mensajes encolados
active_sessions = {}

async def process_debounced_messages(sender_id: str):
    """
    Duerme por 7 segundos, luego recolecta todos los mensajes de este sender_id,
    gestiona la base de datos, envía a Gemini y responde.
    """
    print(f"[ORCHESTRATOR] Task sleep iniciada para {sender_id}...")
    await asyncio.sleep(7)
    
    # Extraer mensajes y limpiar del diccionario para permitir nuevas sesiones
    session = active_sessions.pop(sender_id, None)
    if not session:
        return
        
    messages = session.get("messages", [])
    if not messages:
        return
        
    # Unir mensajes con un salto de línea
    joined_text = "\n".join(messages)
    print(f"\n[ORCHESTRATOR] Procesando bloque unificado para {sender_id}: \n{joined_text}\n", flush=True)
    
    try:
        # 1. Buscar/Crea Usuario
        user_res = supabase.table('orus_users').select('*').eq('phone_number', sender_id).execute()
        
        if not user_res.data:
            new_user = supabase.table('orus_users').insert({'phone_number': sender_id}).execute()
            user_data = new_user.data[0]
        else:
            user_data = user_res.data[0]
            
        user_id = user_data['id']
        session_mode = user_data.get('session_mode', 'AI')
        admin_notified = user_data.get('admin_notified', False)

        # Si el humano ya tomó el control, por ahora solo logueamos (opcional: la IA no responde)
        if session_mode == 'HUMAN':
            print(f"[ORCHESTRATOR] Sesión en modo HUMAN para {sender_id}. La IA no responderá.")
            # Opcional: podríamos guardar el mensaje en db y retornar
            # supabase.table('orus_messages').insert({...})
            # return

        # 2. Gemini (JSON)
        response_dict = await generate_response(joined_text)
        reply = response_dict.get('reply', '')
        sentiment = response_dict.get('sentiment', 'Neutral')
        requires_human = response_dict.get('requires_human', False)

        # 3. Alerta y Cambio de Estado
        if requires_human:
            print(f"[ORCHESTRATOR] FLAG requires_human detectada para {sender_id}. Sentimiento: {sentiment}")
            if not admin_notified:
                await send_telegram_alert(f"⚠️ Atención Requerida.\nUsuario: {sender_id}\nSentimiento: {sentiment}\nMensaje: {joined_text}")
                supabase.table('orus_users').update({'session_mode': 'HUMAN', 'admin_notified': True}).eq('id', user_id).execute()
                print("[ORCHESTRATOR] Usuario pasado a modo HUMAN.")

        # 4. Guardar en DB
        # Guardar mensaje del usuario
        supabase.table('orus_messages').insert({
            'user_id': user_id,
            'role': 'user',
            'content': joined_text,
            'sentiment_flag': sentiment,
            'requires_human': requires_human
        }).execute()

        # Guardar respuesta de la IA
        supabase.table('orus_messages').insert({
            'user_id': user_id,
            'role': 'assistant',
            'content': reply,
            'sentiment_flag': None,
            'requires_human': False
        }).execute()

        # Actualizar last_interaction
        supabase.table('orus_users').update({'last_interaction': 'now()'}).eq('id', user_id).execute()

        # 5. Enviar por Meta si no estamos en modo humano puro (o si recién mutó, enviamos esta respuesta como despedida)
        await send_humanized_response(sender_id, reply)

    except Exception as e:
        print(f"\n[ERROR ORCHESTRATOR para {sender_id}]: {e}\n", flush=True)

def enqueue_message(sender_id: str, message_text: str):
    """
    Agrega un mensaje a la cola del sender_id.
    Si es el primer mensaje, lanza la tarea en segundo plano.
    """
    if sender_id in active_sessions:
        active_sessions[sender_id]["messages"].append(message_text)
        print(f"[ORCHESTRATOR] Añadido al buffer existente: '{message_text}'")
    else:
        active_sessions[sender_id] = {"messages": [message_text]}
        print(f"[ORCHESTRATOR] Nuevo buffer iniciado para {sender_id}: '{message_text}'")
        task = asyncio.create_task(process_debounced_messages(sender_id))
        active_sessions[sender_id]["task"] = task
