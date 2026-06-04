import os
import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from api.db.supabase_client import supabase
from api.dependencies import verify_api_key

router = APIRouter(prefix="/api/calendar", tags=["Calendar"], dependencies=[Depends(verify_api_key)])

CALENDAR_ID = 'oruspgutierrez@gmail.com'
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_calendar_service():
    # Use the downloaded JSON credentials file
    creds_path = os.path.join(os.path.dirname(__file__), '..', 'google_credentials.json')
    if not os.path.exists(creds_path):
        raise HTTPException(status_code=500, detail="Falta el archivo google_credentials.json")
    
    try:
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"Error authenticating with Google Calendar: {e}")
        raise HTTPException(status_code=500, detail="Error autenticando con Google Calendar")

@router.get("/events")
def get_events(time_min: str = None, time_max: str = None):
    service = get_calendar_service()
    
    if not time_min:
        # Default: today minus 7 days
        now = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        time_min = now.isoformat() + 'Z'
        
    try:
        events_result = service.events().list(
            calendarId=CALENDAR_ID, 
            timeMin=time_min,
            timeMax=time_max,
            maxResults=100, 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        return {"events": events}
    except Exception as e:
        print(f"Error fetching calendar events: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo eventos de Google Calendar")

class NoteCreate(BaseModel):
    event_id: str
    client_name: str
    note_content: str

@router.post("/notes")
def save_note(note: NoteCreate):
    try:
        # Usamos upsert por si el usuario vuelve a guardar una nota para el mismo evento
        # Requiere que 'event_id' sea UNIQUE en la tabla
        data = supabase.table('orus_session_notes').upsert({
            'event_id': note.event_id,
            'client_name': note.client_name,
            'note_content': note.note_content
        }, on_conflict='event_id').execute()
        return {"status": "success", "data": data.data}
    except Exception as e:
        print(f"Error saving note: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notes")
def get_notes():
    try:
        response = supabase.table('orus_session_notes').select('*').order('created_at', desc=True).limit(50).execute()
        return {"notes": response.data}
    except Exception as e:
        print(f"Error fetching notes: {e}")
        raise HTTPException(status_code=500, detail=str(e))
