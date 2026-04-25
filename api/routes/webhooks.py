import os
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
from api.services.orchestrator import enqueue_message

router = APIRouter()

@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: int = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """
    Endpoint para que Meta (WhatsApp/Instagram) verifique el webhook.
    """
    verify_token = os.getenv("META_VERIFY_TOKEN")
    
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        # Devuelve el challenge tal cual lo solicita Meta
        return int(hub_challenge)
    
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def receive_webhook(request: Request):
    """
    Endpoint para recibir eventos de Meta.
    Siempre retorna 200 OK inmediatamente.
    """
    # Extraemos el payload JSON
    payload = await request.json()
    
    try:
        # Navegar estructura de Webhooks de WhatsApp Cloud API
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                if "messages" in value:
                    for message in value["messages"]:
                        sender_id = message.get("from")
                        # Extraer el texto si es de tipo texto
                        text_body = message.get("text", {}).get("body") if message.get("type") == "text" else None
                        
                        if sender_id and text_body:
                            # Lanzar la operación de memoria de forma no bloqueante
                            enqueue_message(sender_id, text_body)
    except Exception as e:
        print(f"Error parseando payload de Meta: {e}")
        # Retornar 200 de todos modos para que Meta no reintente con payloads fallidos
        
    return {"status": "ok"}
