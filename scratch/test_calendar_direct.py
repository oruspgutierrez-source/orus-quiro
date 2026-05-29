import os
import sys
# Añadir el directorio raíz al path de Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from api.services.calendar_client import book_appointment, check_free_slots

print("--- INICIANDO DIAGNÓSTICO DIRECTO DE GOOGLE CALENDAR ---")
print(f"CALENDAR_ID configurado: {os.getenv('CALENDAR_ID')}")

# Intentar agendar para una fecha en el futuro cercano (ej. 25 de Mayo de 2026 a las 10:00)
test_phone = "5535998869018"
test_date = "2026-05-25T10:00:00"
test_name = "Diagnóstico Antigravity"

print(f"\nEjecutando book_appointment...")
resultado = book_appointment(test_phone, test_date, test_name)

print("\n--- RESULTADO DE LA FUNCIÓN ---")
print(resultado)
