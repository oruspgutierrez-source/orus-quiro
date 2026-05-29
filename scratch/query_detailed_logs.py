import asyncio
from dotenv import load_dotenv
load_dotenv()
from api.db.supabase_client import supabase

print("--- DETALLE DE LOGS (ÚLTIMOS 50) ---")
try:
    res = supabase.table('orus_logs').select('*').order('created_at', desc=True).limit(50).execute()
    for l in reversed(res.data):
        print(f"[{l.get('created_at')}] [{l.get('event_type')}] Source: {l.get('source_identifier')}")
        print(f"    Payload: {l.get('raw_payload')}")
        print(f"    Error/Message: {l.get('error_message')}")
        print("-" * 50)
except Exception as e:
    print(f"Error consultando logs detallados: {e}")
