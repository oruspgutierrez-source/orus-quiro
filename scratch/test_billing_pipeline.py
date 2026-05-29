import os
import asyncio
from dotenv import load_dotenv

# Cargar variables de entorno del archivo .env en la raíz del proyecto
load_dotenv()

# Asegurar que el PYTHONPATH incluya la raíz del proyecto para importar 'api' correctamente
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from api.services.billing import generate_invoice_pdf, send_invoice_by_whatsapp

async def main():
    print("=== INICIANDO PRUEBA DE PIPELINE DE FACTURACIÓN ===")
    
    # Parámetros de prueba
    test_jid = "553598869018@s.whatsapp.net"
    test_name = "Mario Pacnaca (Test)"
    test_email = "oruspgutierrez@gmail.com"
    test_tx_id = "ch_test_billing_12345"
    test_amount = 49.00
    test_currency = "USD"
    
    print(f"1. Generando PDF de factura para {test_name}...")
    try:
        pdf_path = generate_invoice_pdf(
            transaction_id=test_tx_id,
            client_name=test_name,
            client_email=test_email,
            amount=test_amount,
            currency=test_currency
        )
        print(f"   [ÉXITO] PDF generado en: {pdf_path}")
        
        # Verificar que el archivo existe físicamente y tiene tamaño
        if os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path)
            print(f"   [INFO] El archivo existe y pesa {file_size} bytes.")
        else:
            print("   [ERROR] El archivo no se encuentra en el disco.")
            return
            
    except Exception as e:
        print(f"   [FALLO] Ocurrió un error al generar la factura: {e}")
        return

    print(f"\n2. Enviando factura PDF a WhatsApp (JID: {test_jid})...")
    try:
        res = await send_invoice_by_whatsapp(
            jid=test_jid,
            pdf_path=pdf_path,
            client_name=test_name,
            transaction_id=test_tx_id
        )
        print(f"   [ÉXITO] Respuesta del servidor WA: {res}")
    except Exception as e:
        print(f"   [FALLO] Ocurrió un error al enviar el documento: {e}")

    print("\n=== PRUEBA FINALIZADA ===")

if __name__ == "__main__":
    asyncio.run(main())
