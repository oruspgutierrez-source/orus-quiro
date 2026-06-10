import requests
import json
import time
import sys

URL = "https://api.orusquiroterapia.online/webhook?token=OrusDashboardAdmin202"

def send_message(text: str):
    payload = {
        "event": "messages.upsert",
        "instance": "orusboth",
        "data": {
            "message": {
                "conversation": text
            },
            "key": {
                "remoteJid": "37598781259882@lid",
                "fromMe": False,
                "id": f"TEST_{int(time.time())}"
            },
            "messageContextInfo": {
                "deviceListMetadata": {
                    "senderKeyHash": "TEST"
                }
            }
        },
        "destination": "https://api.orusquiroterapia.online/webhook?token=OrusDashboardAdmin202",
        "date_time": "2026-06-08T13:02:50.667Z",
        "sender": "553798433269@s.whatsapp.net",
        "server_url": "https://whatsapp.orusquiroterapia.online",
        "apikey": "BC36EEF4A0B7-4294-BC1E-F822081CB21F"
    }
    print(f"Sending '{text}'...")
    r = requests.post(URL, json=payload)
    print(r.status_code, r.text)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        send_message(" ".join(sys.argv[1:]))
    else:
        print("Provide message text")
