from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.db.supabase_client import supabase

router = APIRouter(prefix="/api/metrics", tags=["Metrics"])

@router.get("/bot_vs_human")
def get_bot_vs_human_metrics():
    try:
        response = supabase.table('orus_users').select('session_mode').execute()
        users = response.data
        total = len(users)
        if total == 0:
            return {"total_users": 0, "ai_managed": 0, "human_managed": 0, "human_intervention_rate": "0.0%"}
        
        ai_count = sum(1 for u in users if u.get('session_mode') == 'AI')
        human_count = total - ai_count
        
        return {
            "total_users": total,
            "ai_managed": ai_count,
            "human_managed": human_count,
            "human_intervention_rate": f"{(human_count / total) * 100:.1f}%"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversion")
def get_conversion_metrics():
    try:
        response = supabase.table('orus_users').select('payment_status, total_spent').execute()
        users = response.data
        total = len(users)
        if total == 0:
            return {"total_users": 0, "paid_users": 0, "total_revenue": 0.0, "conversion_rate": "0.0%"}
        
        paid_count = sum(1 for u in users if u.get('payment_status') == 'pagado')
        total_revenue = sum(float(u.get('total_spent', 0)) for u in users)
        
        return {
            "total_users": total,
            "paid_users": paid_count,
            "total_revenue": total_revenue,
            "conversion_rate": f"{(paid_count / total) * 100:.1f}%"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/appointments_weekly")
def get_weekly_appointments():
    """Total de citas por semana (usuarios con appointment_date no nulo)"""
    try:
        response = supabase.table('orus_users').select('appointment_date').not_('appointment_date', 'is', 'null').execute()
        return {"total_appointments": len(response.data), "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users_retention")
def get_users_retention():
    """Usuarios nuevos vs. recurrentes"""
    try:
        response = supabase.table('orus_users').select('payment_status, total_spent').execute()
        total = len(response.data)
        new_users = sum(1 for u in response.data if float(u.get('total_spent') or 0) == 0)
        recurrent_users = total - new_users
        return {"total": total, "new": new_users, "recurrent": recurrent_users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/error_rate")
def get_error_rate():
    """Tasa de error basada en los logs del sistema"""
    try:
        logs_res = supabase.table('orus_logs').select('severity').execute()
        total_logs = len(logs_res.data)
        if total_logs == 0:
            return {"error_rate": "0.0%", "total_errors": 0}
        
        errors = sum(1 for log in logs_res.data if log.get('severity') == 'ERROR')
        return {
            "total_logs": total_logs,
            "total_errors": errors,
            "error_rate": f"{(errors / total_logs) * 100:.1f}%"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
