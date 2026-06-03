import os
from fastapi import Header, HTTPException, status

def verify_api_key(x_api_key: str = Header(..., description="API Key para proteger rutas sensibles del Dashboard")):
    expected_key = os.getenv("API_SECRET_KEY")
    if not expected_key:
        # Si no está configurada, bloquear por seguridad
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API_SECRET_KEY no configurada en el servidor"
        )
    if x_api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida"
        )
    return x_api_key
