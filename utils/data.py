import pandas as pd
import os
import random
import pandas as pd
from torchvision import transforms
from PIL import Image
from torch.utils.data import Dataset, DataLoader
from pathlib import Path



def prepare_data_splits(db, config, save_dir):
    """
    Prepara los CSVs con rutas a imágenes y etiquetas para train/val/test.

    Args:
        db: conexión activa a MongoDB.
        config: diccionario cargado desde config.yaml.
        save_dir: carpeta donde guardar los CSVs.
    """
    fuentes = config["fuentes"]
    imagenes_por_clase = config["imagenes_por_clase"]
    split_ratios = config["split"]
    formato_nombre = config["formato"]
    cultivos = config["cultivos"]
    enfermedades = config["enfermedades"]

    # Obtener clases válidas con cultivo y enfermedad filtrados
    clases_filtradas = list(db["Clases"].find({
        "cultivo": {"$in": cultivos},
        "enfermedad": {"$in": enfermedades}
    }))

    if not clases_filtradas:
        raise ValueError("❌ No se han encontrado combinaciones cultivo-enfermedad válidas con los filtros actuales del config.")


    id_to_info = {doc["_id"]: (doc["cultivo"], doc["enfermedad"]) for doc in clases_filtradas}
    clases_ids = list(id_to_info.keys())

    # Formato y fuentes
    formatos = {doc["formato"]: doc["_id"] for doc in db["Formato"].find()}
    formato_id = formatos[formato_nombre]
    fuentes_dict = {doc["fuente"]: doc["_id"] for doc in db["Fuente"].find()}
    fuentes_ids = [fuentes_dict[fuente] for fuente in fuentes if fuente in fuentes_dict]

    # Avisos de fuentes no encontradas
    no_encontradas = [fuente for fuente in fuentes if fuente not in fuentes_dict]
    if no_encontradas:
        print(f"⚠️ Fuentes no encontradas en la base de datos: {no_encontradas}")

    # Obtener documentos válidos
    docs = list(db["Docs"].find({
        "formato": formato_id,
        "clase": {"$in": clases_ids},
        "fuente": {"$in": fuentes_ids}
    }))

    # Agrupar por clase
    docs_por_clase = {}
    for doc in docs:
        clase_id = doc.get("clase")
        if clase_id in id_to_info:
            docs_por_clase.setdefault(clase_id, []).append(doc)

    print(f"Se han encontrado {len(docs_por_clase)} clases con imágenes en formato {formato_nombre}.")

    CURRENT_FILE = Path(__file__).resolve()
    REPO_ROOT = CURRENT_FILE.parents[1]
    IMAGENES_DIR = REPO_ROOT / "imagenes"

    split_data = []

    for clase_id, lista in docs_por_clase.items():
        random.shuffle(lista)
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
            cultivo, enfermedad = id_to_info[clase_id]

            split_data.append({
                "imagen_rgb": ruta_local,
                "cultivo": cultivo,
                "enfermedad": enfermedad,
                "clase_id": clase_id,  # para trazabilidad
                "subset": subset
            })

    df = pd.DataFrame(split_data)
    os.makedirs(save_dir, exist_ok=True)

    for subset in ["train", "val", "test"]:
        df[df["subset"] == subset].to_csv(os.path.join(save_dir, f"{subset}.csv"), index=False)

    print("✅ CSVs guardados en la carpeta data/:")
    print(df["subset"].value_counts())


class PlantDataset(Dataset):
    def __init__(self, csv_path, cultivos, enfermedades, transform=None):
        self.data = pd.read_csv(csv_path)
        self.transform = transform

        self.cultivo_to_idx = {c: i for i, c in enumerate(cultivos)}
        self.enfermedad_to_idx = {e: i for i, e in enumerate(enfermedades)}

        self.idx_to_cultivo = {i: c for c, i in self.cultivo_to_idx.items()}
        self.idx_to_enfermedad = {i: e for e, i in self.enfermedad_to_idx.items()}

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        row = self.data.iloc[idx]
        image_path = row["imagen_rgb"]
        cultivo = self.cultivo_to_idx[row["cultivo"]]  # NUEVO
        enfermedad = self.enfermedad_to_idx[row["enfermedad"]]  # NUEVO
        image = Image.open(image_path).convert("RGB")

        if self.transform:
            image = self.transform(image)

        return image, (cultivo, enfermedad)

def get_dataloader_from_csv(csv_path, config):
    image_size = tuple(config["image_size"])
    batch_size = config["batch_size"]
    transform = transforms.Compose([
        transforms.Resize(image_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                            std=[0.229, 0.224, 0.225])
    ])

    cultivos = config["cultivos"]
    enfermedades = config["enfermedades"]

    train_ds = PlantDataset(os.path.join(csv_path, "train.csv"), cultivos, enfermedades, transform=transform)
    val_ds = PlantDataset(os.path.join(csv_path, "val.csv"), cultivos, enfermedades, transform=transform)
    test_ds = PlantDataset(os.path.join(csv_path, "test.csv"), cultivos, enfermedades, transform=transform)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)
    test_loader = DataLoader(test_ds, batch_size=batch_size)

    return train_loader, val_loader, test_loader
