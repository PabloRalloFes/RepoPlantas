import argparse
import os
import sys
from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from utils.database import connect_to_database, load_yaml_config
from utils.model import build_model


def resolve_config(experiment_path: str) -> dict:
    for filename in ("config_final.yaml", "config.yaml"):
        config_path = os.path.join(experiment_path, filename)
        if os.path.exists(config_path):
            return load_yaml_config(config_path)
    raise FileNotFoundError(f"No se encontró config_final.yaml ni config.yaml en {experiment_path}")


def resolve_classes(config: dict) -> list[str]:
    classes = config.get("classes", [])
    if isinstance(classes, list) and classes and "all" not in [str(value).lower() for value in classes]:
        return classes

    db = connect_to_database()
    classes_docs = list(db["Clases"].find({}, {"_id": 0, "class_label": 1, "nombre": 1, "clase": 1}))
    resolved = []
    for doc in classes_docs:
        class_label = str(doc.get("class_label", "")).strip()
        if class_label:
            resolved.append(class_label)
            continue
        nombre = str(doc.get("nombre", "")).strip()
        clase = str(doc.get("clase", "")).strip()
        if clase:
            resolved.append(clase)
        elif nombre:
            resolved.append(nombre)
    return sorted(set(resolved))


def predict(image_path, experiment_path):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    experiment_name = os.path.basename(os.path.normpath(experiment_path))
    modelo_path = os.path.join(experiment_path, "models", f"{experiment_name}.pth")
    if not os.path.exists(modelo_path):
        modelo_path = os.path.join(experiment_path, "models", "best_model.pth")

    config = resolve_config(experiment_path)
    config["classes"] = resolve_classes(config)

    model = build_model(config)
    model.load_state_dict(torch.load(modelo_path, map_location=device))
    model = model.to(device)
    model.eval()

    transform = transforms.Compose([
        transforms.Resize(tuple(config["image_size"])),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    image = Image.open(image_path).convert("RGB")
    image = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        logits = model(image)
        probabilities = torch.softmax(logits, dim=1).squeeze(0)
        predicted_index = int(probabilities.argmax().item())
        class_predicted = config["classes"][predicted_index]
        confidence = float(probabilities[predicted_index].item())

    print(f"Clase predicha: {class_predicted}")
    print(f"Confianza: {confidence:.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predecir una clase para una imagen")
    parser.add_argument("image_path", help="Ruta a la imagen")
    parser.add_argument(
        "-e",
        "--experiment",
        dest="experiment_path",
        default=os.path.join(str(ROOT), "experiments", "DemoMinimal"),
        help="Ruta al experimento (carpeta). Por defecto: experiments/DemoMinimal",
    )
    args = parser.parse_args()

    predict(args.image_path, args.experiment_path)
