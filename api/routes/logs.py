from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from pydantic import BaseModel
from api.db.supabase_client import supabase
from api.dependencies import verify_api_key

router = APIRouter(prefix="/api/logs", tags=["Logs"], dependencies=[Depends(verify_api_key)])

class LogAnalyzeRequest(BaseModel):
    error_message: str
    stack_trace: Optional[str] = None

@router.get("/")
def get_logs(
    severity: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100)
):
    try:
        # Calcular paginación
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit - 1

        # Construir consulta
        query = supabase.table('orus_logs').select('*', count='exact')
        
        if severity and severity.upper() not in ['ALL', 'TODAS LAS SEVERIDADES']:
            query = query.eq('severity', severity.upper())
            
        # Ejecutar consulta con orden y paginación
        response = query.order('created_at', desc=True).range(start_idx, end_idx).execute()
        
        total_count = response.count if response.count is not None else 0
        total_pages = (total_count + limit - 1) // limit

        return {
            "data": response.data,
            "total": total_count,
            "page": page,
            "pages": total_pages
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze_log(req: LogAnalyzeRequest):
    try:
        from google import genai
        import os
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        prompt = f"""
Eres el ingeniero principal de infraestructura de Orus Quiro.
Se produjo un error en nuestro sistema. Necesito que le expliques al administrador qué significa y qué debe revisar de forma MUY breve, concisa y sin jerga técnica innecesaria (máximo 2 párrafos cortos). Sé elegante y directo.

Error Técnico:
{req.error_message}

Código / Stack trace:
{req.stack_trace or 'No disponible'}
"""
        response = await client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return {"analysis": response.text}
    except Exception as e:
        print(f"Error analizando log con IA: {e}")
        raise HTTPException(status_code=500, detail="Error al conectar con la IA de análisis.")

@router.delete("/{log_id}")
def delete_log(log_id: str):
    try:
        response = supabase.table('orus_logs').delete().eq('id', log_id).execute()
        return {"status": "success", "message": "Log eliminado/resuelto."}
    except Exception as e:
        print(f"Error eliminando log: {e}")
        raise HTTPException(status_code=500, detail="Error al eliminar el registro.")
