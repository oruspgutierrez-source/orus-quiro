import os
import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'credentials.json'

CALENDAR_ID = os.getenv("CALENDAR_ID", "primary")

def get_calendar_service():
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError("El archivo credentials.json no existe en la raíz del proyecto.")
    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=credentials)
    return service

def check_free_slots(start_date: str, end_date: str) -> str:
    """Consulta la disponibilidad en Google Calendar entre dos fechas en formato ISO."""
    try:
        service = get_calendar_service()
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
    """Agenda un evento de 1 hora en Google Calendar y devuelve un mensaje de éxito."""
    try:
        service = get_calendar_service()
        start_time = datetime.datetime.fromisoformat(date_time.replace('Z', '+00:00'))
        end_time = start_time + datetime.timedelta(hours=1)
        
        event = {
            'summary': f'Cita Quiromancia - {name}',
            'description': f'Teléfono: {phone_number}',
            'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'UTC',
            },
            'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'UTC',
            },
        }
        event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        return f"Cita agendada exitosamente: {event.get('htmlLink')}"
    except Exception as e:
        return f"Error agendando cita: {str(e)}"
