import os
from supabase import create_client, Client

url: str = os.getenv("SUPABASE_URL", "")
key: str = os.getenv("SUPABASE_KEY", "")

if not url or not key:
    print("ADVERTENCIA: SUPABASE_URL o SUPABASE_KEY no están definidos en el entorno.")

# Inicialización Singleton del cliente de Supabase
supabase: Client = create_client(url, key)
