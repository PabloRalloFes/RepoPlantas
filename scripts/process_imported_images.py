import argparse
import os
import subprocess
import sys

def run_subprocess(cmd):
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando: {' '.join(cmd)}")
        print(e)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Procesamiento por lotes de imágenes importadas")
    parser.add_argument("--fuente", required=True, help="Nombre de la fuente (subcarpeta dentro de data/)")
    args = parser.parse_args()

    ROOT = os.path.dirname(os.path.abspath(__file__))
    ROOT = os.path.dirname(ROOT)
    base_path = os.path.join(ROOT, "data", args.fuente)
    color_path = os.path.join(base_path, "color")
    grayscale_path = os.path.join(base_path, "grayscale")
    segmented_path = os.path.join(base_path, "segmented")

    os.makedirs(grayscale_path, exist_ok=True)
    os.makedirs(segmented_path, exist_ok=True)

    print("Convirtiendo a escala de grises...")
    run_subprocess([
        "python", os.path.join(ROOT, "scripts", "convert_to_grayscale.py"),
        "--input", color_path,
        "--output", grayscale_path
    ])

    print("Segmentando hojas...")
    run_subprocess([
        "python", os.path.join(ROOT, "scripts", "segment_leaves.py"),
        "--input", color_path,
        "--output", segmented_path
    ])

    print("Procesamiento completado.")
