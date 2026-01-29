from pymongo import MongoClient
import yaml
import os
import dotenv

dotenv.load_dotenv()

def connect_to_database(uri=None, db_name="Repositorio_Plantas"):
    """Conecta a MongoDB y devuelve la instancia de base de datos."""
    if uri is None:
        uri = os.getenv("URL_BBDD", "mongodb://localhost:27017/")
    client = MongoClient(uri)
    return client[db_name]

def load_yaml_config(config_path):
    """Carga configuración desde un archivo YAML dado (ruta absoluta o relativa)."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found at: {config_path}")
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    return config