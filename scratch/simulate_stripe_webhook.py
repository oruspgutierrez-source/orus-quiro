import os
import time
import hmac
import hashlib
import json
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def simulate_webhook():
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if not webhook_secret:
        print("[ERROR] STRIPE_WEBHOOK_SECRET no está configurada en el .env")
        return

    print("=== SIMULADOR DE WEBHOOK DE STRIPE ===")
    
    # 1. Construir el payload del evento de Stripe
    payload_data = {
        "id": "evt_test_simulated_999",
        "object": "event",
        "api_version": "2022-11-15",
        "created": int(time.time()),
        "data": {
            "object": {
                "id": "cs_test_session_completed_999",
                "object": "checkout.session",
                "amount_subtotal": 4900,
                "amount_total": 4900,
                "currency": "usd",
                "customer_details": {
                    "email": "oruspgutierrez@gmail.com",
                    "name": "Mario Pacnaca (Simulado E2E)"
                },
                "payment_intent": "pi_test_simulated_999",
                "payment_status": "paid",
                "status": "complete",
                "metadata": {
                    "jid": "553598869018@s.whatsapp.net",
                    "client_name": "Mario Pacnaca (Simulado E2E)",
                    "client_email": "oruspgutierrez@gmail.com"
                }
            }
        },
        "type": "checkout.session.completed"
    }

    # Serializar el payload exactamente de la misma manera
    payload_text = json.dumps(payload_data, separators=(',', ':'))
    payload_bytes = payload_text.encode('utf-8')

    # 2. Generar el timestamp y firmar
    timestamp = str(int(time.time()))
    signed_payload = f"{timestamp}.".encode('utf-8') + payload_bytes
    
    # Calcular la firma HMAC SHA-256
    signature = hmac.new(
        webhook_secret.encode('utf-8'),
        signed_payload,
        hashlib.sha256
    ).hexdigest()
    
    sig_header = f"t={timestamp},v1={signature}"
    
    print(f"[INFO] Payload serializado ({len(payload_bytes)} bytes)")
    print(f"[INFO] Timestamp de firma: {timestamp}")
    print(f"[INFO] Signature generada: {signature}")
    print(f"[INFO] Header stripe-signature: {sig_header}")

    # 3. Enviar la petición POST al servidor local
    url = "http://localhost:8000/payments/webhook"
    headers = {
        "stripe-signature": sig_header,
        "Content-Type": "application/json"
    }
    
    print(f"\nEnviando POST a {url}...")
    try:
        response = requests.post(url, data=payload_bytes, headers=headers)
        print(f"Respuesta del servidor: HTTP {response.status_code}")
        print(f"Contenido: {response.text}")
    except requests.exceptions.ConnectionError:
        print("[ERROR] No se pudo conectar al servidor. ¿El servidor FastAPI está corriendo en el puerto 8000?")

if __name__ == "__main__":
    simulate_webhook()
