import os
import random
from pathlib import Path

import pandas as pd
import torch
from PIL import Image
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms

from utils.database import get_project_config


def _normalize_list(values):
    if values is None:
        return []
    if not isinstance(values, list):
        values = [values]
    return [value for value in values if isinstance(value, (str, int, float, bool)) and str(value).strip() != ""]


def _extract_class_value(doc, field_name: str):
    if field_name in doc and doc[field_name] is not None:
        return doc[field_name]
    if field_name == "class_label":
        return doc.get("class_label") or doc.get("clase") or doc.get("nombre")
    if field_name == "clase":
        return doc.get("clase") or doc.get("class_label") or doc.get("nombre")
    if field_name == "nombre":
        return doc.get("nombre") or doc.get("class_label") or doc.get("clase")
    return doc.get(field_name)


def _resolve_target_fields(db, config):
    project_config = get_project_config(db=db)
    target_fields = config.get("target_fields") or project_config.get("target_fields") or ["class_label"]
    target_fields = _normalize_list(target_fields)
    if not target_fields:
        target_fields = ["class_label"]
    return target_fields


def prepare_data_splits(db, config, save_dir):
    """
    Prepara los CSVs con rutas a imágenes y etiquetas para train/val/test.
    La etiqueta se construye a partir de los campos definidos en ProjectConfig.
    """
    target_fields = _resolve_target_fields(db, config)
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
        priority = [field_name, "nombre", "clase", "class_label", "name", "valor", "descripcion", "fuente", "formato"]
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

    projection = {"_id": 1, "class_label": 1, "nombre": 1, "clase": 1}
    for field_name in target_fields:
        projection[field_name] = 1

    clases_todas = list(db["Clases"].find({}, projection))
    class_docs = []
    for doc in clases_todas:
        clean_doc = {"_id": doc["_id"]}

        # Resolve a human-readable label: prefer explicit fields but
        # fall back to composing from target fields (supports multi-target).
        class_label = str(_extract_class_value(doc, "class_label") or "").strip()
        nombre = str(_extract_class_value(doc, "nombre") or "").strip()
        clase = str(_extract_class_value(doc, "clase") or "").strip()
        class_label = class_label or clase or nombre

        if not class_label:
            # Build composite label from target fields (e.g. "Apple | healthy").
            parts = []
            for f in target_fields:
                v = _extract_class_value(doc, f)
                if v is not None and str(v).strip() != "":
                    parts.append(str(v).strip())
            composite = " | ".join(parts)
            class_label = composite or None

        if not class_label:
            # If still missing, skip this class doc as invalid.
            continue

        clean_doc["class_label"] = class_label
        clean_doc["nombre"] = nombre or class_label
        clean_doc["clase"] = clase or class_label

        # Ensure all target fields exist on the class document.
        for field_name in target_fields:
            field_value = _extract_class_value(doc, field_name)
            if field_value is None or str(field_value).strip() == "":
                raise ValueError(f"La colección Clases no contiene el campo objetivo '{field_name}' en todos los documentos.")
            clean_doc[field_name] = field_value

        class_docs.append(clean_doc)

    if not class_docs:
        raise ValueError("No se han encontrado clases válidas en la colección Clases.")

    selected_classes = normalize_selected_values(clases_seleccionadas)
    if not selected_classes or "all" in [str(v).lower() for v in selected_classes]:
        selected_classes = sorted({doc["class_label"] for doc in class_docs}, key=lambda x: x.lower())

    class_docs = [doc for doc in class_docs if doc["class_label"] in set(selected_classes)]
    if not class_docs:
        raise ValueError("No se han encontrado clases válidas con los filtros actuales del config.")

    class_ids = [doc["_id"] for doc in class_docs]

    print(f"Se han encontrado {len(class_ids)} clases válidas para clasificación simple.")

    target_classes = {}
    target_class_to_idx = {}
    for field_name in target_fields:
        field_values = sorted({str(doc[field_name]).strip() for doc in class_docs if str(doc.get(field_name, "")).strip() != ""}, key=lambda x: x.lower())
        if not field_values:
            raise ValueError(f"No se han encontrado valores válidos para el campo objetivo '{field_name}'.")
        target_classes[field_name] = field_values
        target_class_to_idx[field_name] = {value: index for index, value in enumerate(field_values)}

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
        "target_fields",
        "target_classes",
        "target_class_to_idx",
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

            row = {
                "imagen_rgb": ruta_local,
                "class_label": class_info["class_label"],
                "nombre": class_info["nombre"],
                "clase": class_info["clase"],
                "clase_id": clase_id,
                "subset": subset,
            }
            for field_name in target_fields:
                row[field_name] = class_info[field_name]
            split_data.append(row)

    if not split_data:
        if solo_validadas:
            raise ValueError("No se han podido generar muestras para train/val/test con solo imágenes validadas.")
        raise ValueError("No se han podido generar muestras para train/val/test con los filtros seleccionados.")

    config["target_fields"] = target_fields
    config["target_classes"] = target_classes
    config["target_class_to_idx"] = target_class_to_idx

    if len(target_fields) == 1:
        config["classes"] = target_classes[target_fields[0]]
        config["class_field"] = target_fields[0]
    else:
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
    def __init__(self, csv_path, classes, transform=None, class_field="class_label", target_fields=None, target_class_to_idx=None):
        self.data = pd.read_csv(csv_path)
        self.transform = transform
        self.class_field = class_field if class_field in self.data.columns else None
        self.target_fields = target_fields or []
        self.target_class_to_idx = target_class_to_idx or {}

        self.class_to_idx = {class_name: i for i, class_name in enumerate(classes)}
        self.idx_to_class = {i: class_name for class_name, i in self.class_to_idx.items()}

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        row = self.data.iloc[idx]
        image_path = row["imagen_rgb"]

        if len(self.target_fields) > 1:
            labels = []
            for field_name in self.target_fields:
                field_value = row.get(field_name)
                if field_value is None or str(field_value).strip() == "":
                    field_value = row.get("class_label") or row.get("clase") or row.get("nombre")
                field_value = str(field_value).strip()
                field_to_idx = self.target_class_to_idx.get(field_name, {})
                if field_value not in field_to_idx:
                    raise KeyError(f"El valor '{field_value}' no existe en el vocabulario del campo '{field_name}'.")
                labels.append(field_to_idx[field_value])
            label = torch.tensor(labels, dtype=torch.long)
        else:
            if self.class_field and self.class_field in row:
                class_label = row[self.class_field]
            elif "class_label" in row:
                class_label = row["class_label"]
            else:
                class_label = row.get("class_label") or row.get("clase") or row.get("nombre")

            label = self.class_to_idx[str(class_label)]
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
    target_fields = config.get("target_fields", [class_field])
    target_class_to_idx = config.get("target_class_to_idx", {})

    train_ds = GenericDataset(os.path.join(csv_path, "train.csv"), classes, transform=transform, class_field=class_field, target_fields=target_fields, target_class_to_idx=target_class_to_idx)
    val_ds = GenericDataset(os.path.join(csv_path, "val.csv"), classes, transform=transform, class_field=class_field, target_fields=target_fields, target_class_to_idx=target_class_to_idx)
    test_ds = GenericDataset(os.path.join(csv_path, "test.csv"), classes, transform=transform, class_field=class_field, target_fields=target_fields, target_class_to_idx=target_class_to_idx)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)
    test_loader = DataLoader(test_ds, batch_size=batch_size)

    return train_loader, val_loader, test_loader
