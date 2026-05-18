from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from utils.database import connect_to_database


SOURCE_DIR = ROOT / "data" / "Ejemplo" / "color"
IMAGES_DIR = ROOT / "imagenes"
EXPERIMENTS_DIR = ROOT / "experiments"
BASE_EXPERIMENT_DIR = EXPERIMENTS_DIR / "BASE"
DEFAULT_DB_NAME = "Demo_Grietas"
DEFAULT_CLASS_NAMES = ["Inofensiva", "Neutra", "Peligrosa"]
DEFAULT_FIELDS = [
    {
        "_id": 0,
        "nombre": "fuente",
        "cod": 4,
        "campos_etiqueta": {"fuente": "str"},
        "coleccion": "Fuente",
    },
    {
        "_id": 1,
        "nombre": "formato",
        "cod": 4,
        "campos_etiqueta": {"formato": "str"},
        "coleccion": "Formato",
    },
    {
        "_id": 2,
        "nombre": "class_label",
        "cod": 0,
        "campos_etiqueta": {"class_label": "str"},
        "coleccion": "Clases",
    },
]


def slugify(text: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "_", text)
    return text.strip("_").lower() or "demo"


def ensure_experiment_structure(experiment_name: str, overwrite: bool) -> Path:
    experiment_dir = EXPERIMENTS_DIR / experiment_name
    if experiment_dir.exists():
        if not overwrite:
            raise FileExistsError(
                f"El experimento '{experiment_name}' ya existe. Usa --overwrite para recrearlo."
            )
        shutil.rmtree(experiment_dir)

    experiment_dir.mkdir(parents=True, exist_ok=True)
    for folder in ("data", "models", "results"):
        (experiment_dir / folder).mkdir(parents=True, exist_ok=True)

    shutil.copy2(BASE_EXPERIMENT_DIR / "run_experiment.py", experiment_dir / "run_experiment.py")
    return experiment_dir


def load_base_config() -> dict:
    with open(BASE_EXPERIMENT_DIR / "config.yaml", "r", encoding="utf-8") as config_file:
        return yaml.safe_load(config_file) or {}


def select_class_dirs(max_classes: int) -> list[Path]:
    """Selecciona carpetas de clase que contengan imágenes. 
    Compatible tanto con nombres Planta___Enfermedad como nombres simples."""
    class_dirs = []
    for path in SOURCE_DIR.iterdir():
        if not path.is_dir():
            continue
        # Revisar si la carpeta contiene imágenes
        has_images = any(
            img_file.suffix.lower() in {".jpg", ".jpeg", ".png"}
            for img_file in path.rglob("*")
            if img_file.is_file()
        )
        if has_images:
            class_dirs.append(path)
    
    class_dirs.sort(key=lambda path: path.name.lower())
    if max_classes > 0:
        return class_dirs[:max_classes]
    return class_dirs


def upsert_reference(collection, field_name: str, value: str):
    existing = collection.find_one({field_name: value})
    if existing:
        return existing

    collection.insert_one({field_name: value})
    return collection.find_one({field_name: value})


def upsert_field(db, field_def: dict):
    db.Campos.replace_one({"_id": field_def["_id"]}, field_def, upsert=True)


def upsert_class(db, class_name: str):
    existing = db.Clases.find_one({"class_label": class_name})
    if existing:
        return existing
    db.Clases.insert_one({"class_label": class_name})
    return db.Clases.find_one({"class_label": class_name})


def seed_demo_data(db, class_dirs: list[Path], source_name: str, class_names: list[str], images_per_class: int):
    for field_def in DEFAULT_FIELDS:
        upsert_field(db, field_def)

    db.Formato.replace_one({"_id": 0}, {"_id": 0, "formato": "Color", "nombre": "Color"}, upsert=True)
    formato_doc = db.Formato.find_one({"_id": 0})

    db.Fuente.replace_one({"_id": 0}, {"_id": 0, "fuente": source_name, "nombre": source_name}, upsert=True)
    fuente_doc = db.Fuente.find_one({"_id": 0})

    inserted_classes = []
    next_doc_id = 0
    for class_index, (class_dir, class_name) in enumerate(zip(class_dirs, class_names), start=0):
        class_doc = {
            "_id": class_index,
            "class_label": class_name  # Campo requerido por el pipeline de entrenamiento
        }
        db.Clases.replace_one({"_id": class_index}, class_doc, upsert=True)
        inserted_classes.append(class_doc)

        image_files = sorted(
            [path for path in class_dir.iterdir() if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}],
            key=lambda path: path.name.lower(),
        )
        if images_per_class > 0:
            image_files = image_files[:images_per_class]

        for index, image_path in enumerate(image_files):
            safe_label = slugify(class_dir.name)
            demo_name = f"demo_{safe_label}_{index}{image_path.suffix.lower()}"
            target_path = IMAGES_DIR / demo_name
            shutil.copy2(image_path, target_path)

            db.Docs.insert_one(
                {
                    "_id": next_doc_id,
                    "imagen_rgb": f"https://localhost:5001/imagen_base64/{demo_name}",
                    "validada": True,
                    "usuario": "demo",
                    "clase": class_doc["_id"],
                    "fuente": fuente_doc["_id"],
                    "formato": formato_doc["_id"],
                }
            )
            next_doc_id += 1

    return [doc["class_label"] for doc in inserted_classes]


def main():
    parser = argparse.ArgumentParser(description="Crear una demo minima con datos de ejemplo y MongoDB.")
    parser.add_argument("--experiment-name", default="DemoMinimal", help="Nombre del experimento a crear.")
    parser.add_argument("--db-name", default=DEFAULT_DB_NAME, help="Nombre de la base de datos demo.")
    parser.add_argument("--class-names", nargs="+", default=DEFAULT_CLASS_NAMES, help="Nombres de clase a crear.")
    parser.add_argument("--source-name", default="DemoGrietas", help="Nombre de la fuente demo en MongoDB.")
    parser.add_argument("--images-per-class", type=int, default=1, help="Numero de imagenes por clase.")
    parser.add_argument("--overwrite", action="store_true", help="Recrear el experimento si ya existe.")
    args = parser.parse_args()

    if not SOURCE_DIR.exists():
        raise FileNotFoundError(f"No se encontro la carpeta de ejemplo: {SOURCE_DIR}")

    if len(args.class_names) < 1:
        raise ValueError("Debes indicar al menos una clase.")

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    db = connect_to_database(db_name=args.db_name)
    db.client.drop_database(args.db_name)

    class_dirs = select_class_dirs(len(args.class_names))
    if len(class_dirs) < len(args.class_names):
        raise ValueError(f"No se encontraron suficientes carpetas de ejemplo en {SOURCE_DIR}")

    class_labels = seed_demo_data(db, class_dirs, args.source_name, args.class_names, args.images_per_class)

    experiment_dir = ensure_experiment_structure(args.experiment_name, args.overwrite)
    config = load_base_config()
    config.update(
        {
            "classes": class_labels,
            "fuentes": [args.source_name],
            "imagenes_por_clase": args.images_per_class,
            "formato": "Color",
            "solo_validadas": True,
            "epochs": min(int(config.get("epochs", 3)), 1),
            "batch_size": min(int(config.get("batch_size", 32)), 8),
        }
    )

    with open(experiment_dir / "config.yaml", "w", encoding="utf-8") as config_file:
        yaml.safe_dump(config, config_file, sort_keys=False, allow_unicode=True)

    print(f"Demo creada en {experiment_dir}")
    print(f"Base de datos demo: {args.db_name}")
    print(f"Clases importadas: {', '.join(class_labels)}")
    print(f"Fuente demo: {args.source_name}")


if __name__ == "__main__":
    main()
