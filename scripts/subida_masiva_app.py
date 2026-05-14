import argparse
import subprocess
import os
import sys

def run_command(cmd):
    print(f"Ejecutando: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando {' '.join(cmd)}")
        print(e)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Subida masiva de imágenes (con opción de procesamiento previo)")
    parser.add_argument("--fuente", required=True, help="Nombre de la fuente (carpeta en data/)")
    parser.add_argument("--procesar", action="store_true", help="Procesar imágenes a grayscale y segmented antes de subir")
    parser.add_argument("--validada", action="store_true", help="Marcar como validadas las imágenes subidas")
    parser.add_argument("--usuario", default="desconocido", help="Usuario que ejecuta la subida")
    args = parser.parse_args()

    ROOT = os.path.dirname(os.path.abspath(__file__))
    ROOT = os.path.dirname(ROOT)
    base_path = os.path.join(ROOT, "data", args.fuente)

    color_path = os.path.join(base_path, "color")
    if not os.path.isdir(color_path):
        print(f"No se encontró la carpeta '{color_path}'.")
        print("Asegúrate de que existe la estructura data/{fuente}/color/")
        sys.exit(1)

    print(f"\nIniciando subida masiva para la fuente '{args.fuente}'")

    if args.procesar:
        print("\nProcesando imágenes (grayscale y segmented)...")
        run_command(["python", os.path.join(ROOT, "scripts", "process_imported_images.py"), "--fuente", args.fuente])
        print("\nSubiendo imágenes a la base de datos...")
        cmd = ["python", os.path.join(ROOT, "scripts", "subir_imagenes_nueva_fuente.py"), "--fuente", args.fuente, "--usuario", args.usuario]
        if args.validada:
            cmd.append("--validada")
        run_command(cmd)
    else:
        print("\nOmitiendo procesamiento. Se subirán solo las imágenes en color.")
        print("Subiendo solo imágenes en color (sin procesar nuevas versiones)...")
        cmd = ["python", os.path.join(ROOT, "scripts", "subir_imagenes_nueva_fuente.py"), "--fuente", args.fuente, "--usuario", args.usuario, "--no_auto_process"]
        if args.validada:
            cmd.append("--validada")
        run_command(cmd)

    

    print(f"\nSubida completada para la fuente '{args.fuente}'")

