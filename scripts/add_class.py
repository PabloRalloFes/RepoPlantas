import json
import os
import argparse
from pymongo import MongoClient
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

DB_NAME = "Demo_Grietas"
CLASE_COLECCION = "Clases"

COMBINADAS_PATH = os.path.join(ROOT, "src", "clases_peligro.json")
ID_DICT_PATH = os.path.join(ROOT, "src", "clases.json")

parser = argparse.ArgumentParser(description="Añadir clase al sistema")
parser.add_argument("nombre_clase", help="Nombre de la clase de peligro (Inofensiva, Neutra, Peligrosa, ...)")
args = parser.parse_args()

nombre_clase = args.nombre_clase

# Conectar a Mongo
client = MongoClient("mongodb://localhost:27017/")
db = client[DB_NAME]
coleccion = db[CLASE_COLECCION]

# Cargar archivos
with open(COMBINADAS_PATH, "r", encoding="utf-8") as f:
    clases_combinadas = json.load(f)

with open(ID_DICT_PATH, "r", encoding="utf-8") as f:
    clase_id_dict = json.load(f)

# Revisar si ya existe
existe = next((c for c in clases_combinadas if c.get("clase") == nombre_clase or c.get("nombre") == nombre_clase), None)

if existe:
    print(f"La clase '{nombre_clase}' ya existe en clases_combinadas.json con ID {existe['_id']}")
    if not existe.get("clasificacion") or not existe.get("nombre_cientifico"):
        print(f"Esta clase tiene información incompleta. Ejecuta 'editar_clases.py' o utiliza la apppara completarla.")
    if not coleccion.find_one({"_id": existe["_id"]}):
        coleccion.insert_one(existe)
        print(f"Insertada en MongoDB con ID {existe['_id']}")
    else:
        print("Ya estaba presente en la base de datos.")
    exit(0)

# Si no existe, crear nuevo _id
nuevo_id = max([c["_id"] for c in clases_combinadas] + [-1]) + 1

nueva_clase = {
    "_id": nuevo_id,
    "nombre": nombre_clase,
    "clase": nombre_clase,
    "clasificacion": "",
    "nombre_cientifico": ""
}

# Actualizar clases_combinadas.json
clases_combinadas.append(nueva_clase)
with open(COMBINADAS_PATH, "w", encoding="utf-8") as f:
    json.dump(clases_combinadas, f, indent=2, ensure_ascii=False)

# Actualizar clases.json
clave = nombre_clase.replace(' ', '_')
clase_id_dict[clave] = nuevo_id
with open(ID_DICT_PATH, "w", encoding="utf-8") as f:
    json.dump(clase_id_dict, f, indent=2, ensure_ascii=False)

# Insertar en MongoDB
coleccion.insert_one(nueva_clase)

# Mensaje final
print(f"Clase '{nombre_clase}' añadida con ID {nuevo_id}")
print("️Esta clase se ha guardado con campos vacíos. Si deseas completarlos, hazlo desde la app o ejecuta:")
print("    python editar_clases.py")
