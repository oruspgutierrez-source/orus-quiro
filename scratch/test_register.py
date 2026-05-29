import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url_https = "https://217.196.61.72"
headers = {
    "Host": "whatsapp.orusquiroterapia.online"
}
print(f"Probando GET a HTTPS IP {url_https} con Host y verify=False...")
try:
    res = requests.get(url_https, headers=headers, timeout=5, verify=False)
    print("Status HTTPS:", res.status_code)
    print("Headers:", dict(res.headers))
    print("Content:", res.text[:200])
except Exception as e:
    print("Error HTTPS:", e)
