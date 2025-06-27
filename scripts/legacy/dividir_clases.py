from pymongo import MongoClient

# Configuración MongoDB
DB_NAME = "Repositorio_Plantas"
CLASE_COLECCION = "Clases"

# Conectar a Mongo
client = MongoClient("mongodb://localhost:27017/")
db = client[DB_NAME]
coleccion = db[CLASE_COLECCION]

# Recorremos todas las clases
docs = list(coleccion.find())

actualizados = 0

for doc in docs:
    clasificacion = doc.get("clasificacion") or doc.get("clase")  # por si algunos están con "clase"
    if not clasificacion:
        continue

    if "___" not in clasificacion:
        print(f"⚠️ Formato no válido: {clasificacion}")
        continue

    cultivo, enfermedad = clasificacion.split("___", 1)

    update_fields = {}
    if "cultivo" not in doc:
        update_fields["cultivo"] = cultivo
    if "enfermedad" not in doc:
        update_fields["enfermedad"] = enfermedad

    if update_fields:
        coleccion.update_one({"_id": doc["_id"]}, {"$set": update_fields})
        actualizados += 1

print(f"✅ {actualizados} documentos actualizados.")