import requests
import qrcode
import json
import base64
import time

base_url = "https://whatsapp.orusquiroterapia.online"
instance_name = "OrusBot"

headers = {
    "apikey": "Vida2025@",
    "Content-Type": "application/json"
}

print("1. Limpiando instancia previa para iniciar limpio...")
requests.delete(f"{base_url}/instance/delete/{instance_name}", headers=headers)
time.sleep(2)

print(f"2. Creando instancia '{instance_name}'...")
payload_create = {
    "instanceName": instance_name,
    "integration": "WHATSAPP-BAILEYS"
}
requests.post(f"{base_url}/instance/create", headers=headers, json=payload_create)
time.sleep(2)

print("3. Solicitando string de conexión...")
res_connect = requests.get(f"{base_url}/instance/connect/{instance_name}", headers=headers)
data = res_connect.json()

# Manejamos los posibles campos donde viene la data
code_str = data.get("code") or data.get("pairingCode") or data.get("base64")

if not code_str:
    if "qrcode" in data:
        if isinstance(data["qrcode"], dict):
             code_str = data["qrcode"].get("base64")
        else:
             code_str = data["qrcode"]

if code_str:
    if str(code_str).startswith("2@") or "WhatsApp" not in code_str: 
        # Es la cadena raw del QR (usualmente empieza por 2@, 1@, etc)
        # o es cualquier string que no sea base64
        try:
            print("=> ¡Generando imagen localmente a partir del raw string!")
            img = qrcode.make(code_str)
            img.save("qr_code.png")
            print("\n=======================================================")
            print("EXITO! El QR fue dibujado y guardado como 'qr_code.png'.")
            print("Abre esta imagen y escaneala rapido con tu WhatsApp.")
            print("=======================================================\n")
        except Exception as e:
            print(f"Error generando imagen: {e}")
    else:
        # Asumimos que es base64
        if "," in str(code_str):
            code_str = code_str.split(",")[1]
        img_data = base64.b64decode(code_str)
        with open("qr_code.png", "wb") as f:
            f.write(img_data)
        print("EXITO! QR guardado como 'qr_code.png'.")
else:
    print("No se encontró cadena para el QR. Payload:", json.dumps(data, indent=2))
