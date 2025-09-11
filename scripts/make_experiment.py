import os
import argparse
import shutil

def create_experiment_structure(experiment_name):
    """Crea la estructura base para un nuevo experimento."""
    base_path = "./experiments"
    experiment_path = os.path.join(base_path, experiment_name)

    # Verificar si la carpeta ya existe
    if os.path.exists(experiment_path):
        print(f"❌ El experimento '{experiment_name}' ya existe. Por favor, elige otro nombre.")
        return

    # Subcarpetas típicas de un experimento
    subfolders = ["data", "models", "results"]

    try:
        os.makedirs(experiment_path, exist_ok=True)
        for folder in subfolders:
            os.makedirs(os.path.join(experiment_path, folder), exist_ok=True)

        # Copiar archivos config.yaml y run_experiment.py desde experiments/BASE
        base_files_path = "./experiments/BASE"
        for file_name in ["config.yaml", "run_experiment.py"]:
            src_file = os.path.join(base_files_path, file_name)
            dest_file = os.path.join(experiment_path, file_name)
            if os.path.exists(src_file):
                shutil.copy(src_file, dest_file)

        print(f"✅ Estructura creada para el experimento: {experiment_name}")
    except Exception as e:
        print(f"❌ Error al crear la estructura del experimento: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crear la estructura base de un experimento.")
    parser.add_argument("experiment_name", type=str, help="Nombre del nuevo experimento.")

    args = parser.parse_args()

    create_experiment_structure(args.experiment_name)
