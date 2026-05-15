import os
import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from api.db.supabase_client import supabase

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'credentials.json'

CALENDAR_ID = os.getenv("CALENDAR_ID", "primary")

def get_calendar_service():
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print("[WARNING] credentials.json no encontrado, operando en modo Mock.")
        return None
    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=credentials)
    return service

def check_free_slots(start_date: str, end_date: str) -> str:
    """Consulta la disponibilidad en el calendario"""
    print(f"[CALENDAR TOOL] Ejecutando check_free_slots({start_date}, {end_date})")
    service = get_calendar_service()
    if not service:
        return f"Horarios ocupados encontrados:\nOcupado desde {start_date}T09:00:00Z hasta {start_date}T10:00:00Z. (Mock)"
        
    try:
        events_result = service.events().list(calendarId=CALENDAR_ID, timeMin=start_date,
                                            timeMax=end_date, singleEvents=True,
                                            orderBy='startTime').execute()
        events = events_result.get('items', [])
        
        if not events:
            return "No hay eventos agendados. El calendario está totalmente libre en ese rango."
        
        busy_slots = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            busy_slots.append(f"Ocupado desde {start} hasta {end}")
        
        return f"Horarios ocupados encontrados:\n" + "\n".join(busy_slots)
    except Exception as e:
        return f"Error consultando calendario: {str(e)}"

def book_appointment(phone_number: str, date_time: str, name: str) -> str:
    """Agenda un evento y guarda la fecha en Supabase"""
    print(f"[CALENDAR TOOL] Ejecutando book_appointment({phone_number}, {date_time}, {name})")
    
    # Actualizar Supabase
    try:
        supabase.table('orus_users').update({'appointment_date': date_time}).eq('phone_number', phone_number).execute()
        print(f"[DB] orus_users.appointment_date actualizado a {date_time} para {phone_number}")
    except Exception as e:
        print(f"[DB ERROR] {e}")

    service = get_calendar_service()
    if not service:
        return f"Cita agendada exitosamente (Mock link: http://calendar.google.com/mock)"

    try:
        start_time = datetime.datetime.fromisoformat(date_time.replace('Z', '+00:00'))
        end_time = start_time + datetime.timedelta(hours=1)
        
        event = {
            'summary': f'Cita Quiromancia - {name}',
            'description': f'Teléfono: {phone_number}',
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'America/Sao_Paulo',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'America/Sao_Paulo',
            },
        }
        event_res = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        return f"Cita agendada exitosamente: {event_res.get('htmlLink')}"
    except Exception as e:
        return f"Error agendando cita en Google Calendar: {str(e)}"
