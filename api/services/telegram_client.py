import os
import httpx

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def send_telegram_alert(message: str):
    """
    Envía un mensaje asíncrono vía la API de Telegram al TELEGRAM_CHAT_ID.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[TELEGRAM ALERT] No configurado. Ignorando alerta.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            if response.status_code != 200:
                print(f"[TELEGRAM ERROR] Fallo al enviar alerta: {response.text}")
            else:
                print("[TELEGRAM] Alerta enviada con éxito.")
    except Exception as e:
        print(f"[TELEGRAM EXCEPTION] {e}")
