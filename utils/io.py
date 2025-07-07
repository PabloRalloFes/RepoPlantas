import json
import torch
import os
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix
import pandas as pd

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

    if "train_loss_planta" in history and "val_loss_planta" in history:
        plt.plot(history["train_loss_planta"], label="Train Loss - planta")
        plt.plot(history["val_loss_planta"], label="Val Loss - planta")

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

def save_confusion_matrix(y_true, y_pred, labels, title, path):
    """
    Guarda una matriz de confusión como imagen en disco.
    """
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', xticklabels=labels, yticklabels=labels, cmap='Greys', cbar=False)
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title(title)
    plt.tight_layout()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.savefig(path)
    plt.close()
    print(f"📊 Matriz de confusión guardada en {path}")

def plot_test_metrics_bar(metrics: dict, path: str):
    csv_dir = os.path.dirname(path)
    csv_path = os.path.join(csv_dir, "test_metrics.csv")
    df = pd.DataFrame.from_dict(metrics, orient='index', columns=["score"])
    df.to_csv(csv_path)
    print(f"📄 Métricas guardadas como CSV en {csv_path}")

    keys = [k for k in metrics.keys() if k.startswith(("accuracy", "f1", "precision", "recall"))]
    values = [metrics[k] for k in keys]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(keys, values)
    plt.ylim(0, 1.05)
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Score")
    plt.title("Test Metrics")
    plt.grid(axis='y')
    plt.tight_layout()

    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., 1.01 * height,
                 f"{height:.2f}", ha='center', va='bottom', fontsize=9)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.savefig(path)
    plt.close()
    print(f"📊 Gráfico de métricas de test guardado en {path}")