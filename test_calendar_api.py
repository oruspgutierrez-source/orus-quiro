import requests

url = "https://api.orusquiroterapia.online/api/calendar/events"
headers = {"x-api-key": "OrusDashboardAdmin2026"}
try:
    res = requests.get(url, headers=headers)
    print(res.status_code)
    print(res.json())
except Exception as e:
    print(e)
