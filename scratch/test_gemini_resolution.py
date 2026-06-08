import os
import sys
import asyncio
from dotenv import load_dotenv
load_dotenv()
sys.path.append('.')

from api.services.calendar_client import book_appointment
from api.db.supabase_client import supabase

async def test_db_update():
    print("Testing book_appointment Supabase database updates...")
    # Buscamos un usuario de prueba en Supabase para obtener su número
    try:
        res = supabase.table('orus_users').select('phone_number, appointment_date').limit(1).execute()
        if not res.data:
            print("No users found in database.")
            return
            
        test_user = res.data[0]
        original_phone = test_user['phone_number']
        print(f"Found test user in Supabase with phone: {original_phone}")
        
        # Simulamos que Gemini nos da un formato sin JID (ej. solo dígitos)
        clean_digits = "".join(c for c in original_phone if c.isdigit())
        print(f"Simulating Gemini calling book_appointment with digits-only phone: {clean_digits}")
        
        test_date = "2026-06-09T08:00:00-03:00"
        
        # Llamamos a book_appointment
        result = book_appointment(
            phone_number=clean_digits,
            date_time=test_date,
            name="Orusn Test",
            email="test@orus.com"
        )
        print("Result from book_appointment:", result)
        
        # Consultamos el usuario de nuevo para validar si se actualizó el appointment_date
        res_after = supabase.table('orus_users').select('appointment_date').eq('phone_number', original_phone).execute()
        updated_date = res_after.data[0]['appointment_date'] if res_after.data else None
        
        if updated_date == test_date:
            print("✅ PASÓ: El campo appointment_date en Supabase se actualizó correctamente a", updated_date)
        else:
            print("❌ FALLÓ: El campo appointment_date sigue siendo", updated_date)
            
    except Exception as e:
        print("Error during database test:", e)

if __name__ == "__main__":
    asyncio.run(test_db_update())
