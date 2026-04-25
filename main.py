from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Cargar variables de entorno antes de importar modulos que dependan de ellas
load_dotenv()

from api.routes import webhooks, health, llm_test, dashboard

app = FastAPI(title="Orus Quiro API", description="API para el Agente de Quiromancia Védica")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhooks.router)
app.include_router(health.router)
app.include_router(llm_test.router)
app.include_router(dashboard.router)

@app.get("/")
def root():
    return {"message": "Servidor base activo"}
