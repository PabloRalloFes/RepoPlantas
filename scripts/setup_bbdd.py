import requests
import json

URL = "http://localhost:5001"

# Campos a crear
with open("src/campos.json", "r", encoding="utf-8") as f:
    campos = json.load(f)

for campo in campos:
    r = requests.post(f"{URL}/add_campo", json=campo)
    print(r.status_code, r.json())

# Etiquetas a añadir
with open("src/etiquetas.json", "r", encoding="utf-8") as f:
    etiquetas = json.load(f)

for e in etiquetas:
    r = requests.post(f"{URL}/add_etiqueta", json=e)
    print(r.status_code, r.json())

# Clases a crear
with open("src/clases.json", "r", encoding="utf-8") as f:
    clase_id_dict = json.load(f)

for nombre_completo in sorted(clase_id_dict, key=lambda x: clase_id_dict[x]):
    cultivo = nombre_completo.split("___")[0]
    enfermedad = nombre_completo.split("___")[1] 
    payload = {
        "coleccion": "Clases",
        "etiqueta": {
            "clasificacion": nombre_completo,
            "cultivo": cultivo,
            "enfermedad": enfermedad
        }
    }
    r = requests.post(f"{URL}/add_etiqueta", json=payload)
    print(f"{nombre_completo} → {r.status_code}")