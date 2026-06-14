import json
import torch
import os
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix
import pandas as pd

from utils.plot_style import (
    COLORS,
    BAR_COLORS,
    apply_plot_style,
    format_class_labels,
    format_metric_label,
    infer_label_kind,
    save_figure,
)


def save_model(model, path):
    """Guarda el modelo PyTorch en disco."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    torch.save(model.state_dict(), path)
    print(f"Modelo guardado en {path}")

def save_metrics(metrics_dict, path):
    """Guarda las métricas en un archivo JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(metrics_dict, f, indent=2)
    print(f"Métricas guardadas en {path}")

def plot_history(history, path):
    apply_plot_style()
    os.makedirs(os.path.dirname(path), exist_ok=True)

    plt.figure(figsize=(10, 6))

    if "train_loss_planta" in history and "val_loss_planta" in history:
        plt.plot(
            history["train_loss_planta"],
            label="Entrenamiento — planta",
            color=COLORS["primary"],
            linewidth=2,
        )
        plt.plot(
            history["val_loss_planta"],
            label="Validación — planta",
            color=COLORS["primary_light"],
            linewidth=2,
            linestyle="--",
        )

    if "train_loss_enfermedad" in history and "val_loss_enfermedad" in history:
        plt.plot(
            history["train_loss_enfermedad"],
            label="Entrenamiento — enfermedad",
            color=COLORS["accent"],
            linewidth=2,
        )
        plt.plot(
            history["val_loss_enfermedad"],
            label="Validación — enfermedad",
            color=COLORS["accent_light"],
            linewidth=2,
            linestyle="--",
        )

    plt.xlabel("Época")
    plt.ylabel("Pérdida")
    plt.title("Evolución del entrenamiento")
    plt.legend(loc="upper right", framealpha=0.9)
    plt.grid(True, axis="y", linestyle="-", alpha=0.6)
    plt.tight_layout()
    save_figure(path)
    print(f"Gráfica de entrenamiento guardada en {path}")

def save_confusion_matrix(y_true, y_pred, labels, title, path):
    """Guarda una matriz de confusión como imagen en disco."""
    apply_plot_style()
    kind = infer_label_kind(title)
    display_labels = format_class_labels(labels, kind=kind)

    cm = confusion_matrix(y_true, y_pred)
    n = len(display_labels)
    figsize = (max(8, min(16, 0.35 * n + 4)), max(7, min(14, 0.32 * n + 4)))
    plt.figure(figsize=figsize)

    tick_size = 8 if n > 14 else 9
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        xticklabels=display_labels,
        yticklabels=display_labels,
        cmap="Greys",
        cbar=False,
        linewidths=0.3,
        linecolor="#EEEEEE",
        annot_kws={"size": 7 if n > 16 else 8},
    )
    plt.xlabel("Predicción")
    plt.ylabel("Real")
    plt.title(title)
    plt.xticks(rotation=45, ha="right", fontsize=tick_size)
    plt.yticks(rotation=0, fontsize=tick_size)
    plt.tight_layout()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    save_figure(path)
    print(f"Matriz de confusión guardada en {path}")

def plot_test_metrics_bar(metrics: dict, path: str):
    csv_dir = os.path.dirname(path)
    csv_path = os.path.join(csv_dir, "test_metrics.csv")
    df = pd.DataFrame.from_dict(metrics, orient='index', columns=["score"])
    df.to_csv(csv_path)
    print(f"Métricas guardadas como CSV en {csv_path}")

    keys = [k for k in metrics.keys() if k.startswith(("accuracy", "f1", "precision", "recall"))]
    values = [metrics[k] for k in keys]
    display_keys = [format_metric_label(k) for k in keys]

    apply_plot_style()
    plt.figure(figsize=(10, 6))
    bar_colors = [BAR_COLORS[i % len(BAR_COLORS)] for i in range(len(keys))]
    bars = plt.bar(display_keys, values, color=bar_colors, edgecolor="white", linewidth=0.6)
    plt.ylim(0, 1.05)
    plt.xticks(rotation=35, ha="right")
    plt.ylabel("Puntuación")
    plt.title("Métricas en test")
    plt.grid(axis="y", linestyle="-", alpha=0.6)

    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            min(1.02, height + 0.02),
            f"{height:.2f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.tight_layout()
    save_figure(path)
    print(f"Gráfico de métricas de test guardado en {path}")
