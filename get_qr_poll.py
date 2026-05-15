import requests
import base64
import json
import time

base_url = "https://whatsapp.orusquiroterapia.online"
instance_name = "OrusBot"
headers = {
    "apikey": "Vida2025@",
    "Content-Type": "application/json"
}

def extract_and_save_qr(data):
    qr_base64 = None
    if "qrcode" in data and isinstance(data["qrcode"], str) and data["qrcode"].startswith("data:image"):
        qr_base64 = data["qrcode"]
    elif "base64" in data:
        qr_base64 = data["base64"]
    elif "qrcode" in data and isinstance(data["qrcode"], dict) and "base64" in data["qrcode"]:
        qr_base64 = data["qrcode"]["base64"]
    elif "code" in data and isinstance(data["code"], str) and data["code"].startswith("data:image"):
        qr_base64 = data["code"]
        
    if qr_base64:
        if "," in qr_base64:
            qr_base64 = qr_base64.split(",")[1]
        img_data = base64.b64decode(qr_base64)
        with open("qr_code.png", "wb") as f:
            f.write(img_data)
        print("\n=======================================================")
        print("EXITO! QR guardado como 'qr_code.png' en tu proyecto.")
        print("Abre ese archivo de imagen y escanealo con WhatsApp.")
        print("=======================================================\n")
        return True
    return False

# Delete first
print("Limpiando instancia previa...")
requests.delete(f"{base_url}/instance/delete/{instance_name}", headers=headers)
time.sleep(2)

payload = {
    "instanceName": instance_name,
    "qrcode": True,
    "integration": "WHATSAPP-BAILEYS"
}

print(f"Creando instancia '{instance_name}'...")
response = requests.post(f"{base_url}/instance/create", headers=headers, json=payload)
data = response.json()

if extract_and_save_qr(data):
    exit(0)

print("Esperando a que se genere el QR...")
for i in range(5):
    time.sleep(3)
    print(f"Intento {i+1} de obtener QR...")
    res = requests.get(f"{base_url}/instance/connect/{instance_name}", headers=headers)
    if res.status_code == 200:
        if extract_and_save_qr(res.json()):
            exit(0)

print("No se pudo obtener el QR. Respuesta final:")
print(res.json())
