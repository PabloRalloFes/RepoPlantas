import os
import sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from utils.database import connect_to_database, load_yaml_config
from utils.data import prepare_data_splits, get_dataloader_from_csv, is_unlimited_imagenes_por_clase
from utils.model import build_model
from utils.train import train_model, evaluate
from utils.io import save_model, save_metrics, plot_history, plot_test_metrics_bar

EXPERIMENT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPERIMENT_NAME = os.path.basename(EXPERIMENT_DIR)
CONFIG_PATH = os.path.join(EXPERIMENT_DIR, "config.yaml")
DATA_DIR = os.path.join(EXPERIMENT_DIR, "data")
MODEL_PATH = os.path.join(EXPERIMENT_DIR, "models", f"{EXPERIMENT_NAME}.pth")
RESULTS_DIR = os.path.join(EXPERIMENT_DIR, "results")
METRICS_PATH = os.path.join(RESULTS_DIR, "metrics.json")
METRICS_GRAPH_PATH = os.path.join(RESULTS_DIR, "metrics_graph.png")
HISTORY_PATH = os.path.join(RESULTS_DIR, "history.png")


def main():
    db = connect_to_database()
    config = load_yaml_config(CONFIG_PATH)

    if is_unlimited_imagenes_por_clase(config.get("imagenes_por_clase")):
        config["imagenes_por_clase"] = 999999999

    config = prepare_data_splits(db, config, save_dir=DATA_DIR)

    with open(os.path.join(EXPERIMENT_DIR, "config_final.yaml"), "w") as f:
        yaml.dump(config, f)

    train_loader, val_loader, test_loader = get_dataloader_from_csv(os.path.join(DATA_DIR), config)
    model = build_model(config)
    model, history = train_model(model, train_loader, val_loader, config, DATA_DIR)

    val_metrics = evaluate(model, val_loader, config, DATA_DIR, results_dir=RESULTS_DIR, split_name="val")
    test_metrics = evaluate(model, test_loader, config, DATA_DIR, results_dir=RESULTS_DIR, split_name="test")

    results = {
        "val": val_metrics,
        "test": test_metrics,
        "history": history,
    }

    save_model(model, MODEL_PATH)
    save_metrics(results, METRICS_PATH)
    plot_test_metrics_bar(results["test"], METRICS_GRAPH_PATH)
    plot_history(history, HISTORY_PATH)


if __name__ == "__main__":
    main()
