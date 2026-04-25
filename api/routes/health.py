from fastapi import APIRouter, HTTPException
from api.db.supabase_client import supabase

router = APIRouter()

@router.get("/health/db")
async def health_check_db():
    try:
        # Ejecutamos una operación inocua para validar que la conexión de red hacia Supabase es exitosa
        supabase.table("health_check_dummy").select("*").limit(1).execute()
    except Exception as e:
        error_msg = str(e)
        # Si el motor de Postgrest responde que no existe la tabla, significa que la API y red están operativas.
        if "does not exist" in error_msg or "APIError" in str(type(e)):
            return {"status": "connected", "message": "Supabase integration operational"}
        # Cualquier otro error (como ConnectError o Invalid Key) lo tratamos como fallo
        raise HTTPException(status_code=500, detail=f"Database connection failed: {error_msg}")
    
    return {"status": "connected", "message": "Supabase integration operational"}
