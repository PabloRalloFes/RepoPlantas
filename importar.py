import os
import subprocess
import argparse

FORMATS = ["Grayscale", "Segmented"]

def run_pipeline(fuente):
    base_dir = os.path.join("data", "importada", fuente)
    if not os.path.isdir(base_dir):
        print(f"❌ No se encontró la carpeta: {base_dir}")
        return

    print("▶️ Procesando imágenes...")
    subprocess.run(["python", "utils/process_imported_images.py", "--fuente", fuente], check=True)

    for formato in FORMATS:
        print(f"⬆️ Subiendo imágenes en formato {formato}...")
        subprocess.run(["python", "upload_images.py", formato, "--fuente", fuente], check=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline de importación de imágenes por fuente")
    parser.add_argument("--fuente", required=True, help="Nombre de la fuente (subcarpeta en data/importada)")
    args = parser.parse_args()

    run_pipeline(args.fuente)
