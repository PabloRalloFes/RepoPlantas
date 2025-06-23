import json
import os
import argparse
from pymongo import MongoClient

# Config
DB_NAME = "Repositorio_Plantas"
CLASE_COLECCION = "Clases"
MAPPING_PATH = "src/clases.json"

# Argumentos
parser = argparse.ArgumentParser(description="Añadir una nueva clase de enfermedad/planta al sistema")
parser.add_argument("nombre_clase", help="Nombre de la nueva clase (ej. Tomato___New_Disease)")
args = parser.parse_args()
nueva_clase = args.nombre_clase

# MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client[DB_NAME]
coleccion = db[CLASE_COLECCION]

# Leer mapping actual
if os.path.exists(MAPPING_PATH):
    with open(MAPPING_PATH, "r", encoding="utf-8") as f:
        clase_id_dict = json.load(f)
else:
    clase_id_dict = {}

# Verificar duplicado
if nueva_clase in clase_id_dict:
    print(f"⚠️ La clase '{nueva_clase}' ya existe con ID {clase_id_dict[nueva_clase]}")
    exit(0)

# Asignar nuevo ID
nuevo_id = max(clase_id_dict.values(), default=-1) + 1

# Insertar en Mongo
coleccion.insert_one({"_id": nuevo_id, "clase": nueva_clase})
print(f"✅ Clase '{nueva_clase}' insertada con ID {nuevo_id} en la colección '{CLASE_COLECCION}'")

# Actualizar JSON
clase_id_dict[nueva_clase] = nuevo_id
os.makedirs(os.path.dirname(MAPPING_PATH), exist_ok=True)
with open(MAPPING_PATH, "w", encoding="utf-8") as f:
    json.dump(clase_id_dict, f, indent=2, ensure_ascii=False)

print(f"📝 Diccionario actualizado en '{MAPPING_PATH}'")
