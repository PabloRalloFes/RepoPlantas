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
DB_NAME = os.getenv("DB_NAME", "Repositorio_Plantas")
DB_USERS = os.getenv("DB_USERS", "Usuarios")
VERIFY_SSL = os.getenv("VERIFY_SSL", "false").strip().lower() in {"1", "true", "yes"}

if not VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _post(url, **kwargs):
    return requests.post(url, verify=VERIFY_SSL, timeout=15, **kwargs)


def _auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


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
        print("STEP registro ->", f"{URL}/registro")
        registro = _post(
            f"{URL}/registro",
            json={"nombre": admin_name, "password": admin_password_hashed},
        )
        print("registro status:", registro.status_code, _json_or_text(registro))
    except Exception as e:
        print("Error creating admin user via /registro:", e)
        return None

    try:
        print("STEP token -> JWT_SECRET len:", len(JWT_SECRET))

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
        print("token generated, len:", len(bootstrap_token))
        print("STEP add_rol ->", f"{URL}/add_rol")
        add_rol = _post(
            f"{URL}/add_rol",
            json={"nombre": admin_name, "rol": "admin"},
            headers=_auth_headers(bootstrap_token),
        )
        print("add_rol status:", add_rol.status_code, _json_or_text(add_rol))
    except Exception as e:
        print("Error granting admin role via /add_rol:", e)
        return None

    try:
        # Si el usuario ya existía con una contraseña creada con el flujo anterior,
        # lo migramos al formato que espera la app de escritorio.
        db_auth = connect_to_database(db_name=DB_USERS)
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
        print("STEP login ->", f"{URL}/iniciar_sesion")
        login = _post(
            f"{URL}/iniciar_sesion",
            json={"nombre": admin_name, "password": admin_password_hashed, "rol": "admin"},
        )
        login_data = _json_or_text(login)
        print("login status:", login.status_code, login_data)
        if login.status_code != 200 or not isinstance(login_data, dict):
            return None
        return login_data.get("access_token")
    except Exception as e:
        print("Error logging in admin via /iniciar_sesion:", e)
        return None

db = connect_to_database(db_name=DB_NAME)

# Asegurar colecciones base (Fuente y Docs deben existir aunque estén vacías).
for name in ("Campos", "Clases", "Formato", "Fuente", "Docs"):
    _ensure_collection(db, name)

admin_token = _bootstrap_admin_user()
if not admin_token:
    raise RuntimeError("No se pudo obtener token de admin para inicialización.")

# Campos a crear
with open("src/campos.json", "r", encoding="utf-8") as f:
    campos = json.load(f)

for campo in campos:
    r = _post(f"{URL}/add_campo", json=campo, headers=_auth_headers(admin_token))
    print(r.status_code, r.json())

# Etiquetas a añadir
with open("src/etiquetas.json", "r", encoding="utf-8") as f:
    etiquetas = json.load(f)

for e in etiquetas:
    r = _post(f"{URL}/add_etiqueta", json=e, headers=_auth_headers(admin_token))
    print(r.status_code, r.json())

with open("src/clases_combinadas.json", "r", encoding="utf-8") as f:
    clases = json.load(f)

for clase in sorted(clases, key=lambda c: c["_id"]):
    payload = {
        "coleccion": "Clases",
        "etiqueta": {
            "clasificacion": clase.get("clasificacion",""),
            "planta": clase["planta"],
            "nombre_comun": clase["nombre_comun"],
            "nombre_cientifico": clase.get("nombre_cientifico",""),
        }
    }
    r = _post(f"{URL}/add_etiqueta", json=payload, headers=_auth_headers(admin_token))
    print(f'{clase["_id"]:>3} {clase["planta"]} - {clase["nombre_comun"]} → {r.status_code}')