#!/usr/bin/env python3
"""Regenera history.png y metrics_graph.png desde results/metrics.json (sin reentrenar)."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.io import plot_history, plot_test_metrics_bar


def main():
    parser = argparse.ArgumentParser(
        description="Regenerar gráficos de un experimento a partir de metrics.json"
    )
    parser.add_argument("experiment", help="Nombre de la carpeta en experiments/")
    args = parser.parse_args()

    exp_dir = ROOT / "experiments" / args.experiment
    metrics_path = exp_dir / "results" / "metrics.json"
    if not metrics_path.exists():
        raise SystemExit(f"No existe {metrics_path}")

    with open(metrics_path, encoding="utf-8") as f:
        metrics = json.load(f)

    results_dir = exp_dir / "results"
    if "history" in metrics:
        plot_history(metrics["history"], str(results_dir / "history.png"))
    if "test" in metrics:
        plot_test_metrics_bar(metrics["test"], str(results_dir / "metrics_graph.png"))

    print("Gráficos regenerados en", results_dir)
    print("Nota: las matrices de confusión requieren re-evaluar o reentrenar el modelo.")


if __name__ == "__main__":
    main()
