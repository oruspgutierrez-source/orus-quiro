import requests

payload = {
    "data": {
        "key": {
            "remoteJid": "5511999999999@s.whatsapp.net",
            "fromMe": False,
            "id": "simulated_123"
        },
        "message": {
            "conversation": "Sí"
        },
        "pushName": "Simulated Customer"
    },
    "event": "messages.upsert"
}

resp = requests.post("http://217.196.61.72:8000/webhook", json=payload)
print(resp.status_code)
print(resp.text)
