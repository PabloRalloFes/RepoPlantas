#!/usr/bin/env python3
"""Diagnóstico rápido de conexión MongoDB (ejecutar dentro del contenedor api)."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pymongo import MongoClient
from utils.database import connect_to_database, DEFAULT_DB_NAME, _normalize_local_mongo_uri

uri = os.getenv("URL_BBDD", "mongodb://localhost:27017/")
db_name = os.getenv("DB_NAME", DEFAULT_DB_NAME)
uri_norm = _normalize_local_mongo_uri(uri)

print("=== Diagnóstico MongoDB ===")
print(f"URL_BBDD (env):     {uri}")
print(f"URL_BBDD (usada):   {uri_norm}")
print(f"DB_NAME (env):      {db_name}")
print(f"Dentro de Docker:   {os.path.exists('/.dockerenv')}")

client = MongoClient(uri_norm, serverSelectionTimeoutMS=5000)
try:
    client.admin.command("ping")
    print("Ping:               OK")
except Exception as exc:
    print(f"Ping:               FALLO ({exc})")
    sys.exit(1)

print(f"Bases de datos:     {client.list_database_names()}")

db = connect_to_database()
counts = {
    "Clases": db["Clases"].count_documents({}),
    "Fuente": db["Fuente"].count_documents({}),
    "Formato": db["Formato"].count_documents({}),
    "Docs": db["Docs"].count_documents({}),
}
print(f"\nColecciones en '{db_name}':")
for name, n in counts.items():
    print(f"  {name}: {n}")

if counts["Docs"] > 0 and counts["Clases"] == 0:
    print(
        "\nHay imágenes (Docs) pero Clases vacía: inconsistencia grave "
        "(¿restore parcial o borrado de catálogo?)."
    )
elif sum(counts.values()) == 0:
    print(
        "\nLa base está vacía. Ejecuta la inicialización:\n"
        "  docker compose --profile init run --rm initdb\n"
        "o restaura un backup con scripts/backup_mongo.sh (mongorestore)."
    )

for other_db in client.list_database_names():
    if other_db in ("admin", "config", "local", db_name):
        continue
    other = client[other_db]
    n_docs = other["Docs"].count_documents({}) if "Docs" in other.list_collection_names() else 0
    n_clases = other["Clases"].count_documents({}) if "Clases" in other.list_collection_names() else 0
    if n_docs or n_clases:
        print(f"\nAtención: '{other_db}' tiene Docs={n_docs}, Clases={n_clases} (¿DB_NAME incorrecto?).")
