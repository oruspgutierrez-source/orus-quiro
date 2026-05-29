import os
import datetime
import asyncio
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from api.db.supabase_client import supabase

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'credentials.json'

CALENDAR_ID = os.getenv("CALENDAR_ID", "primary")
BUSINESS_HOURS = [8, 9, 10, 11, 14, 15, 16, 17]

def get_calendar_service():
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print("[WARNING] credentials.json no encontrado, operando en modo Mock.", flush=True)
        return None
    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=credentials)
    return service

def get_free_slots_data(date_str: str) -> list[int]:
    """Consulta los horarios disponibles en el calendario para una fecha específica (YYYY-MM-DD)
    y retorna una lista de horas libres (enteros).
    """
    print(f"[CALENDAR TOOL] Ejecutando get_free_slots_data({date_str})", flush=True)
    service = get_calendar_service()

    time_min = f"{date_str}T00:00:00-03:00"
    time_max = f"{date_str}T23:59:59-03:00"

    if not service:
        # Modo simulacion: todos los slots de BUSINESS_HOURS están libres
        return BUSINESS_HOURS
        
    try:
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        busy_hours = set()
        for event in events:
            start_str = event['start'].get('dateTime', '')
            if start_str:
                try:
                    dt_val = datetime.datetime.fromisoformat(start_str)
                    busy_hours.add(dt_val.hour)
                except Exception:
                    pass

        free_slots = [h for h in BUSINESS_HOURS if h not in busy_hours]
        return free_slots
    except Exception as e:
        print(f"[CALENDAR TOOL ERROR] Fallo al consultar disponibilidad para {date_str}: {e}", flush=True)
        return []

def format_availability_table(days: list[str], slots_per_day: dict[str, list[int]]) -> str:
    """Formatea la disponibilidad como tabla AM/PM legible por el LLM y el consultante."""
    lines = [
        "DISPONIBILIDAD SEMANAL:",
        "| Día       | AM (8-12h)           | PM (14-17h)         |",
        "|-----------|----------------------|---------------------|"
    ]
    
    import datetime as dt
    days_es = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    
    for day_str in days:
        try:
            parsed_date = dt.datetime.strptime(day_str, "%Y-%m-%d")
            day_name = days_es[parsed_date.weekday()]
            date_short = f"{parsed_date.day}/{parsed_date.month}"
            day_col = f"{day_name} {date_short}"
        except:
            day_col = day_str
            
        slots = slots_per_day.get(day_str, [])
        am_slots = [h for h in slots if h < 12]
        pm_slots = [h for h in slots if h >= 12]
        
        am_str = " ".join([f"{h}:00" for h in am_slots])
        pm_str = " ".join([f"{h}:00" for h in pm_slots])
        
        lines.append(f"| {day_col:<9} | {am_str:<20} | {pm_str:<19} |")
        
    return "\n".join(lines)

def check_free_slots(start_date: str, end_date: str) -> str:
    """Consulta los horarios disponibles en el calendario para un rango de fechas dado.
    
    Args:
        start_date: Fecha de inicio en formato YYYY-MM-DD (ej: '2026-05-20')
        end_date: Fecha de fin en formato YYYY-MM-DD (ej: '2026-05-20')
    
    Returns:
        String con los horarios disponibles o un mensaje de error.
    """
    print(f"[CALENDAR TOOL] Ejecutando check_free_slots({start_date}, {end_date})")
    service = get_calendar_service()

    # Convertir fechas simples (YYYY-MM-DD) a timestamps ISO 8601 completos con timezone
    try:
        if 'T' not in start_date:
            time_min = f"{start_date}T00:00:00-03:00"
        else:
            time_min = start_date
        if 'T' not in end_date:
            time_max = f"{end_date}T23:59:59-03:00"
        else:
            time_max = end_date
    except Exception:
        time_min = start_date
        time_max = end_date

    if not service:
        return (
            f"Horarios disponibles para {start_date}:\n"
            "- 10:00 AM\n- 11:00 AM\n- 3:00 PM\n- 4:00 PM\n"
            "(Modo simulacion: credenciales de calendario no disponibles)"
        )
        
    try:
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        # Horario de atencion: 8am a 6pm, bloques de 1 hora
        busy_hours = set()
        for event in events:
            start_str = event['start'].get('dateTime', '')
            if start_str:
                try:
                    hour = datetime.datetime.fromisoformat(start_str).hour
                    busy_hours.add(hour)
                except Exception:
                    pass

        free_slots = [h for h in BUSINESS_HOURS if h not in busy_hours]

        if not free_slots:
            return f"No hay horarios disponibles para {start_date}. Todas las horas estan ocupadas."

        slots_str = "\n".join([f"- {h:02d}:00" for h in free_slots])
        return f"Horarios disponibles para {start_date}:\n{slots_str}"
    except Exception as e:
        return f"Error consultando calendario: {str(e)}"

async def send_visual_agenda_protocol(phone_number: str, name: str, date_time: str, email: str, link: str):
    """
    Subrutina asíncrona para despachar secuencialmente las imágenes y textos explicativos (Spec 13)
    al WhatsApp del usuario tras agendar la cita.
    """
    from api.services.wa_client import wa_client
    
    print(f"[Visual Agenda] Iniciando envío de guías de agendamiento para {phone_number}...", flush=True)
    
    # Ruta base de las imágenes
    img_path = os.path.join("resources", "media", "images", "explicacionagenda.png")
    
    # 1. Texto unificado
    unified_text = (
        "Tu sesion ha sido agendada con exito.\n\n"
        "Para registrar la cita en tu dispositivo, sigue este protocolo exacto:\n\n"
        "1. Al abrir el enlace que te compartiré, verás tres puntos en la esquina superior derecha. Presiona ahi.\n"
        "2. Selecciona la opcion 'Copiar en...'.\n"
        "3. Elige 'Mi calendario'. La cita se registrara automaticamente en tu dispositivo."
    )
    try:
        await wa_client.send_message(to=phone_number, text=unified_text)
        print("[Visual Agenda] Texto unificado enviado.", flush=True)
    except Exception as e:
        print(f"[Visual Agenda Error] Fallo al enviar texto unificado: {e}", flush=True)
        
    await asyncio.sleep(2.0)
    
    # 2. Imagen unificada
    try:
        await wa_client.send_image_message(to=phone_number, file_path=img_path, caption="")
        print("[Visual Agenda] Imagen unificada enviada.", flush=True)
    except Exception as e:
        print(f"[Visual Agenda Error] Fallo al enviar imagen unificada: {e}", flush=True)
    
    await asyncio.sleep(2.0)
    
    # 4. Mensaje final con el enlace directo para abrir el html de la cita agendada
    link_message = (
        f"Aquí tienes el enlace directo para abrir y guardar la cita en tu calendario:\n\n{link}"
    )
    try:
        await wa_client.send_message(to=phone_number, text=link_message)
        print("[Visual Agenda] Mensaje con enlace enviado exitosamente.", flush=True)
    except Exception as e:
        print(f"[Visual Agenda Error] Fallo al enviar mensaje con enlace: {e}", flush=True)

    await asyncio.sleep(3.0)

    # 5. Mensaje final con el link a la Web App de datos biométricos
    biometric_message = (
        "Finalmente, necesito tu material de trabajo. Ingresa a este enlace seguro https://ruta-del-escultor.vercel.app/ "
        "para subir las fotografias de tus manos siguiendo estrictamente los parametros indicados. "
        "Este es tu hardware; asegurate de que la iluminacion sea perfecta para que Orus pueda decodificarlo "
        "con precision antes de nuestra sesion de Revelacion."
    )
    try:
        await wa_client.send_message(to=phone_number, text=biometric_message)
        print("[Visual Agenda] Mensaje de datos biométricos enviado exitosamente.", flush=True)
    except Exception as e:
        print(f"[Visual Agenda Error] Fallo al enviar mensaje de datos biométricos: {e}", flush=True)

def book_appointment(phone_number: str, date_time: str, name: str, email: str) -> str:
    """Agenda una cita en el Google Calendar del profesional.
    
    Args:
        phone_number: El número de teléfono del cliente (ej: '+5491122334455')
        date_time: La fecha y hora de la cita en formato ISO 8601 (ej: '2026-05-20T10:00:00-03:00')
        name: Nombre completo del cliente
        email: Correo electrónico del cliente
    
    Returns:
        Un mensaje amigable con el enlace para agregar al calendario de Google.
    """
    print(f"[CALENDAR TOOL] Ejecutando book_appointment({phone_number}, {date_time}, {name}, {email})")
    
    # Actualizar Supabase
    try:
        supabase.table('orus_users').update({'appointment_date': date_time}).eq('phone_number', phone_number).execute()
        print(f"[DB] orus_users.appointment_date actualizado a {date_time} para {phone_number}")
    except Exception as e:
        safe_db_err = str(e).encode('ascii', 'replace').decode('ascii')
        print(f"[DB ERROR] {safe_db_err}")

    # Programar el envío de imágenes en segundo plano de manera robusta
    def trigger_visual_protocol(link: str):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(send_visual_agenda_protocol(phone_number, name, date_time, email, link))
            print("[Visual Agenda] Despachado protocolo asíncrono en loop activo.", flush=True)
        except RuntimeError:
            # Si no hay loop activo corriendo, se crea un loop temporal para procesar
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(send_visual_agenda_protocol(phone_number, name, date_time, email, link))
            new_loop.close()
            print("[Visual Agenda] Despachado protocolo asíncrono en nuevo loop cerrado.", flush=True)

    service = get_calendar_service()
    if not service:
        link = "http://calendar.google.com/mock"
        trigger_visual_protocol(link)
        return (
            f"ÉXITO: La cita para {name} el {date_time} fue registrada en Google Calendar. "
            f"El sistema acaba de despachar la confirmación y las guías visuales en segundo plano. "
            f"REGLA CRÍTICA: Ahora tu campo 'reply' DEBE ser única y exactamente: [AGENDA_COMPLETA]"
        )

    try:
        start_time = datetime.datetime.fromisoformat(date_time.replace('Z', '+00:00'))
        end_time = start_time + datetime.timedelta(hours=1)
        
        event = {
            'summary': f'Cita Quiromancia - {name}',
            'description': f'Telefono: {phone_number}\nCorreo: {email}',
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'America/Sao_Paulo',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'America/Sao_Paulo',
            }
        }
        
        event_res = service.events().insert(
            calendarId=CALENDAR_ID, 
            body=event
        ).execute()
        
        link = event_res.get('htmlLink')
        trigger_visual_protocol(link)
        
        return (
            f"ÉXITO: La cita para {name} el {date_time} fue registrada en Google Calendar. "
            f"El sistema acaba de despachar la confirmación y las guías visuales en segundo plano. "
            f"REGLA CRÍTICA: Ahora tu campo 'reply' DEBE ser única y exactamente: [AGENDA_COMPLETA]"
        )
    except Exception as e:
        safe_cal_err = str(e).encode('ascii', 'replace').decode('ascii')
        return f"Error agendando cita en Google Calendar: {safe_cal_err}"
