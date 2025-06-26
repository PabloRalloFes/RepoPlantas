import os
from utils.database import connect_to_database, load_yaml_config
from utils.data import prepare_data_splits, get_dataloader_from_csv
from utils.model import build_model
from utils.train import train_model
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
    train_loader = get_dataloader_from_csv(os.path.join(DATA_DIR, "train.csv"), config, augment=False)
    val_loader = get_dataloader_from_csv(os.path.join(DATA_DIR, "val.csv"), config)

    # 3. Crear modelo
    model = build_model(config)

    # 4. Entrenar
    model, results = train_model(model, train_loader, val_loader, config)

    # 5. Guardar
    save_model(model, MODEL_PATH)
    save_metrics(results, METRICS_PATH)
    plot_history(results["history"], HISTORY_PATH)

if __name__ == "__main__":
    main()


