import requests, time
from dotenv import load_dotenv; load_dotenv()
from api.db.supabase_client import supabase
jid = '553798433269@s.whatsapp.net'
u = supabase.table('orus_users').select('id').eq('phone_number', jid).execute()
if u.data:
    uid = u.data[0]['id']
    supabase.table('orus_messages').delete().eq('user_id', uid).execute()
    supabase.table('orus_users').update({'payment_status': 'pending', 'appointment_date': None, 'session_mode': 'AI', 'admin_notified': False, 'total_spent': 0.0}).eq('id', uid).execute()
    print('Reset OK')
url = 'http://127.0.0.1:8000/webhook'
payload = {'event': 'messages.upsert', 'data': {'key': {'remoteJid': jid, 'fromMe': False, 'id': str(time.time())}, 'message': {'conversation': 'Hola, quiero agendar'}}}
r = requests.post(url, json=payload)
print('Enviado. Status:', r.status_code)
