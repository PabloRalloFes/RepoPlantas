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
    fuentes = config.get("fuentes", ["all"])
    imagenes_por_clase = config["imagenes_por_clase"]
    split_ratios = config["split"]
    formato_nombre = config.get("formato")
    plantas = config.get("plantas", ["all"])
    enfermedades = config.get("enfermedades", ["all"])

    def is_scalar(v):
        return isinstance(v, (str, int, float, bool)) and v is not None

    def normalize_selected_values(values):
        if values is None:
            return []
        if not isinstance(values, list):
            values = [values]
        return [v for v in values if is_scalar(v) and str(v).strip() != ""]

    def resolve_collection_name(field_name, collection_names_lower):
        candidates = [
            field_name,
            field_name.capitalize(),
            field_name.title(),
            field_name.lower(),
            field_name.upper(),
        ]
        if field_name.endswith("s") and len(field_name) > 1:
            singular = field_name[:-1]
            candidates.extend([singular, singular.capitalize(), singular.title(), singular.lower()])

        for c in candidates:
            c_low = c.lower()
            if c_low in collection_names_lower:
                return collection_names_lower[c_low]
        return None

    def pick_label_field(collection_name, field_name):
        sample = db[collection_name].find_one({}, {"_id": 0}) or {}
        priority = [
            field_name,
            "nombre",
            "name",
            "valor",
            "descripcion",
            "fuente",
            "formato",
            "planta",
            "nombre_comun",
        ]
        for p in priority:
            if p in sample:
                return p
        return next(iter(sample.keys()), None)

    def cast_values_to_doc_types(field_name, selected_values):
        sample_values = [v for v in db["Docs"].distinct(field_name) if is_scalar(v)]
        if not sample_values:
            return selected_values

        has_bool = any(isinstance(v, bool) for v in sample_values)
        has_int = any(isinstance(v, int) and not isinstance(v, bool) for v in sample_values)
        has_float = any(isinstance(v, float) for v in sample_values)

        casted = set(selected_values)
        for v in selected_values:
            if isinstance(v, str):
                t = v.strip()
                if has_bool:
                    if t.lower() in ("true", "1", "si", "yes"):
                        casted.add(True)
                    elif t.lower() in ("false", "0", "no"):
                        casted.add(False)
                if has_int:
                    try:
                        casted.add(int(t))
                    except Exception:
                        pass
                if has_float:
                    try:
                        casted.add(float(t))
                    except Exception:
                        pass
        return list(casted)

    collection_names_lower = {c.lower(): c for c in db.list_collection_names()}

    # Obtener clases válidas con planta y enfermedad filtrados
    clases_filtradas = list(db["Clases"].find({
        "planta": {"$in": plantas},
        "nombre_comun": {"$in": enfermedades}
    }))

    if not clases_filtradas:
        raise ValueError(" No se han encontrado combinaciones planta-enfermedad válidas con los filtros actuales del config.")


    id_to_info = {doc["_id"]: (doc["planta"], doc["nombre_comun"]) for doc in clases_filtradas}
    clases_ids = list(id_to_info.keys())

    print(f"Se han encontrado {len(clases_ids)} clases válidas después de aplicar los filtros de planta y enfermedad.")

    # Formato y fuentes
    formatos = {doc["formato"]: doc["_id"] for doc in db["Formato"].find()}
    formato_id = formatos.get(formato_nombre)

    if formato_id is not None:
        print(f"Formato seleccionado: {formato_nombre} (ID: {formato_id})")
    else:
        print(f"Formato no encontrado o no especificado: {formato_nombre}")

    fuentes_dict = {doc["fuente"]: doc["_id"] for doc in db["Fuente"].find()}
    if isinstance(fuentes, list) and "all" in fuentes:
        fuentes_ids = list(fuentes_dict.values())
    else:
        fuentes_ids = [fuentes_dict[fuente] for fuente in fuentes if fuente in fuentes_dict]

    print(f"Fuentes seleccionadas: {fuentes} (IDs: {fuentes_ids})")

    # Avisos de fuentes no encontradas
    no_encontradas = [fuente for fuente in fuentes if fuente not in fuentes_dict]
    if no_encontradas:
        print(f"️Fuentes no encontradas en la base de datos: {no_encontradas}")

    # Construir query base de Docs
    docs_query = {
        "clase": {"$in": clases_ids}
    }

    if formato_id is not None:
        docs_query["formato"] = formato_id

    if fuentes_ids:
        docs_query["fuente"] = {"$in": fuentes_ids}

    solo_validadas = bool(config.get("solo_validadas", False))
    if solo_validadas:
        docs_query["validada"] = True

    # Filtros dinámicos adicionales: cualquier clave del config fuera del bloque reservado.
    reserved_keys = {
        "batch_size",
        "epochs",
        "fine_tune",
        "formato",
        "fuentes",
        "image_size",
        "imagenes_por_clase",
        "lr",
        "min_samples_per_class",
        "optimizer",
        "plantas",
        "enfermedades",
        "split",
        "use_class_weights",
        "weights",
        "peso_planta",
        "peso_enfermedad",
        "filtros_docs",
        "solo_validadas",
    }

    for key, raw_selected in config.items():
        if key in reserved_keys:
            continue

        selected = normalize_selected_values(raw_selected)
        if not selected or "all" in [str(v).lower() for v in selected]:
            continue

        # 1) Intentar filtro directo sobre Docs (con casteo de tipos si hace falta).
        selected_candidates = cast_values_to_doc_types(key, selected)
        direct_matches = db["Docs"].count_documents({key: {"$in": selected_candidates}})
        if direct_matches > 0:
            docs_query[key] = {"$in": selected_candidates}
            continue

        # 2) Si no hay match directo, resolver nombre->id usando una colección de referencia.
        collection_name = resolve_collection_name(key, collection_names_lower)
        if collection_name:
            label_field = pick_label_field(collection_name, key)
            if label_field:
                ref_docs = list(
                    db[collection_name].find(
                        {label_field: {"$in": [str(v) for v in selected]}},
                        {"_id": 1},
                    )
                )
                ref_ids = [d["_id"] for d in ref_docs if "_id" in d]
                if ref_ids:
                    docs_query[key] = {"$in": ref_ids}

    # Obtener documentos válidos
    docs = list(db["Docs"].find(docs_query))

    if not docs:
        if solo_validadas:
            raise ValueError(
                "No se han encontrado documentos para entrenar con los filtros actuales usando solo imágenes validadas."
            )
        raise ValueError("No se han encontrado documentos para entrenar con los filtros actuales.")

    print(f"Se han encontrado {len(docs)} documentos con los filtros configurados.")

    # Agrupar por clase
    docs_por_clase = {}
    for doc in docs:
        clase_id = doc.get("clase")
        if clase_id in id_to_info:
            docs_por_clase.setdefault(clase_id, []).append(doc)

    if not docs_por_clase:
        if solo_validadas:
            raise ValueError(
                "No hay clases con imágenes disponibles tras aplicar el filtro de solo imágenes validadas."
            )
        raise ValueError("No hay clases con imágenes disponibles tras aplicar los filtros seleccionados.")

    print(f"Se han encontrado {len(docs_por_clase)} clases con imágenes en formato {formato_nombre}.")

    clases_con_imagenes = [id_to_info[clase_id] for clase_id in docs_por_clase]
    plantas_filtradas = sorted(set(p for p, _ in clases_con_imagenes))
    enfermedades_filtradas = sorted(set(e for _, e in clases_con_imagenes))


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
            planta, enfermedad = id_to_info[clase_id]

            split_data.append({
                "imagen_rgb": ruta_local,
                "planta": planta,
                "nombre_comun": enfermedad,
                "clase_id": clase_id,  # para trazabilidad
                "subset": subset
            })

    if not split_data:
        if solo_validadas:
            raise ValueError(
                "No se han podido generar muestras para train/val/test con solo imágenes validadas."
            )
        raise ValueError("No se han podido generar muestras para train/val/test con los filtros seleccionados.")


    config["plantas"] = plantas_filtradas
    config["enfermedades"] = enfermedades_filtradas


    df = pd.DataFrame(split_data)
    os.makedirs(save_dir, exist_ok=True)

    for subset in ["train", "val", "test"]:
        df[df["subset"] == subset].to_csv(os.path.join(save_dir, f"{subset}.csv"), index=False)

    print("CSVs guardados en la carpeta data/:")
    print(df["subset"].value_counts())

    return config


class PlantDataset(Dataset):
    def __init__(self, csv_path, plantas, enfermedades, transform=None):
        self.data = pd.read_csv(csv_path)
        self.transform = transform

        self.planta_to_idx = {c: i for i, c in enumerate(plantas)}
        self.enfermedad_to_idx = {e: i for i, e in enumerate(enfermedades)}

        self.idx_to_planta = {i: c for c, i in self.planta_to_idx.items()}
        self.idx_to_enfermedad = {i: e for e, i in self.enfermedad_to_idx.items()}

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        row = self.data.iloc[idx]
        image_path = row["imagen_rgb"]
        planta = self.planta_to_idx[row["planta"]]
        enfermedad = self.enfermedad_to_idx[row["nombre_comun"]]
        image = Image.open(image_path).convert("RGB")

        if self.transform:
            image = self.transform(image)

        return image, (planta, enfermedad)

def get_dataloader_from_csv(csv_path, config):
    image_size = tuple(config["image_size"])
    batch_size = config["batch_size"]
    transform = transforms.Compose([
        transforms.Resize(image_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                            std=[0.229, 0.224, 0.225])
    ])

    plantas = config["plantas"]
    enfermedades = config["enfermedades"]

    train_ds = PlantDataset(os.path.join(csv_path, "train.csv"), plantas, enfermedades, transform=transform)
    val_ds = PlantDataset(os.path.join(csv_path, "val.csv"), plantas, enfermedades, transform=transform)
    test_ds = PlantDataset(os.path.join(csv_path, "test.csv"), plantas, enfermedades, transform=transform)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)
    test_loader = DataLoader(test_ds, batch_size=batch_size)

    return train_loader, val_loader, test_loader
