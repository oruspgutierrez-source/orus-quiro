from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from api.db.supabase_client import supabase
from api.dependencies import verify_api_key

router = APIRouter(prefix="/api/logs", tags=["Logs"], dependencies=[Depends(verify_api_key)])

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
