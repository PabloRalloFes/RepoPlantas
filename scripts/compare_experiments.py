import os
import json
import argparse
import matplotlib.pyplot as plt

def load_metrics(experiment_path):
    """Carga las métricas desde un archivo JSON en la carpeta del experimento."""
    metrics_file = os.path.join(experiment_path, "results", "metrics.json")
    if not os.path.exists(metrics_file):
        print(f"️No se encontró el archivo de métricas en: {metrics_file}")
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

    # Crear carpeta para guardar los gráficos
    comparison_folder = os.path.join(base_path, "comparison", "_vs_".join(experiments))
    os.makedirs(comparison_folder, exist_ok=True)

    # Crear gráfico combinado para las métricas principales de clasificación simple.
    combined_metrics = ["accuracy", "f1", "precision", "recall"]
    x = range(len(experiments))

    plt.figure()
    width = 0.18

    for i, metric in enumerate(combined_metrics):
        values = []
        for experiment in experiments:
            if "test" in all_metrics[experiment] and metric in all_metrics[experiment]["test"]:
                values.append(all_metrics[experiment]["test"][metric])
            else:
                values.append(0)

        plt.bar([pos + i * width for pos in x], values, width=width, label=metric)

    plt.title("Comparación de métricas de clasificación")
    plt.xlabel("Experimentos")
    plt.ylabel("Valor")
    plt.xticks([pos + width * 1.5 for pos in x], experiments)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(comparison_folder, "comparison_metrics.png"))
    plt.close()

    # Restaurar gráfico de history
    plt.figure()
    for experiment, metrics in all_metrics.items():
        if "history" in metrics:
            for sub_metric, values in metrics["history"].items():
                plt.plot(values, label=f"{experiment} - {sub_metric}")

    plt.title("Comparación de History")
    plt.xlabel("Época")
    plt.ylabel("Pérdida")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(comparison_folder, "comparison_history.png"))
    plt.close()

    print("Comparación completada. Gráficos guardados en la carpeta:", comparison_folder)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Comparar métricas entre varios experimentos.")
    parser.add_argument("experiments", type=str, nargs="+", help="Nombres de los experimentos a comparar.")

    args = parser.parse_args()

    compare_experiments(args.experiments)
