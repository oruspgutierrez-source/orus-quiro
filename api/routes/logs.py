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
        import httpx
        import os
        
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        openrouter_model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
        
        prompt = f"""
Eres el ingeniero principal de infraestructura de Orus Quiro.
Se produjo un error en nuestro sistema. Necesito que le expliques al administrador qué significa y qué debe revisar de forma MUY breve, concisa y sin jerga técnica innecesaria (máximo 2 párrafos cortos). Sé elegante y directo.

Error Técnico:
{req.error_message}

Código / Stack trace:
{req.stack_trace or 'No disponible'}
"""
        headers = {
            "Authorization": f"Bearer {openrouter_key}",
            "HTTP-Referer": "https://api.orusquiroterapia.online",
            "X-Title": "Orus Quiroterapia Bot",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": openrouter_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500
        }
        
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            r = await http_client.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
            if r.status_code != 200:
                raise Exception(f"OpenRouter returned status {r.status_code}: {r.text}")
            res_data = r.json()
            analysis_text = res_data["choices"][0]["message"]["content"]
            
        return {"analysis": analysis_text}
    except Exception as e:
        print(f"Error analizando log con IA (OpenRouter): {e}")
        raise HTTPException(status_code=500, detail="Error al conectar con la IA de análisis.")

@router.delete("/{log_id}")
def delete_log(log_id: str):
    try:
        response = supabase.table('orus_logs').delete().eq('id', log_id).execute()
        return {"status": "success", "message": "Log eliminado/resuelto."}
    except Exception as e:
        print(f"Error eliminando log: {e}")
        raise HTTPException(status_code=500, detail="Error al eliminar el registro.")
