import os
import random
from pathlib import Path

import pandas as pd
from PIL import Image
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms


def prepare_data_splits(db, config, save_dir):
    """
    Prepara los CSVs con rutas a imágenes y etiquetas para train/val/test.
    La etiqueta es única: class_label = planta___nombre_comun.
    """
    fuentes = config.get("fuentes", ["all"])
    imagenes_por_clase = config["imagenes_por_clase"]
    split_ratios = config["split"]
    formato_nombre = config.get("formato")
    clases_seleccionadas = config.get("classes", ["all"])

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

        for candidate in candidates:
            candidate_lower = candidate.lower()
            if candidate_lower in collection_names_lower:
                return collection_names_lower[candidate_lower]
        return None

    def pick_label_field(collection_name, field_name):
        sample = db[collection_name].find_one({}, {"_id": 0}) or {}
        priority = [field_name, "nombre", "name", "valor", "descripcion", "fuente", "formato", "planta", "nombre_comun"]
        for priority_field in priority:
            if priority_field in sample:
                return priority_field
        return next(iter(sample.keys()), None)

    def cast_values_to_doc_types(field_name, selected_values):
        sample_values = [v for v in db["Docs"].distinct(field_name) if is_scalar(v)]
        if not sample_values:
            return selected_values

        has_bool = any(isinstance(v, bool) for v in sample_values)
        has_int = any(isinstance(v, int) and not isinstance(v, bool) for v in sample_values)
        has_float = any(isinstance(v, float) for v in sample_values)

        casted = set(selected_values)
        for value in selected_values:
            if isinstance(value, str):
                text_value = value.strip()
                if has_bool:
                    if text_value.lower() in ("true", "1", "si", "yes"):
                        casted.add(True)
                    elif text_value.lower() in ("false", "0", "no"):
                        casted.add(False)
                if has_int:
                    try:
                        casted.add(int(text_value))
                    except Exception:
                        pass
                if has_float:
                    try:
                        casted.add(float(text_value))
                    except Exception:
                        pass
        return list(casted)

    collection_names_lower = {c.lower(): c for c in db.list_collection_names()}

    clases_todas = list(db["Clases"].find({}, {"_id": 1, "planta": 1, "nombre_comun": 1}))
    class_docs = []
    for doc in clases_todas:
        planta = str(doc.get("planta", "")).strip()
        nombre_comun = str(doc.get("nombre_comun", "")).strip()
        if planta and nombre_comun:
            class_label = f"{planta}___{nombre_comun}"
            class_docs.append({"_id": doc["_id"], "class_label": class_label, "planta": planta, "nombre_comun": nombre_comun})

    if not class_docs:
        raise ValueError("No se han encontrado clases válidas en la colección Clases.")

    selected_classes = normalize_selected_values(clases_seleccionadas)
    if not selected_classes or "all" in [str(v).lower() for v in selected_classes]:
        selected_classes = sorted({doc["class_label"] for doc in class_docs}, key=lambda x: x.lower())

    class_docs = [doc for doc in class_docs if doc["class_label"] in set(selected_classes)]
    if not class_docs:
        raise ValueError("No se han encontrado clases válidas con los filtros actuales del config.")

    class_to_ids = {}
    for doc in class_docs:
        class_to_ids.setdefault(doc["class_label"], []).append(doc["_id"])
    class_ids = [doc["_id"] for doc in class_docs]

    print(f"Se han encontrado {len(class_ids)} clases válidas para clasificación simple.")

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

    no_encontradas = [fuente for fuente in fuentes if fuente not in fuentes_dict]
    if no_encontradas:
        print(f"Fuentes no encontradas en la base de datos: {no_encontradas}")

    docs_query = {"clase": {"$in": class_ids}}
    if formato_id is not None:
        docs_query["formato"] = formato_id
    if fuentes_ids:
        docs_query["fuente"] = {"$in": fuentes_ids}

    solo_validadas = bool(config.get("solo_validadas", False))
    if solo_validadas:
        docs_query["validada"] = True

    reserved_keys = {
        "batch_size",
        "classes",
        "class_field",
        "class_weight",
        "epochs",
        "fine_tune",
        "formato",
        "fuentes",
        "image_size",
        "imagenes_por_clase",
        "lr",
        "min_samples_per_class",
        "optimizer",
        "split",
        "use_class_weights",
        "weights",
        "filtros_docs",
        "solo_validadas",
    }

    for key, raw_selected in config.items():
        if key in reserved_keys:
            continue

        selected = normalize_selected_values(raw_selected)
        if not selected or "all" in [str(v).lower() for v in selected]:
            continue

        selected_candidates = cast_values_to_doc_types(key, selected)
        direct_matches = db["Docs"].count_documents({key: {"$in": selected_candidates}})
        if direct_matches > 0:
            docs_query[key] = {"$in": selected_candidates}
            continue

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

    docs = list(db["Docs"].find(docs_query))
    if not docs:
        if solo_validadas:
            raise ValueError("No se han encontrado documentos para entrenar con los filtros actuales usando solo imágenes validadas.")
        raise ValueError("No se han encontrado documentos para entrenar con los filtros actuales.")

    print(f"Se han encontrado {len(docs)} documentos con los filtros configurados.")

    docs_por_clase = {}
    for doc in docs:
        clase_id = doc.get("clase")
        if clase_id in class_ids:
            docs_por_clase.setdefault(clase_id, []).append(doc)

    if not docs_por_clase:
        if solo_validadas:
            raise ValueError("No hay clases con imágenes disponibles tras aplicar el filtro de solo imágenes validadas.")
        raise ValueError("No hay clases con imágenes disponibles tras aplicar los filtros seleccionados.")

    print(f"Se han encontrado {len(docs_por_clase)} clases con imágenes en formato {formato_nombre}.")

    classes_filtradas = sorted({doc["class_label"] for doc in class_docs if doc["_id"] in docs_por_clase}, key=lambda x: x.lower())

    current_file = Path(__file__).resolve()
    repo_root = current_file.parents[1]
    imagenes_dir = repo_root / "imagenes"

    split_data = []
    for clase_id, lista in docs_por_clase.items():
        random.shuffle(lista)
        if imagenes_por_clase is not None and imagenes_por_clase < len(lista):
            lista = lista[:imagenes_por_clase]

        n_total = len(lista)
        n_train = int(n_total * split_ratios["train"])
        n_val = int(n_total * split_ratios["val"])

        class_info = next(doc for doc in class_docs if doc["_id"] == clase_id)

        for i, doc in enumerate(lista):
            if i < n_train:
                subset = "train"
            elif i < n_train + n_val:
                subset = "val"
            else:
                subset = "test"

            nombre_archivo = doc["imagen_rgb"].split("/")[-1]
            ruta_local = os.path.join(imagenes_dir, nombre_archivo)

            split_data.append({
                "imagen_rgb": ruta_local,
                "class_label": class_info["class_label"],
                "planta": class_info["planta"],
                "nombre_comun": class_info["nombre_comun"],
                "clase_id": clase_id,
                "subset": subset,
            })

    if not split_data:
        if solo_validadas:
            raise ValueError("No se han podido generar muestras para train/val/test con solo imágenes validadas.")
        raise ValueError("No se han podido generar muestras para train/val/test con los filtros seleccionados.")

    config["classes"] = classes_filtradas
    config["class_field"] = "class_label"

    df = pd.DataFrame(split_data)
    os.makedirs(save_dir, exist_ok=True)

    for subset in ["train", "val", "test"]:
        df[df["subset"] == subset].to_csv(os.path.join(save_dir, f"{subset}.csv"), index=False)

    print("CSVs guardados en la carpeta data/:")
    print(df["subset"].value_counts())

    return config


class GenericDataset(Dataset):
    def __init__(self, csv_path, classes, transform=None, class_field="class_label"):
        self.data = pd.read_csv(csv_path)
        self.transform = transform
        self.class_field = class_field if class_field in self.data.columns else None

        self.class_to_idx = {class_name: i for i, class_name in enumerate(classes)}
        self.idx_to_class = {i: class_name for class_name, i in self.class_to_idx.items()}

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        row = self.data.iloc[idx]
        image_path = row["imagen_rgb"]

        if self.class_field and self.class_field in row:
            class_label = row[self.class_field]
        elif "class_label" in row:
            class_label = row["class_label"]
        else:
            class_label = f"{row['planta']}___{row['nombre_comun']}"

        label = self.class_to_idx[class_label]
        image = Image.open(image_path).convert("RGB")

        if self.transform:
            image = self.transform(image)

        return image, label


PlantDataset = GenericDataset


def get_dataloader_from_csv(csv_path, config):
    image_size = tuple(config["image_size"])
    batch_size = config["batch_size"]
    transform = transforms.Compose([
        transforms.Resize(image_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    classes = config["classes"]
    class_field = config.get("class_field", "class_label")

    train_ds = GenericDataset(os.path.join(csv_path, "train.csv"), classes, transform=transform, class_field=class_field)
    val_ds = GenericDataset(os.path.join(csv_path, "val.csv"), classes, transform=transform, class_field=class_field)
    test_ds = GenericDataset(os.path.join(csv_path, "test.csv"), classes, transform=transform, class_field=class_field)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)
    test_loader = DataLoader(test_ds, batch_size=batch_size)

    return train_loader, val_loader, test_loader
