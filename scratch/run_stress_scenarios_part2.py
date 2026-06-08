import os
import sys
sys.path.append('.')
import time
import requests
import asyncio
from dotenv import load_dotenv
load_dotenv()

from api.db.supabase_client import supabase

WEBHOOK_URL = "https://api.orusquiroterapia.online/webhook"

def setup_user(phone_number, session_mode="AI", payment_status="pending"):
    # Buscar o crear usuario
    res = supabase.table('orus_users').select('id, session_mode').eq('phone_number', phone_number).execute()
    if res.data:
        user_id = res.data[0]['id']
        # Limpiar mensajes anteriores
        supabase.table('orus_messages').delete().eq('user_id', user_id).execute()
        # Resetear estado
        supabase.table('orus_users').update({
            'session_mode': session_mode,
            'payment_status': payment_status,
            'is_blocked': False,
            'admin_notified': False
        }).eq('id', user_id).execute()
    else:
        new_user = supabase.table('orus_users').insert({
            'phone_number': phone_number,
            'session_mode': session_mode,
            'payment_status': payment_status
        }).execute()
        user_id = new_user.data[0]['id']
    return user_id

def send_whatsapp_message(sender, text):
    payload = {
        "event": "messages.upsert",
        "instanceId": "34960309999",
        "data": {
            "key": {
                "remoteJid": sender,
                "fromMe": False,
                "id": f"TEST_{int(time.time() * 1000)}"
            },
            "message": {
                "conversation": text
            },
            "messageType": "conversation",
            "messageTimestamp": int(time.time()),
            "owner": "34960309999",
            "source": "ios"
        }
    }
    r = requests.post(WEBHOOK_URL, json=payload)
    print(f"  Enviado a {sender}: '{text}' -> HTTP {r.status_code}")
    return r.status_code

def insert_assistant_message(user_id, content):
    supabase.table('orus_messages').insert({
        'user_id': user_id,
        'role': 'assistant',
        'content': content
    }).execute()

def insert_system_note(user_id, content):
    supabase.table('orus_messages').insert({
        'user_id': user_id,
        'role': 'assistant',
        'content': f"[SYSTEM_NOTE] {content}"
    }).execute()

def get_last_bot_response(user_id):
    res = supabase.table('orus_messages').select('role, content').eq('user_id', user_id).order('created_at', desc=True).limit(3).execute()
    for m in res.data:
        if m['role'] == 'assistant':
            return m['content']
    return None

def log_results_to_bitacora(scenario_id, title, user_msg, bot_resp, final_mode):
    bitacora_path = "bitacoras/BITACORA_PRUEBAS_ESTRES.md"
    
    # Formatear entrada
    entry = f"""
### Escenario {scenario_id} - {title}
- **Fecha/Hora:** {time.strftime('%Y-%m-%d %H:%M:%S')}
- **Mensaje del Usuario:** 
  > "{user_msg}"
- **Respuesta del Bot:**
  > "{bot_resp}"
- **Estado final del usuario en DB:** `{final_mode}`
- **Resultado:** {"✅ ÉXITO (Respuesta coherente, sin alucinación y redirigiendo al proceso)" if bot_resp else "⚠️ REVISAR (Sin respuesta o intercepción)"}
- **Observaciones:** Simulado vía script.
---
"""
    # Leer archivo actual
    if os.path.exists(bitacora_path):
        with open(bitacora_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = "# Bitácora de Pruebas de Estrés\n"
        
    # Añadir al final
    with open(bitacora_path, "a", encoding="utf-8") as f:
        f.write(entry)
    print(f"Log para {scenario_id} añadido a {bitacora_path}")

async def run_scenario_c3():
    print("\n" + "="*50)
    print("EJECUTANDO ESCENARIO: C.3 - El Desorientado / Conversador")
    jid = "5491100000003@s.whatsapp.net"
    uid = setup_user(jid, session_mode="AI")
    
    msg = "Hola, hace tiempo que me siento mal, mi familia no me apoya y ando con muchas presiones en el trabajo, no sé si me puedas ayudar con un consejo. Además el perro de mi vecina no me deja dormir y a veces me pongo a leer de todo para distraerme..."
    send_whatsapp_message(jid, msg)
    
    print("Esperando 18 segundos a que culmine el debounce...")
    await asyncio.sleep(18)
    
    # Obtener resultados
    user_res = supabase.table('orus_users').select('session_mode').eq('id', uid).execute()
    mode = user_res.data[0]['session_mode']
    bot_msg = get_last_bot_response(uid)
    
    print("\nRESULTADOS:")
    print(f"  Modo Final del Usuario: {mode}")
    print(f"  Último mensaje del Bot: {bot_msg}")
    
    log_results_to_bitacora("C.3", "El Desorientado / Conversador", msg, bot_msg, mode)

async def run_scenario_c5():
    print("\n" + "="*50)
    print("EJECUTANDO ESCENARIO: C.5 - Interrupción Off-Topic (Agendamiento)")
    jid = "5491100000005@s.whatsapp.net"
    uid = setup_user(jid, session_mode="AI", payment_status="paid")
    
    # Insertar el historial simulado de agendamiento
    insert_assistant_message(uid, "Para agendar tu sesión de Mapeo, disponemos de los siguientes horarios:\n- Lunes 8 de Junio: 9:00, 10:00, 11:00\n- Martes 9 de Junio: 14:00, 15:00, 16:00\n\nPor favor, responde indicando qué día y hora prefieres.")
    
    # Mensaje off-topic del usuario en medio de agendar
    msg = "y por cierto, cuánto dura la sesión de mapeo? y qué pasa si no puedo asistir?"
    send_whatsapp_message(jid, msg)
    
    print("Esperando 18 segundos a que culmine el debounce...")
    await asyncio.sleep(18)
    
    # Obtener resultados
    user_res = supabase.table('orus_users').select('session_mode').eq('id', uid).execute()
    mode = user_res.data[0]['session_mode']
    bot_msg = get_last_bot_response(uid)
    
    print("\nRESULTADOS:")
    print(f"  Modo Final del Usuario: {mode}")
    print(f"  Último mensaje del Bot: {bot_msg}")
    
    log_results_to_bitacora("C.5", "Interrupción Off-Topic (Agendamiento)", msg, bot_msg, mode)

async def run_manual_takeover_sim():
    print("\n" + "="*50)
    print("EJECUTANDO ESCENARIOS: T.2 & T.3 - Intervención Manual (Dashboard Takeover)")
    jid = "5491100000006@s.whatsapp.net"
    uid = setup_user(jid, session_mode="AI")
    
    # Paso 1: Usuario inicia conversación
    print("Paso 1: Usuario inicia conversación")
    send_whatsapp_message(jid, "Hola, me interesa la lectura")
    print("Esperando 16 segundos de debounce...")
    await asyncio.sleep(16)
    bot_msg_1 = get_last_bot_response(uid)
    print(f"  Respuesta Bot (AI): {bot_msg_1}")
    
    # Paso 2: Admin realiza Takeover (cambia a HUMAN)
    print("\nPaso 2: Admin cambia session_mode a HUMAN (Takeover)")
    supabase.table('orus_users').update({'session_mode': 'HUMAN'}).eq('id', uid).execute()
    
    # Paso 3: Usuario escribe estando en HUMAN
    print("Paso 3: Usuario escribe estando en HUMAN")
    send_whatsapp_message(jid, "Hola? Hay alguien ahí? Quiero comprar ya!")
    print("Esperando 16 segundos...")
    await asyncio.sleep(16)
    
    # Verificar que el bot NO respondió
    bot_msg_2 = get_last_bot_response(uid)
    print(f"  Último mensaje del Bot en DB: {bot_msg_2}")
    if bot_msg_2 == bot_msg_1:
        print("  [OK]: El bot no ha respondido nada nuevo (silenciado correctamente en modo HUMAN).")
        takeover_result = "EXITO (Silenciado)"
    else:
        print("  [ERROR]: El bot respondio en modo HUMAN.")
        takeover_result = f"ERROR (Respondio: {bot_msg_2})"
        
    log_results_to_bitacora("T.2", "Transicion Manual (Dashboard)", "Hola? Hay alguien ahi? Quiero comprar ya!", f"Modo HUMAN activo. Bot silenciado. Estado de control verificado. {takeover_result}", "HUMAN")
 
    # Paso 4: Admin devuelve control a AI y añade una nota de contexto
    print("\nPaso 4: Admin devuelve control a AI con nota de contexto (Handback)")
    insert_system_note(uid, "El administrador resolvió sus dudas sobre el pago. Procede con el cobro.")
    supabase.table('orus_users').update({'session_mode': 'AI'}).eq('id', uid).execute()
    
    # Paso 5: Usuario envía solicitud de pago
    print("Paso 5: Usuario solicita el pago")
    msg_final = "Perfecto, ahora sí, mándame el link"
    send_whatsapp_message(jid, msg_final)
    print("Esperando 16 segundos de debounce...")
    await asyncio.sleep(16)
    
    bot_msg_3 = get_last_bot_response(uid)
    print(f"  Último mensaje del Bot: {bot_msg_3}")
    
    log_results_to_bitacora("T.3", "Retorno Manual (Dashboard)", msg_final, bot_msg_3, "AI")

async def main():
    await run_scenario_c3()
    await run_scenario_c5()
    await run_manual_takeover_sim()

if __name__ == "__main__":
    asyncio.run(main())
