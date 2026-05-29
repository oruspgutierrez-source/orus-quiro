import asyncio
from dotenv import load_dotenv
load_dotenv()
from api.db.supabase_client import supabase

res = supabase.table('orus_messages').select('*').order('created_at', desc=True).limit(10).execute()
for m in res.data:
    print(f"[{m['role']}] {m['content']}")
