import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import os
from utils.io import save_confusion_matrix
from sklearn.metrics import precision_score, recall_score, f1_score
from collections import Counter
import json  # Importar json para guardar el archivo de imágenes mal clasificadas

def train_model(model, train_loader, val_loader, config, data_dir):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)

    epochs = config["epochs"]
    lr = config["lr"]
    opt_name = config["optimizer"].lower()
    target_fields = config.get("target_fields", [config.get("class_field", "class_label")])
    multi_target = len(target_fields) > 1

    if opt_name == "adam":
        optimizer = optim.Adam(model.parameters(), lr=lr)
    elif opt_name == "sgd":
        optimizer = optim.SGD(model.parameters(), lr=lr, momentum=0.9)
    else:
        raise ValueError(f" Optimizador no soportado: {opt_name}")

    df = pd.read_csv(os.path.join(data_dir, "train.csv"))
    class_field = config.get("class_field", "class_label")
    classes = config["classes"]

    if multi_target:
        for field_name in target_fields:
            if field_name not in df.columns:
                raise ValueError(f"El CSV de entrenamiento no contiene la columna objetivo '{field_name}'.")
    else:
        if class_field not in df.columns:
            if {"planta", "nombre_comun"}.issubset(df.columns):
                df[class_field] = df["planta"].astype(str) + "___" + df["nombre_comun"].astype(str)
            else:
                raise ValueError(f"El CSV de entrenamiento no contiene la columna '{class_field}'.")

        conteo_clases = Counter(df[class_field])

    use_weights = config.get("use_class_weights", False)
    min_samples = config.get("min_samples_per_class", 10)

    # Avisos si hay clases con muy pocas muestras
    if not multi_target:
        for class_name in classes:
            if conteo_clases.get(class_name, 0) < min_samples:
                print(f"Clase '{class_name}' tiene solo {conteo_clases.get(class_name, 0)} imágenes.")

    # Crear funciones de pérdida
    if use_weights and not multi_target:
        print("Usando ponderación automática por frecuencia de clase.")

        pesos_clases = [1.0 / conteo_clases.get(class_name, 1) for class_name in classes]
        mean_w = sum(pesos_clases) / len(pesos_clases)
        pesos_clases = [weight / mean_w for weight in pesos_clases]
        pesos_clases = torch.tensor(pesos_clases, dtype=torch.float32).to(device)
        criterion = nn.CrossEntropyLoss(weight=pesos_clases)
    else:
        criterion = nn.CrossEntropyLoss()

    if opt_name == "adam":
        optimizer = optim.Adam(model.parameters(), lr=lr)
    elif opt_name == "sgd":
        optimizer = optim.SGD(model.parameters(), lr=lr, momentum=0.9)
    else:
        raise ValueError(f" Optimizador no soportado: {opt_name}")

    history = {
        "train_loss": [],
        "val_loss": []
    }

    for epoch in range(epochs):
        model.train()
        running_loss = 0.0

        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            output = model(images)
            if multi_target:
                loss = 0.0
                for head_idx, head_output in enumerate(output):
                    loss = loss + criterion(head_output, labels[:, head_idx])
            else:
                loss = criterion(output, labels)

            loss.backward()
            optimizer.step()

            running_loss += loss.item()

        avg_train_loss = running_loss / len(train_loader)

        history["train_loss"].append(avg_train_loss)

        # --- Validación ---
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(device)
                labels = labels.to(device)

                output = model(images)
                if multi_target:
                    loss = 0.0
                    for head_idx, head_output in enumerate(output):
                        loss = loss + criterion(head_output, labels[:, head_idx])
                else:
                    loss = criterion(output, labels)

                val_loss += loss.item()

        avg_val_loss = val_loss / len(val_loader)

        history["val_loss"].append(avg_val_loss)

        print(f"Epoch {epoch+1}/{epochs} - Train loss={avg_train_loss:.4f} | Val loss={avg_val_loss:.4f}")

    return model, history


def evaluate(model, dataloader, config, DATA_DIR, results_dir, split_name="test", device=None):
    # Detectar dispositivo automáticamente si no se especifica
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    
    model = model.to(device)
    model.eval()

    df = pd.read_csv(os.path.join(DATA_DIR, "train.csv"))
    class_field = config.get("class_field", "class_label")
    classes = config["classes"]
    target_fields = config.get("target_fields", [class_field])
    multi_target = len(target_fields) > 1

    if multi_target:
        for field_name in target_fields:
            if field_name not in df.columns:
                raise ValueError(f"El CSV de entrenamiento no contiene la columna objetivo '{field_name}'.")
    else:
        if class_field not in df.columns:
            if {"planta", "nombre_comun"}.issubset(df.columns):
                df[class_field] = df["planta"].astype(str) + "___" + df["nombre_comun"].astype(str)
            else:
                raise ValueError(f"El CSV de entrenamiento no contiene la columna '{class_field}'.")

        class_to_idx = {c: i for i, c in enumerate(classes)}
        idx_to_class = {i: c for c, i in class_to_idx.items()}

    correct = 0
    total = 0

    all_preds = []
    all_labels = []

    misclassified = []  # Lista para almacenar imágenes mal clasificadas
    per_target_predictions = {field_name: {"labels": [], "preds": []} for field_name in target_fields} if multi_target else None

    with torch.no_grad():
        global_idx = 0
        for images, labels in dataloader:
            images = images.to(device)
            labels = labels.to(device)

            output = model(images)
            if multi_target:
                probs = [torch.softmax(head_output, dim=1) for head_output in output]
            else:
                probs = torch.softmax(output, dim=1)

            batch_size = images.size(0)
            total += batch_size

            for i in range(batch_size):
                real_idx = global_idx + i
                if multi_target:
                    sample_correct = True
                    predicted_fields = {}
                    actual_fields = {}
                    for head_idx, field_name in enumerate(target_fields):
                        pred = probs[head_idx][i].argmax().item()
                        true = labels[i][head_idx].item()
                        predicted_fields[field_name] = int(pred)
                        actual_fields[field_name] = int(true)
                        per_target_predictions[field_name]["preds"].append(pred)
                        per_target_predictions[field_name]["labels"].append(true)
                        all_preds.append(pred)
                        all_labels.append(true)
                        if pred != true:
                            sample_correct = False
                    if sample_correct:
                        correct += 1
                    else:
                        misclassified.append({
                            "filename": dataloader.dataset.data.iloc[real_idx]["imagen_rgb"],
                            "predicted": predicted_fields,
                            "actual": actual_fields,
                        })
                else:
                    pred = probs[i].argmax().item()
                    pred_class = idx_to_class[pred]
                    true_class = idx_to_class[labels[i].item()]

                    if pred == labels[i].item():
                        correct += 1

                    all_preds.append(pred)
                    all_labels.append(labels[i].item())

                    if pred != labels[i].item():
                        misclassified.append({
                            "filename": dataloader.dataset.data.iloc[real_idx]["imagen_rgb"],
                            "predicted": pred_class,
                            "actual": true_class
                        })
            global_idx += batch_size

    acc = correct / total

    if multi_target:
        per_target_metrics = {}
        f1_values = []
        precision_values = []
        recall_values = []
        for field_name in target_fields:
            field_labels = per_target_predictions[field_name]["labels"]
            field_preds = per_target_predictions[field_name]["preds"]
            field_metrics = {
                "accuracy": sum(int(p == t) for p, t in zip(field_preds, field_labels)) / len(field_labels) if field_labels else 0.0,
                "f1": f1_score(field_labels, field_preds, average="macro") if field_labels else 0.0,
                "precision": precision_score(field_labels, field_preds, average="macro") if field_labels else 0.0,
                "recall": recall_score(field_labels, field_preds, average="macro") if field_labels else 0.0,
            }
            per_target_metrics[field_name] = field_metrics
            f1_values.append(field_metrics["f1"])
            precision_values.append(field_metrics["precision"])
            recall_values.append(field_metrics["recall"])

        metrics = {
            "accuracy": acc,
            "f1": sum(f1_values) / len(f1_values) if f1_values else 0.0,
            "precision": sum(precision_values) / len(precision_values) if precision_values else 0.0,
            "recall": sum(recall_values) / len(recall_values) if recall_values else 0.0,
            "per_target": per_target_metrics,
        }
    else:
        metrics = {
            "accuracy": acc,
            "f1": f1_score(all_labels, all_preds, average="macro"),
            "precision": precision_score(all_labels, all_preds, average="macro"),
            "recall": recall_score(all_labels, all_preds, average="macro"),
        }

    # Guardar matriz de confusión solo si es split de test
    if split_name == "test" and not multi_target:
        save_confusion_matrix(all_labels, all_preds, list(classes),
                            f"Matriz de confusión - Clase ({split_name})",
                            os.path.join(results_dir, "confusion_class.png"))


    # Guardar imágenes mal clasificadas
    if misclassified:
        misclassified_path = os.path.join(results_dir, f"misclassified_{split_name}.json")
        with open(misclassified_path, "w") as f:
            json.dump(misclassified, f, indent=4)
        print(f"Archivo 'misclassified_{split_name}.json' guardado en {misclassified_path}")

    print(f"{split_name.upper()} — Accuracy: {acc:.4f}")
    return metrics

