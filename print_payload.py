from dotenv import load_dotenv
load_dotenv()
from api.db.supabase_client import supabase
import json
res = supabase.table('orus_webhooks_buffer').select('*').order('created_at', desc=True).limit(1).execute()
payload = res.data[0]['payload']
with open('temp_payload_utf8.json', 'w', encoding='utf-8') as f:
    json.dump(payload, f, indent=2)
