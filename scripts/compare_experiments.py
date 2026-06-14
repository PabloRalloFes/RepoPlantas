import os
import json
import argparse
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from utils.plot_style import BAR_COLORS, apply_plot_style, format_metric_label, save_figure


def load_metrics(experiment_path):
    """Carga las métricas desde un archivo JSON en la carpeta del experimento."""
    metrics_file = os.path.join(experiment_path, "results", "metrics.json")
    if not os.path.exists(metrics_file):
        print(f"No se encontró el archivo de métricas en: {metrics_file}")
        return None

    with open(metrics_file, "r") as f:
        return json.load(f)


def compare_experiments(experiments):
    """Compara las métricas entre varios experimentos."""
    base_path = "./experiments"
    all_metrics = {}

    for experiment in experiments:
        experiment_path = os.path.join(base_path, experiment)
        metrics = load_metrics(experiment_path)
        if metrics:
            all_metrics[experiment] = metrics

    if not all_metrics:
        print("No se encontraron métricas para comparar.")
        return

    comparison_folder = os.path.join(base_path, "comparison", "_vs_".join(experiments))
    os.makedirs(comparison_folder, exist_ok=True)
    apply_plot_style()

    combined_metrics = ["accuracy_planta", "accuracy_enfermedad", "accuracy_combinada"]
    x = range(len(experiments))

    plt.figure(figsize=(9, 5))
    width = 0.22
    for i, metric in enumerate(combined_metrics):
        values = []
        for experiment in experiments:
            if "test" in all_metrics[experiment] and metric in all_metrics[experiment]["test"]:
                values.append(all_metrics[experiment]["test"][metric])
            else:
                values.append(0)
        plt.bar(
            [pos + i * width for pos in x],
            values,
            width=width,
            label=format_metric_label(metric),
            color=BAR_COLORS[i % len(BAR_COLORS)],
            edgecolor="white",
        )

    plt.title("Comparación de accuracy (test)")
    plt.xlabel("Experimento")
    plt.ylabel("Accuracy")
    plt.xticks([pos + width for pos in x], experiments, rotation=15, ha="right")
    plt.ylim(0, 1.05)
    plt.legend()
    plt.grid(True, axis="y", alpha=0.6)
    plt.tight_layout()
    save_figure(os.path.join(comparison_folder, "comparison_accuracy_combined.png"))

    f1_metrics = ["f1_planta", "f1_enfermedad"]
    plt.figure(figsize=(8, 5))
    width = 0.32
    for i, metric in enumerate(f1_metrics):
        values = []
        for experiment in experiments:
            if "test" in all_metrics[experiment] and metric in all_metrics[experiment]["test"]:
                values.append(all_metrics[experiment]["test"][metric])
            else:
                values.append(0)
        plt.bar(
            [pos + i * width for pos in x],
            values,
            width=width,
            label=format_metric_label(metric),
            color=BAR_COLORS[i % len(BAR_COLORS)],
            edgecolor="white",
        )

    plt.title("Comparación de F1 (test)")
    plt.xlabel("Experimento")
    plt.ylabel("F1-Score")
    plt.xticks([pos + width / 2 for pos in x], experiments, rotation=15, ha="right")
    plt.ylim(0, 1.05)
    plt.legend()
    plt.grid(True, axis="y", alpha=0.6)
    plt.tight_layout()
    save_figure(os.path.join(comparison_folder, "comparison_f1_combined.png"))

    plt.figure(figsize=(10, 6))
    for experiment, metrics in all_metrics.items():
        if "history" in metrics:
            for sub_metric, values in metrics["history"].items():
                plt.plot(values, label=f"{experiment} — {sub_metric}")

    plt.title("Comparación de pérdida por época")
    plt.xlabel("Época")
    plt.ylabel("Pérdida")
    plt.legend(fontsize=8)
    plt.grid(True, axis="y", alpha=0.6)
    plt.tight_layout()
    save_figure(os.path.join(comparison_folder, "comparison_history.png"))

    print("Comparación completada. Gráficos guardados en la carpeta:", comparison_folder)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Comparar métricas entre varios experimentos.")
    parser.add_argument("experiments", type=str, nargs="+", help="Nombres de los experimentos a comparar.")
    args = parser.parse_args()
    compare_experiments(args.experiments)
