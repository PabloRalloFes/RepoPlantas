#!/usr/bin/env python3
"""
Script de migración: rehashea contraseñas en texto plano existentes en MongoDB.

Ejecutar UNA SOLA VEZ antes de arrancar el backend con la nueva versión bcrypt.

Uso:
    python scripts/migrar_passwords.py

El script detecta automáticamente qué usuarios tienen contraseña en texto plano
(no empieza por '$2b$') y los migra. Los ya hasheados se omiten sin tocarlos.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import connect_to_database
from utils.auth import hash_password


def es_hash_bcrypt(value: str) -> bool:
    return isinstance(value, str) and value.startswith("$2b$")


def migrar():
    db = connect_to_database(db_name="appPlantas")
    col = db["usuarios"]

    usuarios = list(col.find({}))
    total = len(usuarios)
    migrados = 0
    omitidos = 0

    print(f"Usuarios encontrados: {total}")

    for u in usuarios:
        nombre = u.get("nombre", "<sin nombre>")
        pwd = u.get("password", "")

        if es_hash_bcrypt(pwd):
            print(f"  ✓ {nombre}: ya tiene hash, omitido")
            omitidos += 1
            continue

        nuevo_hash = hash_password(pwd)
        col.update_one({"_id": u["_id"]}, {"$set": {"password": nuevo_hash}})
        print(f"  → {nombre}: migrado")
        migrados += 1

    print(f"\nResumen: {migrados} migrados, {omitidos} omitidos, {total} total.")
    if migrados > 0:
        print("Migración completada. Ya puedes arrancar el backend con bcrypt.")
    else:
        print("No había contraseñas en texto plano. Nada que migrar.")


if __name__ == "__main__":
    migrar()
