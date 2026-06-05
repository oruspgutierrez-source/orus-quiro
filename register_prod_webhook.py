import requests
import json
import os
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main():
    print("=== REGISTRO DE WEBHOOK PARA PRODUCCIÓN ===")
    
    # Intenta cargar un archivo .env.production, sino recae al .env normal
    load_dotenv(".env.production") if os.path.exists(".env.production") else load_dotenv()
    
    # 1. Obtener URL de producción desde el env
    production_url = os.getenv("VPS_DOMAIN_URL")
    if not production_url:
        print("Error: VPS_DOMAIN_URL no encontrada en el entorno (ej. https://api.tudominio.com).")
        print("Por favor agrégala al archivo .env.production")
        return
        
    if production_url.endswith("/"):
        production_url = production_url[:-1]
        
    print(f"\nURL de Producción detectada: {production_url}")
    
    base_url = os.getenv("EVOLUTION_API_URL")
    instance_name = os.getenv("EVOLUTION_INSTANCE_NAME")
    api_key = os.getenv("EVOLUTION_API_KEY")
    api_secret_key = os.getenv("API_SECRET_KEY")
    
    # REGISTRO 1: Evolution API
    if all([base_url, instance_name, api_key]):
        full_webhook_url = f"{production_url}/webhook"
        if api_secret_key:
            full_webhook_url += f"?token={api_secret_key}"
            
        payload = {
            "webhook": {
                "enabled": True,
                "url": full_webhook_url,
                "byEvents": False,
                "base64": True,
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
            print(f"  Status: {response.status_code} | Respuesta: {response.text}")
        except Exception as e:
            print(f"  Error: {e}")
    else:
        print("[1/2] Skipped Evolution API - faltan variables de entorno base_url/instance_name/api_key.")

    # REGISTRO 2: Stripe
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if stripe_key:
        stripe_payment_url = f"{production_url}/payments/webhook"
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

    print("\n=== FIN DEL REGISTRO ===")

if __name__ == "__main__":
    main()
