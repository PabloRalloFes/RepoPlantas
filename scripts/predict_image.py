# predict_image.py
import sys
import torch
from torchvision import transforms
from PIL import Image
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from utils.model import build_model
from utils.database import load_yaml_config, connect_to_database

def predict(image_path, config_path, modelo_path, known_planta=None):
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Cargar configuración y modelo
    config = load_yaml_config(config_path)

    if config["plantas"] == "all":
        db = connect_to_database()
        config["plantas"] = sorted(db["Clases"].distinct("planta"))
    if config["enfermedades"] == "all":
        db = connect_to_database()
        config["enfermedades"] = sorted(db["Clases"].distinct("nombre_comun"))

    model = build_model(config)
    model.load_state_dict(torch.load(modelo_path, map_location=device))
    model.eval()

    model = model.to(device)


    # Transforms
    transform = transforms.Compose([
        transforms.Resize(tuple(config["image_size"])),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])

    # Índices
    cultivo_to_idx = {c: i for i, c in enumerate(config["cultivos"])}
    enfermedad_to_idx = {e: i for i, e in enumerate(config["enfermedades"])}
    idx_to_cultivo = {i: c for c, i in cultivo_to_idx.items()}
    idx_to_enfermedad = {i: e for e, i in enfermedad_to_idx.items()}

    # Cargar imagen
    image = Image.open(image_path).convert("RGB")
    image = transform(image).unsqueeze(0).to(device)

    # Predecir
    with torch.no_grad():
        out_cultivo, out_enfermedad = model(image)
        probs_c = torch.softmax(out_cultivo, dim=1).squeeze()
        probs_e = torch.softmax(out_enfermedad, dim=1).squeeze()

        if known_planta:
            if known_planta not in cultivo_to_idx:
                raise ValueError(f"Cultivo '{known_planta}' no está en el config.")
            idx_cultivo = cultivo_to_idx[known_planta]
        else:
            idx_cultivo = probs_c.argmax().item()

        cultivo_pred = idx_to_cultivo[idx_cultivo]

        # Filtrar enfermedades válidas para ese cultivo
        combinaciones_validas = [(c, e) for c, e in zip(config["plantas"], config["enfermedades"])]
        enfermedades_validas = [e for c, e in combinaciones_validas if c == cultivo_pred]

        if not enfermedades_validas:
            raise ValueError(f"No hay enfermedades válidas para el cultivo predicho: {cultivo_pred}")

        probs_filtradas = {e: probs_e[enfermedad_to_idx[e]].item() for e in enfermedades_validas}
        enfermedad_pred = max(probs_filtradas, key=probs_filtradas.get)

    print(f"🌿 Cultivo predicho: {cultivo_pred}")
    print(f"🦠 Nombre común enfermedad predicha: {enfermedad_pred}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python predict_image.py <imagen.jpg> <config.yaml> <modelo.pth> [<planta>]")
        sys.exit(1)

    image_path = sys.argv[1]
    config_path = sys.argv[2]
    modelo_path = sys.argv[3]
    known_planta = sys.argv[4] if len(sys.argv) == 5 else None

    predict(image_path, config_path, modelo_path, known_planta)
