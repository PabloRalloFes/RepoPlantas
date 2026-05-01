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

    if opt_name == "adam":
        optimizer = optim.Adam(model.parameters(), lr=lr)
    elif opt_name == "sgd":
        optimizer = optim.SGD(model.parameters(), lr=lr, momentum=0.9)
    else:
        raise ValueError(f" Optimizador no soportado: {opt_name}")

    # Clasificación simple: una sola pérdida y una sola salida.
    df = pd.read_csv(os.path.join(data_dir, "train.csv"))
    class_field = config.get("class_field", "class_label")
    classes = config["classes"]

    if class_field not in df.columns:
        if {"planta", "nombre_comun"}.issubset(df.columns):
            df[class_field] = df["planta"].astype(str) + "___" + df["nombre_comun"].astype(str)
        else:
            raise ValueError(f"El CSV de entrenamiento no contiene la columna '{class_field}'.")

    conteo_clases = Counter(df[class_field])

    use_weights = config.get("use_class_weights", False)
    min_samples = config.get("min_samples_per_class", 10)

    # Avisos si hay clases con muy pocas muestras
    for class_name in classes:
        if conteo_clases.get(class_name, 0) < min_samples:
            print(f"Clase '{class_name}' tiene solo {conteo_clases.get(class_name, 0)} imágenes.")

    # Crear funciones de pérdida
    if use_weights:
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

    with torch.no_grad():
        global_idx = 0
        for images, labels in dataloader:
            images = images.to(device)
            labels = labels.to(device)

            output = model(images)
            probs = torch.softmax(output, dim=1)

            batch_size = images.size(0)
            total += batch_size

            for i in range(batch_size):
                pred = probs[i].argmax().item()
                pred_class = idx_to_class[pred]
                true_class = idx_to_class[labels[i].item()]

                if pred == labels[i].item():
                    correct += 1

                all_preds.append(pred)
                all_labels.append(labels[i].item())

                # Usar el índice global real en el dataset
                real_idx = global_idx + i
                if pred != labels[i].item():
                    misclassified.append({
                        "filename": dataloader.dataset.data.iloc[real_idx]["imagen_rgb"],
                        "predicted": pred_class,
                        "actual": true_class
                    })
            global_idx += batch_size

    acc = correct / total

    # Métricas adicionales
    metrics = {
        "accuracy": acc,
        "f1": f1_score(all_labels, all_preds, average="macro"),
        "precision": precision_score(all_labels, all_preds, average="macro"),
        "recall": recall_score(all_labels, all_preds, average="macro"),
    }

    # Guardar matriz de confusión solo si es split de test
    if split_name == "test":
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

