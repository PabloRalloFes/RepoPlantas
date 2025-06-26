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

    plt.figure(figsize=(8, 5))
    plt.plot(history["train_loss"], label="Train Loss")
    if "val_loss" in history:
        plt.plot(history["val_loss"], label="Val Loss")
    if "val_acc" in history:
        plt.plot(history["val_acc"], label="Val Accuracy")

    plt.xlabel("Epoch")
    plt.ylabel("Metric Value")
    plt.title("Training History")
    plt.legend()
    plt.grid(True)
    plt.savefig(path)
    plt.close()
    print(f"📈 Gráfica de entrenamiento guardada en {path}")

