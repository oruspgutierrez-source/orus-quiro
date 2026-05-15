import requests
import base64
import json

base_url = "https://whatsapp.orusquiroterapia.online"
instance_name = "OrusBot"
headers = {
    "apikey": "Vida2025@",
    "Content-Type": "application/json"
}

def extract_and_save_qr(data):
    qr_base64 = None
    
    # Manejar las diferentes estructuras de respuesta que puede dar Evolution V1/V2
    if "qrcode" in data and isinstance(data["qrcode"], str) and data["qrcode"].startswith("data:image"):
        qr_base64 = data["qrcode"]
    elif "base64" in data:
        qr_base64 = data["base64"]
    elif "qrcode" in data and isinstance(data["qrcode"], dict) and "base64" in data["qrcode"]:
        qr_base64 = data["qrcode"]["base64"]
    elif "code" in data and isinstance(data["code"], str) and data["code"].startswith("data:image"):
        qr_base64 = data["code"]
        
    if qr_base64:
        # Remover el prefijo URI si existe
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
    else:
        print("\nNo se encontro un QR en la respuesta. Mostrando payload:")
        print(json.dumps(data, indent=2))
        return False

# 1. Intentar crear la instancia
payload = {
    "instanceName": instance_name,
    "qrcode": True,
    "integration": "WHATSAPP-BAILEYS"
}

print(f"Intentando crear la instancia '{instance_name}'...")
try:
    response = requests.post(f"{base_url}/instance/create", headers=headers, json=payload)
    
    # Manejar la respuesta
    try:
        data = response.json()
    except json.JSONDecodeError:
        print(f"Error decodificando JSON. Respuesta cruda: {response.text}")
        exit(1)
        
    if response.status_code in [200, 201]:
        print("Instancia creada exitosamente.")
        extract_and_save_qr(data)
    else:
        print(f"Respuesta del servidor ({response.status_code}): {data}")
        # Si la instancia ya existe (comun error 403 o mensaje especifico)
        if response.status_code in [400, 403] or "exist" in str(data).lower():
            print("\nLa instancia probablemente ya existe. Intentando obtener QR de reconexion...")
            connect_res = requests.get(f"{base_url}/instance/connect/{instance_name}", headers=headers)
            
            if connect_res.status_code == 200:
                extract_and_save_qr(connect_res.json())
            else:
                print(f"Error al intentar conectar: {connect_res.status_code} - {connect_res.text}")
                
except Exception as e:
    print(f"\nError grave de conexion: {e}")
