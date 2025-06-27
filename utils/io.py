import json
import torch
import os
import matplotlib.pyplot as plt

def save_model(model, path):
    """Guarda el modelo PyTorch en disco."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    torch.save(model.state_dict(), path)
    print(f"📦 Modelo guardado en {path}")

def save_metrics(metrics_dict, path):
    """Guarda las métricas en un archivo JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(metrics_dict, f, indent=2)
    print(f"📄 Métricas guardadas en {path}")

def plot_history(history, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    plt.figure(figsize=(10, 6))

    if "train_loss_cultivo" in history and "val_loss_cultivo" in history:
        plt.plot(history["train_loss_cultivo"], label="Train Loss - Cultivo")
        plt.plot(history["val_loss_cultivo"], label="Val Loss - Cultivo")

    if "train_loss_enfermedad" in history and "val_loss_enfermedad" in history:
        plt.plot(history["train_loss_enfermedad"], label="Train Loss - Enfermedad")
        plt.plot(history["val_loss_enfermedad"], label="Val Loss - Enfermedad")

    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.title("Training History")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()

    print(f"📈 Gráfica de entrenamiento guardada en {path}")


