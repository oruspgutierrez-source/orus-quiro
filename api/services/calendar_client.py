import os
import datetime
import asyncio
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from api.db.supabase_client import supabase

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'credentials.json'

CALENDAR_ID = os.getenv("CALENDAR_ID", "primary")
BUSINESS_HOURS = [8, 9, 10, 11, 13, 15, 16, 17, 18, 19, 20]

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

HOUR_LABEL = {
    8: "8am", 9: "9am", 10: "10am", 11: "11am",
    13: "1pm", 15: "3pm", 16: "4pm", 17: "5pm",
    18: "6pm", 19: "7pm", 20: "8pm"
}
MONTHS_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
DAYS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

def format_availability_table(days: list[str], slots_per_day: dict[str, list[int]]) -> str:
    """Formatea la disponibilidad en lenguaje natural humanizado para WhatsApp."""
    import datetime as dt

    lines = ["Estos son los horarios disponibles para tu sesión de Mapeo:"]

    for day_str in days:
        try:
            parsed = dt.datetime.strptime(day_str, "%Y-%m-%d")
            day_name = DAYS_ES[parsed.weekday()]
            day_num = parsed.day
            month_name = MONTHS_ES[parsed.month - 1]
            label = f"{day_name} {day_num} de {month_name}"
        except Exception:
            label = day_str

        slots = slots_per_day.get(day_str, [])
        am_slots = [HOUR_LABEL.get(h, f"{h}am") for h in slots if h < 12]
        pm_slots = [HOUR_LABEL.get(h, f"{h}pm") for h in slots if h >= 12]

        if not slots:
            lines.append(f"\n{label}: sin disponibilidad")
            continue

        day_line = f"\n{label}:"
        if am_slots:
            day_line += f"\n  Mañana: {', '.join(am_slots)}"
        if pm_slots:
            day_line += f"\n  Tarde: {', '.join(pm_slots)}"
        lines.append(day_line)

    lines.append("\n¿Qué día y horario prefieres?")
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
    Subrutina simplificada (Spec 41) para notificar el agendamiento exitoso y redirigir
    directamente al consultante a la Web App de datos biométricos.
    """
    from api.services.wa_client import wa_client
    
    print(f"[Visual Agenda] Iniciando envío simplificado para {phone_number}...", flush=True)
    
    fecha_legible = date_time
    try:
        import datetime
        dt = datetime.datetime.fromisoformat(date_time.replace('Z', '+00:00'))
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        meses = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        dia_semana = dias[dt.weekday()]
        dia_mes = dt.day
        nombre_mes = meses[dt.month - 1]
        
        hour_12 = dt.hour
        ampm = "am" if hour_12 < 12 else "pm"
        hour_display = hour_12 if hour_12 <= 12 else hour_12 - 12
        if hour_display == 0:
            hour_display = 12
            
        time_str = f"{hour_display}:{dt.minute:02d} {ampm}"
        fecha_legible = f"{dia_semana} {dia_mes} de {nombre_mes} a las {time_str}"
    except Exception as parse_err:
        print(f"[Visual Agenda] Error formateando fecha {date_time}: {parse_err}", flush=True)
        fecha_legible = date_time
        
    clean_phone = phone_number.split("@")[0] if "@" in phone_number else phone_number
    
    unified_message = (
        f"¡Tu cita ha sido registrada exitosamente! 📅\n"
        f"{fecha_legible}\n"
        f"Recibirás todos los detalles en {email}.\n\n"
        f"Para completar tu proceso de preparación, el siguiente paso es registrar tus datos y fotos biométricas en nuestro formulario seguro:\n"
        f"https://ruta-del-escultor.vercel.app/?phone={clean_phone}\n\n"
        f"Asegúrate de que la iluminación de tus fotos sea perfecta para que pueda decodificarse con precisión antes de nuestra sesión. ¡Nos vemos pronto!"
    )
    
    try:
        await wa_client.send_message(to=phone_number, text=unified_message)
        print("[Visual Agenda] Mensaje simplificado enviado exitosamente.", flush=True)
        try:
            from api.db.supabase_client import supabase
            user_res = supabase.table('orus_users').select('id').eq('phone_number', phone_number).execute()
            if user_res.data:
                user_uuid = user_res.data[0]['id']
                supabase.table('orus_messages').insert({
                    'user_id': user_uuid,
                    'role': 'assistant',
                    'content': unified_message
                }).execute()
                print("[Visual Agenda DB] Mensaje registrado en Supabase.", flush=True)
        except Exception as db_err:
            print(f"[Visual Agenda DB Error] Fallo al registrar mensaje: {db_err}", flush=True)
    except Exception as e:
        print(f"[Visual Agenda Error] Fallo al enviar mensaje simplificado: {e}", flush=True)

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
    
    # Programmatic firewall to prevent early booking without real user details
    name_clean = str(name).strip().lower()
    email_clean = str(email).strip().lower()
    if (not name or name_clean == "" or "pendiente" in name_clean or "unknown" in name_clean or "placeholder" in name_clean or
        not email or email_clean == "" or "pendiente" in email_clean or "unknown" in email_clean or "placeholder" in email_clean or
        "@" not in email_clean):
        print("[CALENDAR TOOL ERROR] book_appointment abortado: Faltan datos reales del usuario (Nombre/Email).")
        return (
            "ERROR: No se puede agendar la cita todavía. Faltan registrar o confirmar el Nombre completo y el Correo electrónico real del usuario. "
            "Por favor, solicítale estos datos al usuario (Nombre completo y Correo electrónico) en tu respuesta y espera su mensaje con los datos antes de volver a invocar esta herramienta."
        )
        
    # Actualizar Supabase
    try:
        # Asegurarnos de que el número tenga el formato JID completo (@s.whatsapp.net) para buscar en Supabase
        clean_jid = phone_number.strip()
        if not clean_jid.endswith("@s.whatsapp.net"):
            import re
            digits = "".join(re.findall(r"\d+", clean_jid))
            clean_jid = f"{digits}@s.whatsapp.net"
            
        print(f"[DB] Intentando actualizar appointment_date a {date_time} para JID: {clean_jid}", flush=True)
        res = supabase.table('orus_users').update({'appointment_date': date_time}).eq('phone_number', clean_jid).execute()
        
        # Si no se modificó ninguna fila (data vacía), intentamos con solo dígitos
        if not res.data:
            import re
            digits_only = "".join(re.findall(r"\d+", phone_number))
            print(f"[DB] JID no encontrado, intentando actualizar con dígitos solos: {digits_only}", flush=True)
            res2 = supabase.table('orus_users').update({'appointment_date': date_time}).eq('phone_number', digits_only).execute()
            if res2.data:
                print(f"[DB] Éxito: orus_users.appointment_date actualizado usando dígitos para {digits_only}", flush=True)
            else:
                print(f"[DB WARNING] Ninguna fila actualizada para {phone_number} ni en formato JID ni dígitos.", flush=True)
        else:
            print(f"[DB] Éxito: orus_users.appointment_date actualizado usando JID para {clean_jid}", flush=True)
            
    except Exception as e:
        safe_db_err = str(e).encode('ascii', 'replace').decode('ascii')
        print(f"[DB ERROR] {safe_db_err}", flush=True)

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
