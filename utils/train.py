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
        raise ValueError(f"❌ Optimizador no soportado: {opt_name}")

    wp = config["peso_planta"]
    we = config["peso_enfermedad"]

    # PARA LOS CRITERIOS DE PÉRDIDA USAMOS PESOS INVERSOS POR CLASE PARA CONTRARRESTAR EL DESBALANCEO
    df = pd.read_csv(os.path.join(data_dir, "train.csv"))
    plantas = config["plantas"]
    enfermedades = config["enfermedades"]

    conteo_plantas = Counter(df["planta"])
    conteo_enfermedades = Counter(df["nombre_comun"])

    use_weights = config.get("use_class_weights", False)
    min_samples = config.get("min_samples_per_class", 10)

    # Avisos si hay clases con muy pocas muestras
    for p in plantas:
        if conteo_plantas.get(p, 0) < min_samples:
            print(f"⚠️ Clase planta '{p}' tiene solo {conteo_plantas[p]} imágenes.")
    for e in enfermedades:
        if conteo_enfermedades.get(e, 0) < min_samples:
            print(f"⚠️ Clase enfermedad '{e}' tiene solo {conteo_enfermedades[e]} imágenes.")

    # Crear funciones de pérdida
    if use_weights:
        print("🧮 Usando ponderación automática por frecuencia de clase.")

        # Pesos inversos normalizados
        pesos_planta = [1.0 / conteo_plantas.get(p, 1) for p in plantas]
        pesos_enfermedad = [1.0 / conteo_enfermedades.get(e, 1) for e in enfermedades]

        # Normalizar (media = 1.0)
        mean_p = sum(pesos_planta) / len(pesos_planta)
        mean_e = sum(pesos_enfermedad) / len(pesos_enfermedad)
        pesos_planta = [w / mean_p for w in pesos_planta]
        pesos_enfermedad = [w / mean_e for w in pesos_enfermedad]

        pesos_planta = torch.tensor(pesos_planta, dtype=torch.float32).to(device)
        pesos_enfermedad = torch.tensor(pesos_enfermedad, dtype=torch.float32).to(device)

        criterion_planta = nn.CrossEntropyLoss(weight=pesos_planta)
        criterion_enfermedad = nn.CrossEntropyLoss(weight=pesos_enfermedad)
    else:
        criterion_planta = nn.CrossEntropyLoss()
        criterion_enfermedad = nn.CrossEntropyLoss()

    optimizer = optim.Adam(model.parameters(), lr=lr)

    history = {
        "train_loss_planta": [],
        "train_loss_enfermedad": [],
        "val_loss_planta": [],
        "val_loss_enfermedad": []
    }

    for epoch in range(epochs):
        model.train()
        running_loss_planta = 0.0
        running_loss_enfermedad = 0.0

        for images, (labels_planta, labels_enfermedad) in train_loader:
            images = images.to(device)
            labels_planta = labels_planta.to(device)
            labels_enfermedad = labels_enfermedad.to(device)

            optimizer.zero_grad()
            out_planta, out_enfermedad = model(images)

            loss_planta = criterion_planta(out_planta, labels_planta)
            loss_enfermedad = criterion_enfermedad(out_enfermedad, labels_enfermedad)
            loss = wp * loss_planta + we * loss_enfermedad

            loss.backward()
            optimizer.step()

            running_loss_planta += loss_planta.item()
            running_loss_enfermedad += loss_enfermedad.item()

        avg_train_loss_planta = running_loss_planta / len(train_loader)
        avg_train_loss_enfermedad = running_loss_enfermedad / len(train_loader)

        history["train_loss_planta"].append(avg_train_loss_planta)
        history["train_loss_enfermedad"].append(avg_train_loss_enfermedad)

        # --- Validación ---
        model.eval()
        val_loss_planta = 0.0
        val_loss_enfermedad = 0.0
        with torch.no_grad():
            for images, (labels_planta, labels_enfermedad) in val_loader:
                images = images.to(device)
                labels_planta = labels_planta.to(device)
                labels_enfermedad = labels_enfermedad.to(device)

                out_planta, out_enfermedad = model(images)

                loss_planta = criterion_planta(out_planta, labels_planta)
                loss_enfermedad = criterion_enfermedad(out_enfermedad, labels_enfermedad)

                val_loss_planta += loss_planta.item()
                val_loss_enfermedad += loss_enfermedad.item()

        avg_val_loss_planta = val_loss_planta / len(val_loader)
        avg_val_loss_enfermedad = val_loss_enfermedad / len(val_loader)

        history["val_loss_planta"].append(avg_val_loss_planta)
        history["val_loss_enfermedad"].append(avg_val_loss_enfermedad)

        print(f"Epoch {epoch+1}/{epochs} - "
              f"Train: planta={avg_train_loss_planta:.4f}, enfermedad={avg_train_loss_enfermedad:.4f} | "
              f"Val: planta={avg_val_loss_planta:.4f}, enfermedad={avg_val_loss_enfermedad:.4f}")

    return model, history


def evaluate(model, dataloader, config, DATA_DIR, results_dir, split_name="val", device="cuda"):
    model = model.to(device)
    model.eval()

    planta_to_idx = {c: i for i, c in enumerate(config["plantas"])}
    enfermedad_to_idx = {e: i for i, e in enumerate(config["enfermedades"])}
    idx_to_planta = {i: c for c, i in planta_to_idx.items()}
    idx_to_enfermedad = {i: e for e, i in enfermedad_to_idx.items()}

    df = pd.read_csv(os.path.join(DATA_DIR, "train.csv"))
    combinaciones_validas = set(zip(df["planta"], df["nombre_comun"]))

    correct_planta = 0
    correct_enfermedad = 0
    correct_comb = 0
    total = 0

    all_preds_planta = []
    all_preds_enfermedad = []
    all_labels_planta = []
    all_labels_enfermedad = []

    misclassified = []  # Lista para almacenar imágenes mal clasificadas

    with torch.no_grad():
        for images, (labels_planta, labels_enfermedad) in dataloader:
            images = images.to(device)
            labels_planta = labels_planta.to(device)
            labels_enfermedad = labels_enfermedad.to(device)

            out_planta, out_enfermedad = model(images)
            probs_planta = torch.softmax(out_planta, dim=1)
            probs_enfermedad = torch.softmax(out_enfermedad, dim=1)

            batch_size = images.size(0)
            total += batch_size

            for i in range(batch_size):
                pred_c = probs_planta[i].argmax().item()
                pred_e = probs_enfermedad[i].argmax().item()

                planta_str = idx_to_planta[pred_c]
                enfermedad_str = idx_to_enfermedad[pred_e]

                if (planta_str, enfermedad_str) not in combinaciones_validas:
                    best_pair = max(
                        combinaciones_validas,
                        key=lambda pair: probs_planta[i][planta_to_idx[pair[0]]] *
                                         probs_enfermedad[i][enfermedad_to_idx[pair[1]]]
                    )
                    planta_str, enfermedad_str = best_pair
                    pred_c = planta_to_idx[planta_str]
                    pred_e = enfermedad_to_idx[enfermedad_str]

                if pred_c == labels_planta[i].item():
                    correct_planta += 1
                if pred_e == labels_enfermedad[i].item():
                    correct_enfermedad += 1
                if (pred_c == labels_planta[i].item()) and (pred_e == labels_enfermedad[i].item()):
                    correct_comb += 1

                all_preds_planta.append(pred_c)
                all_preds_enfermedad.append(pred_e)
                all_labels_planta.append(labels_planta[i].item())
                all_labels_enfermedad.append(labels_enfermedad[i].item())

                if pred_c != labels_planta[i].item() or pred_e != labels_enfermedad[i].item():
                    misclassified.append({
                        "filename": dataloader.dataset.data.iloc[i]["imagen_rgb"],  # Ruta de la imagen
                        "predicted": {
                            "planta": planta_str,
                            "enfermedad": enfermedad_str
                        },
                        "actual": {
                            "planta": idx_to_planta[labels_planta[i].item()],
                            "enfermedad": idx_to_enfermedad[labels_enfermedad[i].item()]
                        }
                    })

    acc_planta = correct_planta / total
    acc_enfermedad = correct_enfermedad / total
    acc_combinada = correct_comb / total

    # Métricas adicionales
    metrics = {
        "accuracy_planta": acc_planta,
        "accuracy_enfermedad": acc_enfermedad,
        "accuracy_combinada": acc_combinada,
        "f1_planta": f1_score(all_labels_planta, all_preds_planta, average="macro"),
        "f1_enfermedad": f1_score(all_labels_enfermedad, all_preds_enfermedad, average="macro"),
        "precision_planta": precision_score(all_labels_planta, all_preds_planta, average="macro"),
        "precision_enfermedad": precision_score(all_labels_enfermedad, all_preds_enfermedad, average="macro"),
        "recall_planta": recall_score(all_labels_planta, all_preds_planta, average="macro"),
        "recall_enfermedad": recall_score(all_labels_enfermedad, all_preds_enfermedad, average="macro"),
    }

    # Guardar matriz de confusión solo si es split de test
    if split_name == "test":
        save_confusion_matrix(all_labels_planta, all_preds_planta, list(config["plantas"]),
                            f"Matriz de confusión - Planta ({split_name})",
                            os.path.join(results_dir, f"confusion_planta.png"))

        save_confusion_matrix(all_labels_enfermedad, all_preds_enfermedad, list(config["enfermedades"]),
                            f"Matriz de confusión - Enfermedad ({split_name})",
                            os.path.join(results_dir, f"confusion_enfermedad.png"))


    # Guardar imágenes mal clasificadas
    if misclassified:
        misclassified_path = os.path.join(results_dir, "misclassified.json")
        with open(misclassified_path, "w") as f:
            json.dump(misclassified, f, indent=4)
        print(f"💾 Archivo 'misclassified.json' guardado en {misclassified_path}")

    print(f"🎯 {split_name.upper()} — Accuracy: planta={acc_planta:.4f}, enfermedad={acc_enfermedad:.4f}, combinada={acc_combinada:.4f}")
    return metrics

