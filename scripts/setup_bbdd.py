import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

URL = os.getenv("URL_API")

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

with open("src/clases_peligro.json", "r", encoding="utf-8") as f:
    clases = json.load(f)

for clase in sorted(clases, key=lambda c: c["_id"]):
    payload = {
        "coleccion": "Clases",
        "etiqueta": {
            "nombre": clase.get("nombre", clase.get("clase", "")),
            "clase": clase.get("clase", clase.get("nombre", "")),
            "clasificacion": clase.get("clasificacion", ""),
            "nombre_cientifico": clase.get("nombre_cientifico", ""),
        }
    }
    r = requests.post(f"{URL}/add_etiqueta", json=payload)
    print(f'{clase["_id"]:>3} {payload["etiqueta"]["nombre"]} → {r.status_code}')
