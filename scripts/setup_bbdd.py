import requests
import json
from dotenv import load_dotenv
import os
import jwt
import sys
from pathlib import Path
import urllib3
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from utils.database import connect_to_database
from utils.auth import hash_password

load_dotenv()

URL = os.getenv("URL_API")
JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_ME_IN_PRODUCTION")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
DB_NAME = os.getenv("DB_NAME", "Demo")
VERIFY_SSL = os.getenv("VERIFY_SSL", "false").strip().lower() in {"1", "true", "yes"}

if not VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _post(url, **kwargs):
    return requests.post(url, verify=VERIFY_SSL, timeout=15, **kwargs)


# Normalize URL: when VERIFY_SSL is False and URL points to a local/internal host,
# prefer http:// to avoid HTTPS connection attempts inside Docker/local setups.
def _normalize_api_url(raw_url: str) -> str:
    if not raw_url:
        return raw_url
    u = raw_url.strip()
    # If SSL verification disabled and URL uses https with local hostnames, switch to http
    if not VERIFY_SSL and u.lower().startswith("https://"):
        if any(h in u for h in ("127.0.0.1", "localhost", "api")):
            u = "http://" + u.split("://", 1)[1]
    return u


# Apply normalization and log URL used for bootstrap.
URL = _normalize_api_url(URL)
print("Using API URL for bootstrap:", URL)


def _app_password_hash(usuario: str, password: str) -> str:
    """Replica el hash cliente que usa `logicav3.hash_func` para login/registro."""
    cadena = usuario + "HOLAAAA" + password
    hash_res = ""
    for i in range(len(cadena)):
        c = ord(cadena[i]) * (i + 1) * (i + 1)
        hash_res += str(c)
    hash_res = hash_res.zfill(20)
    return hash_res[-20:]


def _ensure_collection(db, collection_name: str):
    if collection_name not in db.list_collection_names():
        db.create_collection(collection_name)


def _seed_target_database():
    """Inicializa la BBDD objetivo con estructura base y datos semilla genéricos."""
    db = connect_to_database(db_name=DB_NAME)

    # Asegurar colecciones base (Fuente y Docs deben existir aunque estén vacías).
    for name in ("Campos", "Clases", "Formato", "Fuente", "Docs"):
        _ensure_collection(db, name)

    # Campos
    with open("src/campos.json", "r", encoding="utf-8") as f:
        campos = json.load(f)

    for idx, campo in enumerate(campos):
        campo_doc = dict(campo)
        campo_doc.setdefault("_id", idx)
        db.Campos.replace_one({"nombre": campo_doc["nombre"]}, campo_doc, upsert=True)

    # Formatos (desde etiquetas.json, solo coleccion Formato)
    with open("src/etiquetas.json", "r", encoding="utf-8") as f:
        etiquetas = json.load(f)

    formato_entries = [e for e in etiquetas if e.get("coleccion") == "Formato"]
    next_formato_id = 0
    for entry in formato_entries:
        formato = (entry.get("etiqueta") or {}).get("formato")
        if not formato:
            continue
        existing = db.Formato.find_one({"formato": formato})
        if existing:
            continue
        db.Formato.insert_one({"_id": next_formato_id, "formato": formato, "nombre": formato})
        next_formato_id += 1

    # Clases
    with open("src/coleccion_clases.json", "r", encoding="utf-8") as f:
        clases = json.load(f)

    for clase in sorted(clases, key=lambda c: c.get("_id", 0)):
        doc = dict(clase)
        # Ensure an _id is present; skip otherwise.
        doc_id = clase.get("_id")
        if doc_id is None:
            continue
        doc["_id"] = doc_id

        # Backward-compatible: if old-style label fields exist, preserve them.
        class_label = doc.get("class_label") or doc.get("clase") or doc.get("nombre")
        if class_label:
            doc.setdefault("class_label", class_label)

        # Insert the class document even if no explicit `class_label` is provided.
        db.Clases.replace_one({"_id": doc["_id"]}, doc, upsert=True)

    # Fuente: crear la fuente "App" con id 0 para imágenes subidas desde la aplicación
    db.Fuente.replace_one({"_id": 0}, {"_id": 0, "fuente": "App", "nombre": "App"}, upsert=True)

    print("Target DB initialized:")
    print("- Campos:", db.Campos.count_documents({}))
    print("- Formato:", db.Formato.count_documents({}))
    print("- Clases:", db.Clases.count_documents({}))
    print("- Fuente:", db.Fuente.count_documents({}), "(includes App with id 0)")
    print("- Docs:", db.Docs.count_documents({}), "(should be 0 by default)")

def _json_or_text(response):
    try:
        return response.json()
    except Exception:
        return response.text


def _bootstrap_admin_user():
    admin_name = "admin"
    admin_password = "admin"
    admin_password_hashed = _app_password_hash(admin_name, admin_password)

    try:
        registro = _post(
            f"{URL}/registro",
            json={"nombre": admin_name, "password": admin_password_hashed},
        )
        print(registro.status_code, _json_or_text(registro))
    except Exception as e:
        print("Error creating admin user via /registro:", e)
        return None

    try:
        # Primer bootstrap: /add_rol exige admin, así que se usa un token de arranque.
        bootstrap_token = jwt.encode(
            {
                "sub": admin_name,
                "roles": ["usuario", "admin"],
                "active_role": "admin",
            },
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )

        add_rol = _post(
            f"{URL}/add_rol",
            json={"nombre": admin_name, "rol": "admin"},
            headers={"Authorization": f"Bearer {bootstrap_token}"},
        )
        print(add_rol.status_code, _json_or_text(add_rol))
    except Exception as e:
        print("Error granting admin role via /add_rol:", e)
        return None

    try:
        # Si el usuario ya existía con una contraseña creada con el flujo anterior,
        # lo migramos al formato que espera la app de escritorio.
        db_auth = connect_to_database(db_name="Usuarios")
        col_usuarios = db_auth["usuarios"]
        col_usuarios.update_one(
            {"nombre": admin_name},
            {
                "$set": {"password": hash_password(admin_password_hashed)},
                "$addToSet": {"rol": {"$each": ["usuario", "admin"]}},
            },
            upsert=True,
        )
    except Exception as e:
        print("Error migrating admin password in Usuarios DB:", e)

    try:
        login = _post(
            f"{URL}/iniciar_sesion",
            json={"nombre": admin_name, "password": admin_password_hashed, "rol": "admin"},
        )
        login_data = _json_or_text(login)
        print(login.status_code, login_data)
        if login.status_code != 200 or not isinstance(login_data, dict):
            return None
        return login_data.get("access_token")
    except Exception as e:
        print("Error logging in admin via /iniciar_sesion:", e)
        return None


admin_token = _bootstrap_admin_user()
if not admin_token:
    raise RuntimeError("No se pudo obtener token de admin para inicialización.")

# Inicializar datos en la BBDD objetivo elegida por DB_NAME.
_seed_target_database()


def _load_and_persist_project_targets():
    """Si existe `src/project_targets.json`, lo carga y persiste en la coleccion ProjectConfig.

    El archivo debe listar nombres de variables a predecir
    Ejemplo: ["clase"] o ["clase", "planta"] si la coleccion de clases incluye esos campos.
    """
    db = connect_to_database(db_name=DB_NAME)

    path = Path("src/project_targets.json")
    if not path.exists():
        print("No project_targets.json found; skipping project target persistence.")
        return

    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as e:
        print("Error reading src/project_targets.json:", e)
        return

    if isinstance(payload, dict):
        targets = payload.get("target_fields") or payload.get("targets") or []
    elif isinstance(payload, list):
        targets = payload
    else:
        print("Unrecognized format for src/project_targets.json; expected list or object.")
        return

    if not targets:
        print("Warning: src/project_targets.json is empty; skipping ProjectConfig persistence.")
        return

    if not all(isinstance(t, str) for t in targets):
        print("Warning: project targets must be strings naming class variables; skipping ProjectConfig persistence.")
        return

    class_docs = list(db.Clases.find({}, {"_id": 0}))
    available_fields = sorted({key for doc in class_docs for key in doc.keys()})
    available_fields = [key for key in available_fields if key != "_id"]

    missing = [field for field in targets if field not in available_fields]
    if missing:
        print("Warning: these target fields are not present in Clases documents:", missing)
        print("Available fields in Clases:", available_fields)
        return

    doc = {
        "_id": "project",
        "target_fields": targets,
        "available_class_fields": available_fields,
        "raw": targets,
        "created_at": datetime.utcnow().isoformat(),
    }

    db.ProjectConfig.replace_one({"_id": "project"}, doc, upsert=True)
    print("Persisted ProjectConfig with target_fields:", targets)


_load_and_persist_project_targets()

print("Database bootstrap completed. Next step: define what data the user must provide for project creation.")
