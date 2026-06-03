import requests
import json
import os
import time
from dotenv import load_dotenv
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main():
    print("=== AUTOMATIC WEBHOOK REGISTRATION ===")
    
    # 1. Obtener URL de ngrok de forma dinamica
    ngrok_api_url = "http://127.0.0.1:4040/api/tunnels"
    ngrok_url = None
    
    for i in range(5):
        try:
            res = requests.get(ngrok_api_url, timeout=3)
            data = res.json()
            if "tunnels" in data and len(data["tunnels"]) > 0:
                ngrok_url = data["tunnels"][0]["public_url"]
                break
        except Exception:
            pass
        print(f"Esperando que ngrok levante (intento {i+1}/5)...")
        time.sleep(2)
        
    if not ngrok_url:
        print("Error: No se pudo obtener la URL publica de ngrok.")
        return
        
    if ngrok_url.endswith("/"):
        ngrok_url = ngrok_url[:-1]
        
    print(f"\nURL de ngrok detectada: {ngrok_url}")
    
    # 2. Cargar variables de entorno
    load_dotenv()
    base_url = os.getenv("EVOLUTION_API_URL")
    instance_name = os.getenv("EVOLUTION_INSTANCE_NAME")
    api_key = os.getenv("EVOLUTION_API_KEY")
    
    # REGISTRO 1: Evolution API (WhatsApp)
    if all([base_url, instance_name, api_key]):
        api_secret_key = os.getenv("API_SECRET_KEY")
        full_webhook_url = f"{ngrok_url}/webhook"
        if api_secret_key:
            full_webhook_url += f"?token={api_secret_key}"
            
        payload = {
            "webhook": {
                "enabled": True,
                "url": full_webhook_url,
                "byEvents": False,
                "base64": False,
                "events": ["MESSAGES_UPSERT"]
            }
        }
        headers = {
            "apikey": api_key,
            "Content-Type": "application/json",
            "Host": "whatsapp.orusquiroterapia.online"
        }
        print(f"\n[1/2] Evolution API -> {full_webhook_url} ...")
        try:
            response = requests.post(f"{base_url}/webhook/set/{instance_name}", headers=headers, json=payload, timeout=10, verify=False)
            print(f"  Status: {response.status_code} | URL: {response.json().get('url', 'N/A')}")
        except Exception as e:
            print(f"  Error: {e}")
    else:
        print("[1/2] Skipped Evolution API - faltan variables de entorno.")

    # REGISTRO 2: Stripe (Pagos)
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if stripe_key:
        stripe_payment_url = f"{ngrok_url}/payments/webhook"
        print(f"\n[2/2] Stripe -> {stripe_payment_url} ...")
        try:
            import stripe
            stripe.api_key = stripe_key
            webhooks = stripe.WebhookEndpoint.list(limit=5)
            if webhooks.data:
                wh = webhooks.data[0]
                updated = stripe.WebhookEndpoint.modify(wh.id, url=stripe_payment_url)
                print(f"  Status: {updated.status} | URL: {updated.url}")
            else:
                created = stripe.WebhookEndpoint.create(
                    url=stripe_payment_url,
                    enabled_events=["checkout.session.completed"]
                )
                print(f"  Creado: {created.url}")
        except Exception as e:
            print(f"  Error: {e}")
    else:
        print("[2/2] Skipped Stripe - STRIPE_SECRET_KEY no encontrada.")

    print("\n=== REGISTRO COMPLETO ===")

if __name__ == "__main__":
    main()
