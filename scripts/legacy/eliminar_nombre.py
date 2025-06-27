from pymongo import MongoClient

# Configuración MongoDB
DB_NAME = "Repositorio_Plantas"
CLASE_COLECCION = "Clases"

client = MongoClient("mongodb://localhost:27017/")
db = client[DB_NAME]
coleccion = db[CLASE_COLECCION]

# Eliminar el campo "nombre" de todos los documentos
result = coleccion.update_many({}, {"$unset": {"nombre": ""}})

print(f"✅ Campo 'nombre' eliminado en {result.modified_count} documentos.")
