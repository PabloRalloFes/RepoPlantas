import subprocess
import argparse
import sys
import os

def run_subprocess(cmd):
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando: {' '.join(cmd)}")
        print(e)
        sys.exit(1)

def check_upload_images_exists():
    ROOT = os.path.dirname(os.path.abspath(__file__))
    ROOT = os.path.dirname(ROOT)
    if not os.path.exists(os.path.join(ROOT, "scripts", "upload_images.py")):
        print("No se encuentra upload_images.py en el directorio actual.")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline completo de subida de imágenes para una nueva fuente")
    parser.add_argument("--fuente", required=True, help="Nombre de la fuente nueva (subcarpeta dentro de data/Imported/)")
    parser.add_argument("--start", type=int, default=0, help="Índice inicial por clase (batch)")
    parser.add_argument("--limit", type=int, default=None, help="Número máximo de imágenes por clase (batch)")
    parser.add_argument("--no_auto_process", action="store_true", help="No procesar automáticamente si faltan carpetas")

    args = parser.parse_args()

    check_upload_images_exists()

    ROOT = os.path.dirname(os.path.abspath(__file__))
    ROOT = os.path.dirname(ROOT)

    fuente = args.fuente
    start = args.start
    limit = args.limit

    if args.no_auto_process:
        formatos = ["Color"]
    else:
        formatos = ["Color", "Grayscale", "Segmented"]
        
    for formato in formatos:
        print(f"\nSubiendo imágenes en formato {formato}...")
        cmd = ["python", os.path.join(ROOT, "scripts", "upload_images.py"), formato, "--fuente", fuente]
        if start: cmd += ["--start", str(start)]
        if limit: cmd += ["--limit", str(limit)]
        if args.no_auto_process:
            cmd.append("--no_auto_process")
        run_subprocess(cmd)

    print("\nPipeline completo finalizado con éxito.")
