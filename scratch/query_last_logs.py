import asyncio
from dotenv import load_dotenv
load_dotenv()
from api.db.supabase_client import supabase

print("--- ÚLTIMOS MENSAJES ---")
try:
    res_msg = supabase.table('orus_messages').select('*').order('created_at', desc=True).limit(15).execute()
    for m in reversed(res_msg.data):
        print(f"[{m.get('created_at')}] [{m.get('role')}] {m.get('content')}")
        print(f"    Sentiment: {m.get('sentiment_flag')} | ReqHuman: {m.get('requires_human')}")
except Exception as e:
    print(f"Error consultando mensajes: {e}")

print("\n--- ÚLTIMOS LOGS ---")
try:
    res_logs = supabase.table('orus_logs').select('*').order('created_at', desc=True).limit(20).execute()
    for l in reversed(res_logs.data):
        print(f"[{l.get('created_at')}] [{l.get('event_type')}] Source: {l.get('source_identifier')}")
        print(f"    Payload/Message ID: {l.get('raw_payload')}")
        print(f"    Content/Error: {l.get('error_message')}")
except Exception as e:
    print(f"Error consultando logs: {e}")
