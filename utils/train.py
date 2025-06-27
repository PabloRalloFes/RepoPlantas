import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import os

def train_model(model, train_loader, val_loader, config):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)

    epochs = config["epochs"]
    lr = config["lr"]

    # Dos funciones de pérdida
    criterion_cultivo = nn.CrossEntropyLoss()
    criterion_enfermedad = nn.CrossEntropyLoss()

    optimizer = optim.Adam(model.parameters(), lr=lr)

    history = {
        "train_loss_cultivo": [],
        "train_loss_enfermedad": [],
        "val_loss_cultivo": [],
        "val_loss_enfermedad": []
    }

    for epoch in range(epochs):
        model.train()
        running_loss_cultivo = 0.0
        running_loss_enfermedad = 0.0

        for images, (labels_cultivo, labels_enfermedad) in train_loader:
            images = images.to(device)
            labels_cultivo = labels_cultivo.to(device)
            labels_enfermedad = labels_enfermedad.to(device)

            optimizer.zero_grad()
            out_cultivo, out_enfermedad = model(images)

            loss_cultivo = criterion_cultivo(out_cultivo, labels_cultivo)
            loss_enfermedad = criterion_enfermedad(out_enfermedad, labels_enfermedad)
            loss = loss_cultivo + loss_enfermedad

            loss.backward()
            optimizer.step()

            running_loss_cultivo += loss_cultivo.item()
            running_loss_enfermedad += loss_enfermedad.item()

        avg_train_loss_cultivo = running_loss_cultivo / len(train_loader)
        avg_train_loss_enfermedad = running_loss_enfermedad / len(train_loader)

        history["train_loss_cultivo"].append(avg_train_loss_cultivo)
        history["train_loss_enfermedad"].append(avg_train_loss_enfermedad)

        # --- Validación ---
        model.eval()
        val_loss_cultivo = 0.0
        val_loss_enfermedad = 0.0
        with torch.no_grad():
            for images, (labels_cultivo, labels_enfermedad) in val_loader:
                images = images.to(device)
                labels_cultivo = labels_cultivo.to(device)
                labels_enfermedad = labels_enfermedad.to(device)

                out_cultivo, out_enfermedad = model(images)

                loss_cultivo = criterion_cultivo(out_cultivo, labels_cultivo)
                loss_enfermedad = criterion_enfermedad(out_enfermedad, labels_enfermedad)

                val_loss_cultivo += loss_cultivo.item()
                val_loss_enfermedad += loss_enfermedad.item()

        avg_val_loss_cultivo = val_loss_cultivo / len(val_loader)
        avg_val_loss_enfermedad = val_loss_enfermedad / len(val_loader)

        history["val_loss_cultivo"].append(avg_val_loss_cultivo)
        history["val_loss_enfermedad"].append(avg_val_loss_enfermedad)

        print(f"Epoch {epoch+1}/{epochs} - "
              f"Train: cultivo={avg_train_loss_cultivo:.4f}, enfermedad={avg_train_loss_enfermedad:.4f} | "
              f"Val: cultivo={avg_val_loss_cultivo:.4f}, enfermedad={avg_val_loss_enfermedad:.4f}")

    return model, history


def evaluate(model, dataloader, config, DATA_DIR, device="cuda"):
    model = model.to(device)
    model.eval()

    cultivo_to_idx = {c: i for i, c in enumerate(config["cultivos"])}
    enfermedad_to_idx = {e: i for i, e in enumerate(config["enfermedades"])}
    idx_to_cultivo = {i: c for c, i in cultivo_to_idx.items()}
    idx_to_enfermedad = {i: e for e, i in enfermedad_to_idx.items()}

    # Set de combinaciones válidas
    df = pd.read_csv(os.path.join(DATA_DIR, "train.csv"))
    combinaciones_validas = set(zip(df["cultivo"], df["enfermedad"]))

    correct_cultivo = 0
    correct_enfermedad = 0
    correct_comb = 0
    total = 0

    with torch.no_grad():
        for images, (labels_cultivo, labels_enfermedad) in dataloader:
            images = images.to(device)
            labels_cultivo = labels_cultivo.to(device)
            labels_enfermedad = labels_enfermedad.to(device)

            out_cultivo, out_enfermedad = model(images)

            probs_cultivo = torch.softmax(out_cultivo, dim=1)
            probs_enfermedad = torch.softmax(out_enfermedad, dim=1)

            batch_size = images.size(0)
            total += batch_size

            for i in range(batch_size):
                # Predicciones independientes
                pred_c = probs_cultivo[i].argmax().item()
                pred_e = probs_enfermedad[i].argmax().item()

                cultivo_str = idx_to_cultivo[pred_c]
                enfermedad_str = idx_to_enfermedad[pred_e]

                # Reasignar si no es válida
                if (cultivo_str, enfermedad_str) not in combinaciones_validas:
                    # Buscar la combinación válida con mayor probabilidad conjunta
                    best_pair = max(
                        combinaciones_validas,
                        key=lambda pair: probs_cultivo[i][cultivo_to_idx[pair[0]]] *
                                         probs_enfermedad[i][enfermedad_to_idx[pair[1]]]
                    )
                    cultivo_str, enfermedad_str = best_pair
                    pred_c = cultivo_to_idx[cultivo_str]
                    pred_e = enfermedad_to_idx[enfermedad_str]

                # Comparar con etiquetas reales
                if pred_c == labels_cultivo[i].item():
                    correct_cultivo += 1
                if pred_e == labels_enfermedad[i].item():
                    correct_enfermedad += 1
                if (pred_c == labels_cultivo[i].item()) and (pred_e == labels_enfermedad[i].item()):
                    correct_comb += 1

    acc_cultivo = correct_cultivo / total
    acc_enfermedad = correct_enfermedad / total
    acc_combinada = correct_comb / total

    print(f"🎯 Accuracy - Cultivo: {acc_cultivo:.4f} | Enfermedad: {acc_enfermedad:.4f} | Combinada: {acc_combinada:.4f}")

    return acc_cultivo, acc_enfermedad, acc_combinada

