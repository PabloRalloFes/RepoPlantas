import json
import os
import subprocess

JSON_PATH = os.path.join("src", "clases_combinadas.json")
REEMPLAZAR_SCRIPT = "scripts/reemplazar_clases.py"

if not os.path.exists(JSON_PATH):
    print(f"No se encontró el archivo: {JSON_PATH}")
    exit(1)

with open(JSON_PATH, "r", encoding="utf-8") as f:
    clases = json.load(f)

original = {c["_id"]: (c["clasificacion"], c["nombre_cientifico"]) for c in clases}

# Preguntar por filtro
filtrar = input("¿Quieres aplicar un filtro por planta? (s/n): ").strip().lower()
filtro_planta = None
if filtrar == "s":
    filtro_planta = input("Escribe el nombre exacto de la planta a filtrar (ej. 'Vid'): ").strip()

# Filtrar clases incompletas
incompletas = [
    c for c in clases
    if (not c.get("clasificacion") or not c.get("nombre_cientifico")) and
       (filtro_planta is None or c["planta"] == filtro_planta)
]

if not incompletas:
    print("No hay clases incompletas que coincidan con el filtro.")
    exit(0)

print(f"️Se encontraron {len(incompletas)} clases incompletas:")
for i, clase in enumerate(incompletas):
    print(f"[{i}] ID: {clase['_id']} | {clase['planta']}___{clase['nombre_comun']} | "
          f"clasificacion: '{clase['clasificacion']}' | cientifico: '{clase['nombre_cientifico']}'")

# Preguntar si quiere editar
print("\nPuedes editar los campos. Pulsa ENTER para dejar sin cambios.")
for i, clase in enumerate(incompletas):
    print(f"\n--- Clase {clase['_id']} ({clase['planta']}___{clase['nombre_comun']}) ---")
    nueva_clasificacion = input(f"Clasificación actual: '{clase['clasificacion']}'  Nuevo valor: ") or clase['clasificacion']
    nuevo_nombre_cientifico = input(f"Nombre científico actual: '{clase['nombre_cientifico']}' Nuevo valor: ") or clase['nombre_cientifico']

    for c in clases:
        if c["_id"] == clase["_id"]:
            c["clasificacion"] = nueva_clasificacion
            c["nombre_cientifico"] = nuevo_nombre_cientifico
            break

# Detectar si hubo cambios
modificados = [c for c in clases if (c["clasificacion"], c["nombre_cientifico"]) != original[c["_id"]]]

if modificados:
    print(f"Se modificaron {len(modificados)} clases. Guardando archivo...")
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(clases, f, indent=2, ensure_ascii=False)

    respuesta = input("\n¿Deseas actualizar la base de datos con estos cambios? (s/n): ").strip().lower()
    if respuesta == "s":
        if not os.path.exists(REEMPLAZAR_SCRIPT):
            print(f"No se encontró el script '{REEMPLAZAR_SCRIPT}'")
        else:
            print("Ejecutando reemplazar_clases.py...")
            subprocess.run(["python", REEMPLAZAR_SCRIPT])
else:
    print("\nNo se realizaron cambios en los datos. No se actualizó la base de datos.")
