from dotenv import load_dotenv
load_dotenv()
from api.db.supabase_client import supabase

users = supabase.table('orus_users').select('id, phone_number').execute()
for u in users.data:
    phone = u['phone_number']
    uid = u['id']
    print(f'\n=== USER: {phone} ===')
    msgs = supabase.table('orus_messages').select('role, content, created_at').eq('user_id', uid).order('created_at').execute()
    for m in msgs.data:
        role = m['role'].upper()
        ts = m['created_at'][11:16]
        content = m['content'][:500].replace('\n', ' ')
        print(f'[{ts}] {role}: {content}')
        print('---')
