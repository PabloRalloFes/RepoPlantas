import pandas as pd
import os
import random
import pandas as pd
from torchvision import transforms
from PIL import Image
import torch
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix
import torch.nn as nn
import torch.optim as optim



def prepare_data_splits(db, config, save_dir):
    """
    Prepara los CSVs con rutas a imágenes y etiquetas para train/val/test.

    Args:
        db: conexión activa a MongoDB.
        config: diccionario cargado desde config.yaml.
        save_dir: carpeta donde guardar los CSVs.
    """
    fuentes = list(config["fuentes"])
    imagenes_por_clase = config["imagenes_por_clase"]
    split_ratios = config["split"]
    formato_nombre = config["formato"]
    if len(config["clases"]) == 1 and config["clases"][0] == "all":
        clases = list(set(doc["clasificacion"] for doc in db["Clases"].find()))
    else:
        clases = config["clases"]  
    print(clases)

    formatos = {doc["formato"]: doc["_id"] for doc in db["Formato"].find()}
    formato_id = formatos[formato_nombre]

    clases_dict = {doc["clasificacion"]: doc["_id"] for doc in db["Clases"].find()}
    fuentes_dict = {doc["fuente"]: doc["_id"] for doc in db["Fuente"].find()}

    clases_ids = [clases_dict[clase] for clase in clases if clase in clases_dict]
    fuentes_ids = [fuentes_dict[fuente] for fuente in fuentes if fuente in fuentes_dict]
    
    no_encontradas = [clase for clase in clases if clase not in clases_dict.keys()]
    if no_encontradas:
        print(f"⚠️ Clases no encontradas en la base de datos: {no_encontradas}")
    no_encontradas = [fuente for fuente in fuentes if fuente not in fuentes_dict]
    if no_encontradas:
        print(f"⚠️ Fuentes no encontradas en la base de datos: {no_encontradas}") 

    docs = list(db["Docs"].find({
        "formato": formato_id,
        "clase": {"$in": clases_ids},
        "fuente": {"$in": fuentes_ids}
    }))

    docs_por_clase = {}

    for doc in docs:
        clase_id = doc.get("clase")
        if clase_id not in clases_dict.values():
            continue

        docs_por_clase.setdefault(clase_id, []).append(doc)

    print(f"Se han encontrado {len(docs_por_clase)} clases con imágenes en formato {formato_nombre}.")

    
    CURRENT_FILE = Path(__file__).resolve()
    REPO_ROOT = CURRENT_FILE.parents[1]
    IMAGENES_DIR = REPO_ROOT / "imagenes"

    split_data = []

    for clase_id, lista in docs_por_clase.items():
        random.shuffle(lista)
        # Si imagenes_por_clase es mayor que la cantidad disponible, no recorta la lista
        if imagenes_por_clase is not None and imagenes_por_clase < len(lista):
            lista = lista[:imagenes_por_clase]
        n_total = len(lista)
        n_train = int(n_total * split_ratios["train"])
        n_val = int(n_total * split_ratios["val"])

        for i, doc in enumerate(lista):
            if i < n_train:
                subset = "train"
            elif i < n_train + n_val:
                subset = "val"
            else:
                subset = "test"

            nombre_archivo = doc["imagen_rgb"].split("/")[-1]
            ruta_local = os.path.join(IMAGENES_DIR, nombre_archivo)

            # Buscar el nombre de la clase a partir del id (valor) en clases_dict
            clase_nombre = next((k for k, v in clases_dict.items() if v == clase_id), None)
            split_data.append({
                "imagen_rgb": ruta_local,
                "clase_id": clase_id,
                "clase_nombre": clase_nombre,
                "subset": subset
            })

    df = pd.DataFrame(split_data)

    os.makedirs(save_dir, exist_ok=True)

    for subset in ["train", "val", "test"]:
        df[df["subset"] == subset].to_csv(os.path.join(save_dir, f"{subset}.csv"), index=False)

    print("✅ CSVs guardados en la carpeta data/:")
    print(df["subset"].value_counts())


class PlantDataset(Dataset):
    def __init__(self, csv_path, class_names, transform=None):
        self.data = pd.read_csv(csv_path)
        self.transform = transform
        self.class_to_idx = {c: i for i, c in enumerate(class_names)}
        self.classes = class_names

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        row = self.data.iloc[idx]
        image_path = row["imagen_rgb"]
        label = self.class_to_idx[row["clase_nombre"]]
        #label = row["clase_id"]
        image = Image.open(image_path).convert("RGB")

        if self.transform:
            image = self.transform(image)
        return image, label

def get_dataloader_from_csv(csv_path, config):
    image_size = tuple(config["image_size"])
    batch_size = config["batch_size"]
    transform = transforms.Compose([
        transforms.Resize(image_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                            std=[0.229, 0.224, 0.225])
    ])

    class_names = config["clases"]
    if class_names == ["all"]:
        raise ValueError("Debes definir explícitamente las clases si usas múltiples splits.")

    train_ds = PlantDataset(os.path.join(csv_path, "train.csv"), class_names, transform=transform)
    val_ds = PlantDataset(os.path.join(csv_path, "val.csv"), class_names, transform=transform)
    test_ds = PlantDataset(os.path.join(csv_path, "test.csv"), class_names, transform=transform)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)
    test_loader = DataLoader(test_ds, batch_size=batch_size)

    return train_loader, val_loader, test_loader
