import requests
import json

url = "http://localhost:8000/api/biometrics/completed"
payload = {
    "record": {
        "wa_id": "5511999999999",  # Un número de test
        "nombre": "Test User",
        "fotos_completadas": True
    }
}

headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    print("Status Code:", response.status_code)
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print("Error:", e)
