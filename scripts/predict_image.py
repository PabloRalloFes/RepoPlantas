import argparse
import os
import sys
from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from utils.database import connect_to_database, load_yaml_config, get_project_config
from utils.model import build_model


def resolve_config(experiment_path: str) -> dict:
    for filename in ("config_final.yaml", "config.yaml"):
        config_path = os.path.join(experiment_path, filename)
        if os.path.exists(config_path):
            return load_yaml_config(config_path)
    raise FileNotFoundError(f"No se encontró config_final.yaml ni config.yaml en {experiment_path}")


def resolve_project_metadata(config: dict) -> tuple[list[str], dict[str, list[str]]]:
    db = connect_to_database()
    project_config = get_project_config(db=db)

    target_fields = config.get("target_fields") or project_config.get("target_fields") or ["class_label"]
    if not isinstance(target_fields, list):
        target_fields = [target_fields]
    target_fields = [str(field).strip() for field in target_fields if str(field).strip()]

    target_classes = config.get("target_classes") or project_config.get("target_classes") or {}
    if not target_classes:
        classes_docs = list(db["Clases"].find({}, {"_id": 0, "class_label": 1, "nombre": 1, "clase": 1, **{field: 1 for field in target_fields}}))
        for field_name in target_fields:
            values = []
            for doc in classes_docs:
                value = doc.get(field_name)
                if value is None or str(value).strip() == "":
                    value = doc.get("class_label") or doc.get("clase") or doc.get("nombre")
                if value is not None and str(value).strip() != "":
                    values.append(str(value).strip())
            target_classes[field_name] = sorted(set(values))

    return target_fields, target_classes


def predict(image_path, experiment_path):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    experiment_name = os.path.basename(os.path.normpath(experiment_path))
    modelo_path = os.path.join(experiment_path, "models", f"{experiment_name}.pth")
    if not os.path.exists(modelo_path):
        modelo_path = os.path.join(experiment_path, "models", "best_model.pth")

    config = resolve_config(experiment_path)
    target_fields, target_classes = resolve_project_metadata(config)
    config["target_fields"] = target_fields
    config["target_classes"] = target_classes
    if len(target_fields) == 1:
        config["classes"] = target_classes[target_fields[0]]
        config["class_field"] = target_fields[0]

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
        if len(target_fields) == 1:
            probabilities = torch.softmax(logits, dim=1).squeeze(0)
            predicted_index = int(probabilities.argmax().item())
            class_predicted = config["classes"][predicted_index]
            confidence = float(probabilities[predicted_index].item())

            print(f"Clase predicha: {class_predicted}")
            print(f"Confianza: {confidence:.4f}")
        else:
            predictions = {}
            confidences = {}
            for head_idx, field_name in enumerate(target_fields):
                probabilities = torch.softmax(logits[head_idx], dim=1).squeeze(0)
                predicted_index = int(probabilities.argmax().item())
                predictions[field_name] = target_classes[field_name][predicted_index]
                confidences[field_name] = float(probabilities[predicted_index].item())

            for field_name in target_fields:
                print(f"{field_name}: {predictions[field_name]} (confianza={confidences[field_name]:.4f})")


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
