# predict_image.py
import sys
import torch
from torchvision import transforms
from PIL import Image
import sys
from pathlib import Path
import pandas as pd
import os
import argparse


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from utils.model import build_model
from utils.database import load_yaml_config, connect_to_database

def predict(image_path, experiment_path, known_planta=None):
    device = "cuda" if torch.cuda.is_available() else "cpu"

    config_path = os.path.join(experiment_path, "config_final.yaml")
    modelo_path = os.path.join(experiment_path, "models/best_model.pth")
    data_path = os.path.join(experiment_path, "data")

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
    cultivo_to_idx = {c: i for i, c in enumerate(config["plantas"])}
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
                raise ValueError(f"La planta '{known_planta}' no está en el config.")
            idx_cultivo = cultivo_to_idx[known_planta]
        else:
            idx_cultivo = probs_c.argmax().item()

        cultivo_pred = idx_to_cultivo[idx_cultivo]

        # Filtrar enfermedades válidas para ese cultivo
        train_csv_path = Path(data_path) / "train.csv"
        if not train_csv_path.exists():
            raise FileNotFoundError(f"No se encuentra el archivo de combinaciones válidas: {train_csv_path}")

        df_train = pd.read_csv(train_csv_path)
        combinaciones_validas = set(zip(df_train["planta"], df_train["nombre_comun"]))

        # Filtrar enfermedades válidas para el cultivo predicho
        enfermedades_validas = [e for (p, e) in combinaciones_validas if p == cultivo_pred]

        if not enfermedades_validas:
            raise ValueError(f"No hay enfermedades válidas para el cultivo predicho: {cultivo_pred}")

        probs_filtradas = {e: probs_e[enfermedad_to_idx[e]].item() for e in enfermedades_validas}
        enfermedad_pred = max(probs_filtradas, key=probs_filtradas.get)

        if not enfermedades_validas:
            raise ValueError(f"No hay enfermedades válidas para el cultivo predicho: {cultivo_pred}")

        probs_filtradas = {e: probs_e[enfermedad_to_idx[e]].item() for e in enfermedades_validas}
        enfermedad_pred = max(probs_filtradas, key=probs_filtradas.get)

    print(f"Cultivo predicho: {cultivo_pred}")
    print(f"Nombre común enfermedad predicha: {enfermedad_pred}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predecir planta/enfermedad para una imagen")
    parser.add_argument("image_path", help="Ruta a la imagen")
    parser.add_argument("-e", "--experiment", dest="experiment_path",
                        default=os.path.join(str(ROOT), "experiments", "enteroColor"),
                        help="Ruta al experimento (carpeta). Por defecto: experiments/enteroColor")
    parser.add_argument("-p", "--planta", dest="known_planta", default=None,
                        help="Nombre de la planta conocido (opcional), para forzar la predicción de enfermedad")
    args = parser.parse_args()

    predict(args.image_path, args.experiment_path, args.known_planta)
