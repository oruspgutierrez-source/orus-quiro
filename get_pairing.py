import requests
import json
import time

base_url = "https://whatsapp.orusquiroterapia.online"
instance_name = "OrusBot"
number = "5537998433269"

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
    "integration": "WHATSAPP-BAILEYS",
    # En V2 a veces se permite pasar el numero directo en la creacion
    "number": number 
}
response_create = requests.post(f"{base_url}/instance/create", headers=headers, json=payload_create)
if response_create.status_code not in [200, 201]:
    print(f"Advertencia al crear: {response_create.text}")

print("3. Solicitando Codigo de Emparejamiento (Pairing Code)...")
time.sleep(2) # Dar tiempo al contenedor para inicializar la sesion

# endpoint de conexion enviando el parametro number
res_connect = requests.get(f"{base_url}/instance/connect/{instance_name}?number={number}", headers=headers)
data = res_connect.json()

print("\n================ RESPUESTA DE LA API ================\n")
if "code" in data:
    code = data["code"]
    print(f"   SU CODIGO DE EMPAREJAMIENTO ES:  {code}")
elif "pairingCode" in data:
    code = data["pairingCode"]
    print(f"   SU CODIGO DE EMPAREJAMIENTO ES:  {code}")
else:
    print("No se encontró un código en la respuesta:")
    print(json.dumps(data, indent=2))
print("\n=======================================================\n")
