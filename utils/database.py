from pymongo import MongoClient
import yaml
import os
import dotenv

dotenv.load_dotenv()


def _running_inside_docker() -> bool:
    """Detecta si el proceso se ejecuta dentro de un contenedor Docker."""
    return os.path.exists("/.dockerenv")


def _normalize_local_mongo_uri(uri: str) -> str:
    """Evita usar hostname interno de Docker (mongo) cuando se ejecuta en local."""
    if not uri:
        return "mongodb://localhost:27017/"

    # Si estamos fuera de Docker y la URI apunta al hostname interno "mongo",
    # forzamos localhost para evitar timeouts en ejecuciones locales.
    if not _running_inside_docker() and "://mongo" in uri:
        return uri.replace("://mongo", "://localhost", 1)

    return uri

def connect_to_database(uri=None, db_name="Repositorio_Plantas"):
    """Conecta a MongoDB y devuelve la instancia de base de datos."""
    if uri is None:
        uri = os.getenv("URL_BBDD", "mongodb://localhost:27017/")
    uri = _normalize_local_mongo_uri(uri)
    client = MongoClient(uri)
    return client[db_name]

def load_yaml_config(config_path):
    """Carga configuración desde un archivo YAML dado (ruta absoluta o relativa)."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found at: {config_path}")
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    return config