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
            loss = loss_planta + loss_enfermedad

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


def evaluate(model, dataloader, config, DATA_DIR, device="cuda"):
    model = model.to(device)
    model.eval()

    planta_to_idx = {c: i for i, c in enumerate(config["plantas"])}
    enfermedad_to_idx = {e: i for i, e in enumerate(config["enfermedades"])}
    idx_to_planta = {i: c for c, i in planta_to_idx.items()}
    idx_to_enfermedad = {i: e for e, i in enfermedad_to_idx.items()}

    # Set de combinaciones válidas
    df = pd.read_csv(os.path.join(DATA_DIR, "train.csv"))
    combinaciones_validas = set(zip(df["planta"], df["enfermedad"]))

    correct_planta = 0
    correct_enfermedad = 0
    correct_comb = 0
    total = 0

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
                # Predicciones independientes
                pred_c = probs_planta[i].argmax().item()
                pred_e = probs_enfermedad[i].argmax().item()

                planta_str = idx_to_planta[pred_c]
                enfermedad_str = idx_to_enfermedad[pred_e]

                # Reasignar si no es válida
                if (planta_str, enfermedad_str) not in combinaciones_validas:
                    # Buscar la combinación válida con mayor probabilidad conjunta
                    best_pair = max(
                        combinaciones_validas,
                        key=lambda pair: probs_planta[i][planta_to_idx[pair[0]]] *
                                         probs_enfermedad[i][enfermedad_to_idx[pair[1]]]
                    )
                    planta_str, enfermedad_str = best_pair
                    pred_c = planta_to_idx[planta_str]
                    pred_e = enfermedad_to_idx[enfermedad_str]

                # Comparar con etiquetas reales
                if pred_c == labels_planta[i].item():
                    correct_planta += 1
                if pred_e == labels_enfermedad[i].item():
                    correct_enfermedad += 1
                if (pred_c == labels_planta[i].item()) and (pred_e == labels_enfermedad[i].item()):
                    correct_comb += 1

    acc_planta = correct_planta / total
    acc_enfermedad = correct_enfermedad / total
    acc_combinada = correct_comb / total

    print(f"🎯 Accuracy - planta: {acc_planta:.4f} | Enfermedad: {acc_enfermedad:.4f} | Combinada: {acc_combinada:.4f}")

    return acc_planta, acc_enfermedad, acc_combinada

