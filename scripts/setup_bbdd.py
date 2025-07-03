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

with open("src/clases_combinadas.json", "r", encoding="utf-8") as f:
    clases = json.load(f)

for clase in sorted(clases, key=lambda c: c["_id"]):
    payload = {
        "coleccion": "Clases",
        "etiqueta": {
            "clasificacion": clase.get("clasificacion") or None,
            "planta": clase["planta"],
            "nombre_comun": clase["nombre_comun"],
            "nombre_cientifico": clase.get("nombre_cientifico") or None,
        }
    }
    r = requests.post(f"{URL}/add_etiqueta", json=payload)
    print(f'{clase["_id"]:>3} {clase["planta"]} - {clase["nombre_comun"]} → {r.status_code}')
