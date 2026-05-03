import json
import os
from pymongo import MongoClient
import sys
from pathlib import Path
from bson import ObjectId


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

json_path = os.path.join(ROOT, "src", "clases_peligro.json")
backup_path = os.path.join(ROOT, "src", "clases_backup.json")
os.makedirs(os.path.dirname(backup_path), exist_ok=True)

# Conexión a MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["Demo_Grietas"]
coleccion = db["Clases"]

def convertir_ids(doc):
    return {k: str(v) if isinstance(v, ObjectId) else v for k, v in doc.items()}

backup = list(coleccion.find())
backup_serializable = [convertir_ids(doc) for doc in backup]

if backup_serializable:
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(backup_serializable, f, indent=2, ensure_ascii=False)
else:
    print("️La colección 'Clases' estaba vacía. No se hizo backup.")

# Cargar nuevas clases desde archivo
if not os.path.exists(json_path):
    raise FileNotFoundError(f"No se encontró el archivo: {json_path}")

with open(json_path, "r", encoding="utf-8") as f:
    nuevas_clases = json.load(f)

# Reemplazar colección
coleccion.drop()
coleccion.insert_many(nuevas_clases)
print(f"Colección 'Clases' actualizada con {len(nuevas_clases)} nuevos documentos.")
