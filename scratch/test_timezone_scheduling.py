import sys
import os
from datetime import datetime, date

# Añadir directorio actual al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.services.location_service import (
    detect_country_and_timezone,
    get_user_localized_slots,
    format_localized_availability,
    find_matching_date,
    find_matching_slot,
    get_next_5_active_days
)

def run_tests():
    print("=== INICIANDO PRUEBAS UNITARIAS DE AGENDA Y TIMEZONES ===")
    
    # 1. Test detect_country_and_timezone
    print("\n1. Probando detect_country_and_timezone:")
    test_cases_tz = [
        ("hola soy de colombia", ("Colombia", "America/Bogota")),
        ("estoy en españa y quiero agendar", ("España", "Europe/Madrid")),
        ("un saludo desde cdmx", ("Mexico", "America/Mexico_City")),
        ("soy ecuatoriano", ("Ecuador", "America/Guayaquil")),
        ("hola buenas noches", (None, None))
    ]
    for text, expected in test_cases_tz:
        country, tz = detect_country_and_timezone(text)
        assert (country, tz) == expected, f"Fallo en '{text}': esperanzado {expected}, obtenido {(country, tz)}"
        print(f"  [OK] '{text}' -> {country} ({tz})")

    # 2. Test get_next_5_active_days
    print("\n2. Probando get_next_5_active_days:")
    next_days = get_next_5_active_days()
    print(f"  Siguientes 5 días hábiles obtenidos: {next_days}")
    assert len(next_days) == 5, f"Debe retornar 5 días, obtuvo {len(next_days)}"
    for day_str in next_days:
        dt = datetime.strptime(day_str, "%Y-%m-%d").date()
        assert dt.weekday() != 6, f"No debe incluir domingos (weekday=6), obtuvo {day_str} ({dt.strftime('%A')})"
    print("  [OK] Todos los días son válidos y excluyen domingos")

    # 3. Test get_user_localized_slots (conversión y filtros)
    print("\n3. Probando get_user_localized_slots:")
    # Disponibilidad del terapeuta en Sao Paulo (UTC-3)
    # 8 AM a 8 PM (20h) excluyendo almuerzo (12 y 14h)
    therapist_slots = {
        "2026-06-12": [8, 9, 10, 11, 13, 15, 16, 17, 18, 19, 20]
    }
    
    # Caso España (Europe/Madrid)
    # Madrid en junio 2026 está en UTC+2 (Horario de verano)
    # Diferencia de +5 horas respecto a Sao Paulo.
    # 8 AM SP -> 13:00 Madrid
    # 17:00 SP -> 22:00 Madrid (debe filtrarse porque es >= 22:00)
    # 18:00 SP -> 23:00 Madrid (debe filtrarse)
    madrid_slots = get_user_localized_slots(therapist_slots, "Europe/Madrid")
    print(f"  Slots España (Europe/Madrid):")
    for date_str, slots in madrid_slots.items():
        print(f"    Fecha: {date_str}")
        for s in slots:
            print(f"      Local: {s['local_time_str']} (SP hour: {s['sp_hour']})")
            # Verificar que no hay citas de noche tarde
            assert s['local_hour'] < 22 and s['local_hour'] >= 8, f"Hora incorrecta para España: {s['local_hour']}"
    
    # Caso Colombia (America/Bogota)
    # Bogota está en UTC-5. Diferencia de -2 horas respecto a Sao Paulo.
    # 8 AM SP -> 6 AM Bogota (debe filtrarse por ser < 7 AM local)
    # 9 AM SP -> 7 AM Bogota (debe aparecer)
    # 20:00 SP -> 18:00 Bogota (debe aparecer)
    bogota_slots = get_user_localized_slots(therapist_slots, "America/Bogota")
    print(f"  Slots Colombia (America/Bogota):")
    for date_str, slots in bogota_slots.items():
        print(f"    Fecha: {date_str}")
        for s in slots:
            print(f"      Local: {s['local_time_str']} (SP hour: {s['sp_hour']})")
            assert s['local_hour'] >= 7 and s['local_hour'] < 22, f"Hora incorrecta para Colombia: {s['local_hour']}"
    print("  [OK] Conversiones y límites locales correctos")

    # 4. Test find_matching_date
    print("\n4. Probando find_matching_date:")
    cached_slots = {
        "2026-06-12": [], # 12 de Junio (Viernes)
        "2026-06-13": [], # 13 de Junio (Sábado)
    }
    # Por número
    assert find_matching_date("quiero el dia 12", cached_slots) == "2026-06-12"
    # Por nombre de día
    assert find_matching_date("el viernes por favor", cached_slots) == "2026-06-12"
    assert find_matching_date("el sabado", cached_slots) == "2026-06-13"
    print("  [OK] Búsqueda de fechas correcta")

    # 5. Test find_matching_slot
    print("\n5. Probando find_matching_slot:")
    slots_list = [
        {"local_hour": 8, "local_time_str": "8:00 am", "sp_iso": "...", "sp_hour": 10},
        {"local_hour": 15, "local_time_str": "3:00 pm", "sp_iso": "...", "sp_hour": 17},
        {"local_hour": 20, "local_time_str": "8:00 pm", "sp_iso": "...", "sp_hour": 22}
    ]
    # Caso pm explícito
    assert find_matching_slot("a las 3 pm", slots_list)["local_hour"] == 15
    # Caso 24h
    assert find_matching_slot("a las 15:00", slots_list)["local_hour"] == 15
    # Caso número solo (si no especifica, chequea ambas opciones; pero aquí 8 coincide con 8 am)
    assert find_matching_slot("a las 8", slots_list)["local_hour"] == 8
    # Caso "noche"
    assert find_matching_slot("a las 8 de la noche", slots_list)["local_hour"] == 20
    
    # Caso de conflicto entre día de mes y hora (ej: lunes 15 a las 8 am)
    assert find_matching_slot("lunes 15 de junio a las 8 am", slots_list, "2026-06-15")["local_hour"] == 8
    # Si dice "lunes 15 de junio a las 3 pm" donde 15 es el día y 3 es la hora, debe encontrar 15:00
    assert find_matching_slot("lunes 15 de junio a las 3 pm", slots_list, "2026-06-15")["local_hour"] == 15
    
    print("  [OK] Búsqueda de slots horaria correcta con exclusión de día de mes")
    print("\n=== TODAS LAS PRUEBAS SE PASARON CORRECTAMENTE ===")

if __name__ == "__main__":
    run_tests()
