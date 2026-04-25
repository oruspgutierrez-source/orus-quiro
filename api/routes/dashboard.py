from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.db.supabase_client import supabase
from api.services.meta_client import send_humanized_response

router = APIRouter(prefix="/api/users", tags=["Dashboard"])

class ManualMessage(BaseModel):
    message: str

@router.get("/human_mode")
def get_users_in_human_mode():
    """Devuelve la lista de usuarios que tienen session_mode == 'HUMAN'"""
    try:
        response = supabase.table('orus_users').select('*').eq('session_mode', 'HUMAN').execute()
        return {"data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/history")
def get_user_history(user_id: str):
    """Devuelve todo el historial de orus_messages de un cliente específico, ordenado por fecha."""
    try:
        response = supabase.table('orus_messages').select('*').eq('user_id', user_id).order('created_at', desc=False).execute()
        return {"data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}/resolve")
def resolve_human_session(user_id: str):
    """Cambia el session_mode de vuelta a 'AI' y admin_notified a False."""
    try:
        response = supabase.table('orus_users').update({
            'session_mode': 'AI',
            'admin_notified': False
        }).eq('id', user_id).execute()
        return {"status": "success", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}/send_manual_message")
async def send_manual_message(user_id: str, payload: ManualMessage):
    """El humano escribe un mensaje, se guarda en la DB y se envía al cliente."""
    try:
        # Recuperar el teléfono del usuario para enviarlo por Meta
        user_res = supabase.table('orus_users').select('phone_number').eq('id', user_id).execute()
        if not user_res.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        phone_number = user_res.data[0]['phone_number']

        # Guardar en DB
        supabase.table('orus_messages').insert({
            'user_id': user_id,
            'role': 'assistant',
            'content': payload.message,
            'requires_human': False
        }).execute()
        
        # Enviar vía Meta Client
        await send_humanized_response(phone_number, payload.message)
        
        return {"status": "success", "message": "Mensaje enviado correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
