import os
import argparse
import shutil
import yaml
import json

def create_experiment_structure(experiment_name, config_variables=None):
    """Crea la estructura base para un nuevo experimento."""
    base_path = "./experiments"
    experiment_path = os.path.join(base_path, experiment_name)

    # Verificar si la carpeta ya existe
    if os.path.exists(experiment_path):
        print(f"El experimento '{experiment_name}' ya existe. Por favor, elige otro nombre.")
        return

    # Subcarpetas típicas de un experimento
    subfolders = ["data", "models", "results"]

    try:
        os.makedirs(experiment_path, exist_ok=True)
        for folder in subfolders:
            os.makedirs(os.path.join(experiment_path, folder), exist_ok=True)

        # Cargar el config.yaml del experimento "BASE"
        base_config_path = os.path.join(base_path, "BASE", "config.yaml")
        if not os.path.exists(base_config_path):
            raise FileNotFoundError(f"No se encontró el archivo base config.yaml en {base_config_path}")

        with open(base_config_path, "r") as base_config_file:
            base_config = yaml.safe_load(base_config_file)

        # Sobrescribir las variables con las proporcionadas por el usuario
        final_config = base_config.copy()
        if config_variables:
            final_config.update(config_variables)

        # Guardar el nuevo config.yaml
        config_path = os.path.join(experiment_path, "config.yaml")
        with open(config_path, "w") as config_file:
            yaml.dump(final_config, config_file)

        # Copiar run_experiment.py desde experiments/BASE
        base_files_path = os.path.join(base_path, "BASE")
        run_experiment_file = os.path.join(base_files_path, "run_experiment.py")
        if os.path.exists(run_experiment_file):
            shutil.copy(run_experiment_file, os.path.join(experiment_path, "run_experiment.py"))

        print(f"Estructura creada para el experimento: {experiment_name}")
    except Exception as e:
        print(f"Error al crear la estructura del experimento: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crear la estructura base de un experimento.")
    parser.add_argument("experiment_name", type=str, help="Nombre del nuevo experimento.")
    parser.add_argument("--config", type=str, help="Variables de configuración en formato JSON.", default="{}")

    args = parser.parse_args()
    config_variables = json.loads(args.config)

    create_experiment_structure(args.experiment_name, config_variables)
