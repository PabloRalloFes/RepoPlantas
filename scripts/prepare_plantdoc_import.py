"""
Reorganiza el dataset PlantDoc al layout de Foliarium:
  data/PlantDoc/color/{Planta___Enfermedad}/imagen.jpg

Uso:
  python scripts/prepare_plantdoc_import.py --input /ruta/a/PlantDoc --output data/PlantDoc
  python scripts/subir_imagenes_nueva_fuente.py --fuente PlantDoc --validada

Descarga PlantDoc: https://github.com/pratikkayal/PlantDoc-Dataset
Referencia: Singh et al., PlantDoc, CoDS-COMAD 2020.
"""

import argparse
import os
import shutil
from pathlib import Path

# Etiquetas PlantDoc (carpetas del dataset original) -> convención PlantVillage en Foliarium
PLANTDOC_TO_FOLIARIUM = {
    "Apple Scab Leaf": "Apple___Apple_scab",
    "Apple rust leaf": "Apple___Cedar_apple_rust",
    "Apple leaf": "Apple___healthy",
    "Blueberry leaf": "Blueberry___healthy",
    "Cherry leaf": "Cherry_(including_sour)___healthy",
    "Corn Gray leaf spot": "Corn_(maize)___Cercospora_leaf_spot_Gray_leaf_spot",
    "Corn leaf blight": "Corn_(maize)___Northern_Leaf_Blight",
    "Corn rust leaf": "Corn_(maize)___Common_rust",
    "Peach leaf": "Peach___healthy",
    "Potato leaf early blight": "Potato___Early_blight",
    "Potato leaf": "Potato___healthy",
    "Potato leaf late blight": "Potato___Late_blight",
    "Raspberry leaf": "Raspberry___healthy",
    "Soyabean leaf": "Soybean___healthy",
    "Squash Powdery mildew leaf": "Squash___Powdery_mildew",
    "Strawberry leaf": "Strawberry___healthy",
    "Strawberry leaf scorch": "Strawberry___Leaf_scorch",
    "Tomato Early blight leaf": "Tomato___Early_blight",
    "Tomato leaf mosaic virus": "Tomato___Tomato_mosaic_virus",
    "Tomato leaf yellow virus": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato mold leaf": "Tomato___Leaf_Mold",
    "Tomato Septoria leaf spot": "Tomato___Septoria_leaf_spot",
    "Tomato leaf bacterial spot": "Tomato___Bacterial_spot",
    "Tomato leaf late blight": "Tomato___Late_blight",
    "Tomato leaf": "Tomato___healthy",
    "Tomato two spotted spider mites leaf": "Tomato___Spider_mites_Two-spotted_spider_mite",
    # Variantes de nombre que aparecen en algunas distribuciones
    "Bell_pepper leaf": "Pepper_bell___healthy",
    "Bell_pepper leaf spot": "Pepper_bell___Bacterial_spot",
    "grape leaf black rot": "Grape___Black_rot",
    "grape leaf": "Grape___healthy",
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def iter_labeled_image_dirs(root: Path):
    """Encuentra carpetas cuyo nombre coincide con una etiqueta PlantDoc conocida."""
    for dirpath, _dirnames, filenames in os.walk(root):
        base = os.path.basename(dirpath)
        if base not in PLANTDOC_TO_FOLIARIUM:
            continue
        has_images = any(Path(f).suffix.lower() in IMAGE_EXTENSIONS for f in filenames)
        if has_images:
            yield Path(dirpath), base


def copy_plantdoc(input_dir: Path, output_dir: Path, dry_run: bool = False):
    color_dir = output_dir / "color"
    stats = {"copied": 0, "skipped_class": 0, "unmapped": []}

    for class_path, label in iter_labeled_image_dirs(input_dir):
        target_class = PLANTDOC_TO_FOLIARIUM.get(label)
        if target_class is None:
            stats["skipped_class"] += 1
            continue

        dest = color_dir / target_class
        if not dry_run:
            dest.mkdir(parents=True, exist_ok=True)

        for f in class_path.iterdir():
            if f.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            dest_file = dest / f.name
            if dest_file.exists():
                continue
            if dry_run:
                print(f"[dry-run] {f} -> {dest_file}")
            else:
                shutil.copy2(f, dest_file)
            stats["copied"] += 1

    return stats


def main():
    parser = argparse.ArgumentParser(description="Preparar PlantDoc para importación en Foliarium")
    parser.add_argument(
        "--input",
        required=True,
        help="Ruta al dataset PlantDoc descomprimido (contiene carpetas por clase)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Carpeta destino (default: data/PlantDoc respecto a la raíz del repo)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar operaciones")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    output = Path(args.output) if args.output else root / "data" / "PlantDoc"
    input_dir = Path(args.input)

    if not input_dir.is_dir():
        raise SystemExit(f"No existe el directorio de entrada: {input_dir}")

    print(f"Entrada:  {input_dir}")
    print(f"Salida:   {output / 'color'}")
    stats = copy_plantdoc(input_dir, output, dry_run=args.dry_run)

    print(f"\nImágenes copiadas: {stats['copied']}")
    if stats["skipped_class"]:
        print(f"Carpetas omitidas (sin clase destino): {stats['skipped_class']}")
    if not args.dry_run and stats["copied"] > 0:
        print("\nSiguiente paso:")
        print("  python scripts/process_imported_images.py --fuente PlantDoc")
        print("  python scripts/subir_imagenes_nueva_fuente.py --fuente PlantDoc --validada")


if __name__ == "__main__":
    main()
