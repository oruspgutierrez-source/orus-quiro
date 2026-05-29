import os
import sys
import requests
import urllib3
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

base_url = os.getenv("EVOLUTION_API_URL")
instance_name = os.getenv("EVOLUTION_INSTANCE_NAME")
api_key = os.getenv("EVOLUTION_API_KEY")

headers = {
    "apikey": api_key,
    "Content-Type": "application/json",
    "Host": "whatsapp.orusquiroterapia.online"
}

number = "553598869018"
payload = {
    "number": number,
    "count": 5
}

url = f"{base_url}/chat/findMessages/{instance_name}"

try:
    res = requests.post(url, json=payload, headers=headers, verify=False, timeout=10)
    data = res.json()
    records = data.get("messages", [])
    if isinstance(records, dict):
        records = records.get("records", [])
    
    print(f"Total mensajes recuperados: {len(records)}")
    for i, msg in enumerate(records[:5]):
        print(f"\nMensaje {i+1}:")
        print(f"  ID: {msg.get('key', {}).get('id')}")
        print(f"  FromMe: {msg.get('key', {}).get('fromMe')}")
        message_content = msg.get('message', {})
        if message_content:
            txt = message_content.get('conversation') or message_content.get('extendedTextMessage', {}).get('text')
            print(f"  Text: {txt}")
        print(f"  Timestamp: {msg.get('messageTimestamp')}")
except Exception as e:
    print(f"Error: {e}")
