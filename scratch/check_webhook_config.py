import os
import requests
import urllib3
from dotenv import load_dotenv

load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

base_url = os.getenv("EVOLUTION_API_URL")
instance_name = os.getenv("EVOLUTION_INSTANCE_NAME")
api_key = os.getenv("EVOLUTION_API_KEY")

headers = {
    "apikey": api_key,
    "Host": "whatsapp.orusquiroterapia.online"
}

url = f"{base_url}/webhook/find/{instance_name}"
print(f"Consultando webhook config en: {url}")

try:
    res = requests.get(url, headers=headers, verify=False, timeout=10)
    print(f"Status Code: {res.status_code}")
    print("Respuesta:")
    import json
    try:
        print(json.dumps(res.json(), indent=2))
    except Exception:
        print(res.text)
except Exception as e:
    print(f"Error consultando webhook: {e}")
