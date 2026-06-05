import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(url, key)

try:
    print("Intentando subir archivo de prueba de audio...")
    res = supabase.storage.from_("biometria_test").upload(
        path="inbox_media/test_upload.mp3",
        file=b"test",
        file_options={"content-type": "audio/mp3"}
    )
    print("Subida exitosa:", res)
    
except Exception as e:
    print("Error mp3:", e)

try:
    print("Intentando subir archivo de prueba de documento...")
    res = supabase.storage.from_("biometria_test").upload(
        path="inbox_media/test_upload.pdf",
        file=b"test",
        file_options={"content-type": "application/pdf"}
    )
    print("Subida exitosa pdf:", res)
    
except Exception as e:
    print("Error pdf:", e)
