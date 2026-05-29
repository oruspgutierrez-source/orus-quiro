import os
import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()
CALENDAR_ID = os.getenv("CALENDAR_ID", "primary")

def list_events():
    credentials = Credentials.from_service_account_file('credentials.json', scopes=['https://www.googleapis.com/auth/calendar'])
    service = build('calendar', 'v3', credentials=credentials)
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(calendarId=CALENDAR_ID, timeMin=now, maxResults=10, singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(f"[{start}] {event['summary']}")

if __name__ == "__main__":
    list_events()
