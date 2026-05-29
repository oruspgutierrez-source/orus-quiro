import os
import stripe
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Inicializar clave secreta de Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

async def create_stripe_checkout_session(
    jid: str, 
    email: str | None = None, 
    name: str | None = None, 
    currency: str = "USD",
    amount: float = 49.00
) -> str:
    """
    Crea dinámicamente una sesión de Checkout de Stripe y retorna su URL pública.
    
    Parámetros:
    - jid: Identificador único de WhatsApp del consultante (ej. '5511999999999@s.whatsapp.net').
    - email: Correo electrónico opcional del cliente (para pre-completar en el checkout).
    - name: Nombre opcional del cliente para propósitos de facturación y metadatos.
    - currency: Divisa del cobro en formato ISO de 3 letras (USD, EUR, BRL, etc.). Por defecto USD.
    - amount: Monto flotante a cobrar (ej. 49.00). Por defecto 49.00.
    
    Retorna:
    - str: URL única de la sesión de Checkout segura de Stripe.
    """
    if not stripe.api_key:
        raise ValueError("Error crítico: STRIPE_SECRET_KEY no está configurada en las variables de entorno.")

    currency_upper = currency.upper()
    currency_lower = currency.lower()
    
    # Calcular el monto en centavos (unidad mínima de Stripe)
    unit_amount = int(round(amount * 100))

    # Definir los métodos de pago según la divisa
    # Si la moneda es BRL, permitimos Pix y tarjeta
    if currency_upper == "BRL":
        payment_method_types = ["card", "pix"]
    else:
        payment_method_types = ["card"]

    print(f"[Payment Gateway] Creando sesión de Stripe Checkout para JID={jid}, Monto={amount} {currency_upper}", flush=True)

    # Éxito y cancelación (URLs dinámicas con fallback)
    success_url = os.getenv("STRIPE_SUCCESS_URL", "https://orusquiroterapia.online/pago-exitoso")
    cancel_url = os.getenv("STRIPE_CANCEL_URL", "https://orusquiroterapia.online/pago-cancelado")

    # Crear la sesión de checkout utilizando la API de Stripe
    try:
        session_args = {
            "payment_method_types": payment_method_types,
            "line_items": [{
                "price_data": {
                    "currency": currency_lower,
                    "product_data": {
                        "name": "Lectura Completa de Quiromancia Védica",
                        "description": "Análisis biométrico y lectura personalizada de líneas de la mano",
                    },
                    "unit_amount": unit_amount,
                },
                "quantity": 1,
            }],
            "mode": "payment",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": {
                "jid": jid,
                "client_name": name or "",
                "client_email": email or "",
            }
        }

        # Si viene email, se pre-completa en la pantalla de Stripe
        if email:
            session_args["customer_email"] = email

        # Para Pix, Stripe exige configurar detalles adicionales de expiración o condiciones en ciertos casos
        if "pix" in payment_method_types:
            session_args["payment_method_options"] = {
                "pix": {
                    "expires_after_seconds": 3600  # 1 hora para completar el Pix
                }
            }

        session = stripe.checkout.Session.create(**session_args)
        
        print(f"[Payment Gateway] Sesión creada con éxito. URL: {session.url}", flush=True)
        return session.url

    except stripe.StripeError as e:
        print(f"[Payment Gateway] Error de Stripe: {e}", flush=True)
        raise e
    except Exception as e:
        print(f"[Payment Gateway] Error inesperado creando sesión: {e}", flush=True)
        raise e
