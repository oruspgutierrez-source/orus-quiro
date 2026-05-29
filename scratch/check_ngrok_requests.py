import requests
import json

url = "http://127.0.0.1:4040/api/requests"
print(f"Consultando peticiones de ngrok en: {url}")

try:
    res = requests.get(url, timeout=10)
    print(f"Status Code: {res.status_code}")
    data = res.json()
    requests_list = data.get("requests", [])
    print(f"Total de peticiones registradas en ngrok: {len(requests_list)}")
    for i, req in enumerate(requests_list[:10]):
        print(f"\nPetición {i+1}:")
        print(f"  ID: {req.get('id')}")
        print(f"  URI: {req.get('uri')}")
        print(f"  Method: {req.get('method')}")
        print(f"  Proto: {req.get('proto')}")
        print(f"  Duration: {req.get('duration')} ns")
        resp = req.get("response", {})
        print(f"  Response Status: {resp.get('status')} ({resp.get('proto')})")
        err = req.get("error")
        if err:
            print(f"  Error: {err}")
except Exception as e:
    print(f"Error consultando peticiones: {e}")
