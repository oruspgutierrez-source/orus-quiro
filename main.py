from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Cargar variables de entorno antes de importar modulos que dependan de ellas
load_dotenv()

from api.routes import webhooks, health, llm_test, dashboard, metrics, payments

app = FastAPI(
    title="Orus Quiro API",
    description="API para el Agente de Quiromancia Védica"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# (Middleware de Meta removido a favor de API No Oficial)

from fastapi import Request
from fastapi.responses import JSONResponse
import traceback

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = str(exc)
    stack = traceback.format_exc()
    try:
        from api.db.supabase_client import supabase
        supabase.table('orus_logs').insert({
            'error_message': error_msg,
            'stack_trace': stack,
            'severity': 'ERROR'
        }).execute()
    except Exception as db_exc:
        print(f"Error guardando log: {db_exc}")
        
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error occurred."}
    )

app.include_router(webhooks.router)
app.include_router(health.router)
app.include_router(llm_test.router)
app.include_router(dashboard.router)
app.include_router(metrics.router)
app.include_router(payments.router)

@app.get("/")
def root():
    return {"message": "Servidor base activo"}
