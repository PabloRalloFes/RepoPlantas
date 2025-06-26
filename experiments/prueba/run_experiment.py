import os
import sys
from pathlib import Path

# Añadir la raíz del proyecto al sys.path
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from utils.database import connect_to_database, load_yaml_config
from utils.data import prepare_data_splits, get_dataloader_from_csv
from utils.model import build_model
from utils.train import train_model, evaluate
from utils.io import save_model, save_metrics, plot_history

EXPERIMENT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(EXPERIMENT_DIR, "config.yaml")
DATA_DIR = os.path.join(EXPERIMENT_DIR, "data")
MODEL_PATH = os.path.join(EXPERIMENT_DIR, "models/best_model.pth")
METRICS_PATH = os.path.join(EXPERIMENT_DIR, "results/metrics.json")
HISTORY_PATH = os.path.join(EXPERIMENT_DIR, "results/history.png")

def main():
    db = connect_to_database()
    config = load_yaml_config(CONFIG_PATH)

    # 1. Preparar CSVs
    prepare_data_splits(db, config, save_dir=DATA_DIR)

    # 2. Cargar datos
    train_loader, val_loader, test_loader = get_dataloader_from_csv(os.path.join(DATA_DIR), config)

    # 3. Crear modelo
    model = build_model(config)

    # 4. Entrenar
    model, history = train_model(model, train_loader, val_loader, config)

    # 5. Evaluación en validación
    val_loss, val_acc = evaluate(model, val_loader)

    # 6. Guardar
    results = {
        "val_loss": val_loss,
        "val_acc": val_acc,
        "history": history
    }

    save_model(model, MODEL_PATH)
    save_metrics(results, METRICS_PATH)
    plot_history(history, HISTORY_PATH)

if __name__ == "__main__":
    main()


