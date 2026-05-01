import base64
import io
from PIL import Image
from flask import Flask, request, jsonify, abort, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import re
import os
import shutil
from bson.objectid import ObjectId
from io import BytesIO
import uuid
import zipfile
from utils.model import build_model
from utils.database import load_yaml_config, connect_to_database
from utils.auth import hash_password, check_password
from torchvision import transforms
from PIL import Image
import torch
import pandas as pd
from pathlib import Path
import json
from datetime import datetime, timezone, timedelta
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from dotenv import load_dotenv
from pymongo import UpdateOne, InsertOne, DeleteOne, ReturnDocument
from pymongo.errors import DuplicateKeyError
from pymongo.cursor import Cursor
from decimal import Decimal
import subprocess
import matplotlib
from flask import send_file
import mimetypes
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Carga .env del directorio del proyecto (si existe).
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=False)


def _env_int(name, default):
    value = os.getenv(name, str(default))
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _env_json(name, default):
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


app = Flask(__name__)
db = connect_to_database(db_name="Repositorio_Plantas")  # por defecto usa "Repositorio_Plantas"

ROOT = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(ROOT, "imagenes")

MAX_IMAGE_SIZE_MB = _env_int("MAX_IMAGE_SIZE_MB", 10)
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG"}
JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_ME_IN_PRODUCTION")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXP_MINUTES = _env_int("JWT_EXP_MINUTES", 120)
PUBLIC_API_BASE_URL = os.getenv("PUBLIC_API_BASE_URL", "").strip().rstrip("/")

cors_origins_env = os.getenv("CORS_ORIGINS", "").strip()
if cors_origins_env == "*":
    allowed_origins = "*"
elif cors_origins_env:
    allowed_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
else:
    # Origenes por defecto para desarrollo local.
    allowed_origins = [
        "http://localhost",
        "http://127.0.0.1",
        "https://localhost",
        "https://127.0.0.1",
    ]

CORS(app, resources={r"/*": {"origins": allowed_origins}})
limiter = Limiter(key_func=get_remote_address, app=app, default_limits=[])

PUBLIC_ENDPOINTS = set(_env_json("PUBLIC_ENDPOINTS", []))
AUTH_REQUIRED_ENDPOINTS = set(_env_json("AUTH_REQUIRED_ENDPOINTS", []))
AUTH_REQUIRED_PREFIXES = tuple(_env_json("AUTH_REQUIRED_PREFIXES", []))

ROLE_REQUIRED_ENDPOINTS = {}
_roles_from_env = _env_json("ROLE_REQUIRED_ENDPOINTS", {})
if isinstance(_roles_from_env, dict):
    ROLE_REQUIRED_ENDPOINTS = {
        str(endpoint): set(roles if isinstance(roles, list) else [roles])
        for endpoint, roles in _roles_from_env.items()
    }

def create_access_token(username, roles, active_role=None):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "roles": roles,
        "active_role": active_role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_EXP_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def _extract_bearer_token():
    auth = request.headers.get("Authorization", "").strip()
    if auth:
        parts = auth.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1].strip()
            if token:
                return token

    # Fallback para clientes que abren URL en navegador externo (p. ej. app móvil).
    token_qs = (request.args.get("access_token") or request.args.get("token") or "").strip()
    if token_qs:
        return token_qs

    return None

def require_any_role(*allowed_roles):
    roles = set(getattr(g, "auth_roles", []))
    if roles.intersection(set(allowed_roles)):
        return None
    return jsonify({"success": False, "error": "No autorizado para este recurso"}), 403

def require_self_or_admin(target_username):
    roles = set(getattr(g, "auth_roles", []))
    auth_username = getattr(g, "auth_username", None)
    if auth_username == target_username or "admin" in roles:
        return None
    return jsonify({"success": False, "error": "No autorizado para operar sobre este usuario"}), 403

@app.before_request
def authenticate_sensitive_endpoints():
    if request.method == "OPTIONS":
        return None

    path = request.path
    if path in PUBLIC_ENDPOINTS:
        return None

    needs_auth = (path in AUTH_REQUIRED_ENDPOINTS) or any(path.startswith(p) for p in AUTH_REQUIRED_PREFIXES)
    if not needs_auth:
        return None

    token = _extract_bearer_token()
    if not token:
        return jsonify({"success": False, "error": "Falta token de autenticacion"}), 401

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except ExpiredSignatureError:
        return jsonify({"success": False, "error": "Token expirado"}), 401
    except InvalidTokenError:
        return jsonify({"success": False, "error": "Token invalido"}), 401

    g.auth_user = payload
    g.auth_username = payload.get("sub")
    g.auth_roles = payload.get("roles", [])
    g.auth_active_role = payload.get("active_role")

    allowed_roles = ROLE_REQUIRED_ENDPOINTS.get(path)
    if allowed_roles:
        if not set(g.auth_roles).intersection(allowed_roles):
            return jsonify({"success": False, "error": "No autorizado para este recurso"}), 403

    return None

def get_image_url(nombre_imagen):
    """
    Construye la URL pública de una imagen.
    - Si PUBLIC_API_BASE_URL está definida, se usa esa base.
    - Si no, usa el host de la request actual (útil en local y LAN).
    """
    if PUBLIC_API_BASE_URL:
        return f"{PUBLIC_API_BASE_URL}/imagen_base64/{nombre_imagen}"
    return f"{request.host_url.rstrip('/')}/imagen_base64/{nombre_imagen}"

def ensure_backup_ttl(db, days=None):
    if days is None:
        return
    try:
        seconds = int(days * 24 * 3600)
        db["Clases_backup"].create_index("created_at", expireAfterSeconds=seconds)
    except Exception:
        pass

def store_clases_backup_single(db, docs, max_backups=5, ttl_days=None):
    """
    Guarda todas las clases en un único documento dentro de 'Clases_backup'.
    - docs: lista de documentos (resultado de find()).
    - max_backups: cantidad de backups a mantener (más recientes). None = sin rotación.
    - ttl_days: si se pasa entero crea índice TTL con ese número de días (puede llamar a ensure_backup_ttl).
    Devuelve el _id del documento de backup (ObjectId) y el timestamp backup_id.
    """
    if ttl_days:
        ensure_backup_ttl(db, ttl_days)

    backup_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    now = datetime.now(timezone.utc)

    backup_docs = []
    for d in docs:
        clean = {}
        for k, v in d.items():
            if k == "_id":
                clean[k] = str(v) if isinstance(v, ObjectId) else v
            else:
                clean[k] = v
        backup_docs.append(clean)

    doc = {
        "_backup_id": backup_id,
        "created_at": now,
        "count": len(backup_docs),
        "docs": backup_docs
    }

    res = db["Clases_backup"].insert_one(doc)
    inserted_id = res.inserted_id

    if max_backups is not None and max_backups > 0:
        to_delete = list(db["Clases_backup"].find({}, {"_id": 1}).sort("created_at", -1).skip(max_backups))
        if to_delete:
            ids = [d["_id"] for d in to_delete]
            db["Clases_backup"].delete_many({"_id": {"$in": ids}})

    return inserted_id, backup_id

def ensure_counter_at_least(db, name, min_value):
    """
    Asegura que el contador 'name' en db.counters tenga seq >= min_value.
    Usa $max con upsert para elevar el seq si hace falta.
    """
    try:
        minv = int(min_value) if min_value is not None else 0
        db.counters.update_one({"_id": name}, {"$max": {"seq": minv}}, upsert=True)
    except Exception:
        pass

def serialize_value(v):
    """
    Convierte a tipos JSON-serializables:
      - Cursor -> lista
      - ObjectId -> str
      - datetime -> ISO
      - bytes -> base64
      - dict/list/tuple/set -> recursivo
      - Decimal -> float
    """
    # Cursores de pymongo -> lista serializada
    if isinstance(v, Cursor):
        return [serialize_value(x) for x in v]

    # Colecciones
    if isinstance(v, dict):
        return {k: serialize_value(val) for k, val in v.items()}
    if isinstance(v, (list, tuple, set)):
        return [serialize_value(x) for x in v]

    # Tipos especiales
    if isinstance(v, ObjectId):
        return str(v)
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, bytes):
        try:
            return base64.b64encode(v).decode("ascii")
        except Exception:
            return None
    if isinstance(v, Decimal):
        try:
            return float(v)
        except Exception:
            return str(v)

    # Valores básicos (int, str, bool, float, None) -> devuelven tal cual
    return v

def jsonify_serialized(obj):
    """Conveniencia: serializa recursivamente y devuelve jsonify."""
    return jsonify(serialize_value(obj))


### IMÁGENES ###

def validar_imagen_base64(cadena_base64):
    try:
        imagen_bytes = base64.b64decode(cadena_base64)
        if len(imagen_bytes) > MAX_IMAGE_SIZE_BYTES:
            max_mb = MAX_IMAGE_SIZE_BYTES // (1024 * 1024)
            return False, f"La imagen supera el tamaño máximo permitido ({max_mb} MB)"
        with Image.open(BytesIO(imagen_bytes)) as imagen:
            imagen.load()  # Fuerza la carga completa
            fmt = imagen.format
        if fmt not in ALLOWED_IMAGE_FORMATS:
            return False, f"Formato no permitido: '{fmt}'. Solo se aceptan JPEG y PNG"
        return True, imagen_bytes
    except Exception as e:
        return False, str(e)
    
def guardar_como_png(imagen_bytes, ruta_salida):
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    with Image.open(BytesIO(imagen_bytes)) as img:
        img = img.convert("RGB")  # Asegura compatibilidad
        img.save(ruta_salida, format="PNG")

def comprobar_tipo(tipo_etq, tipo_esperado):
    tipos = {
        "str": str,
        "bool": bool,
        "int": int,
        "float": float
    }

    return tipo_etq == tipos[tipo_esperado]

### CLASES ###

def get_next_id(db, name="clases_counter"):
    """
    Devuelve el siguiente id entero de forma atómica usando una colección 'counters'.
    """
    doc = db.counters.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return int(doc["seq"])

### NUEVOS ###

@app.route("/predict_image", methods=["POST"])
def predict_image():
    """
    Endpoint para predecir una clase/etiqueta a partir de una imagen base64.
    Clasificación simple: una única salida por imagen.
    Requiere que el modelo y la configuración estén definidos en una carpeta de experimento.
    """
    try:
        data = request.get_json(force=True)
        image_b64 = data.get("imagen")
        modelo_seleccionado = data.get("modelo", None)

        if not image_b64 or not modelo_seleccionado:
            return jsonify({"success": False, "error": "Faltan datos para la predicción"}), 400

        # Convertir la imagen base64 en tensor
        import base64, io
        image_bytes = base64.b64decode(image_b64)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # Cargar configuración y modelo
        device = "cuda" if torch.cuda.is_available() else "cpu"
        experiment_path = data.get("experiments", modelo_seleccionado)
        experiment_path = os.path.splitext(experiment_path)[0]
        experiment_path = os.path.join("./experiments", experiment_path)
        config_path = os.path.join(experiment_path, "config_final.yaml")
        modelo_path = os.path.join("./models", modelo_seleccionado)

        if not os.path.exists(modelo_path):
            return jsonify({"success": False, "error": f"El modelo '{modelo_seleccionado}' no existe"}), 404

        if not os.path.exists(experiment_path):
            return jsonify({"success": False, "error": f"El experimento '{experiment_path}' no existe"}), 404
        config = load_yaml_config(config_path)

        # Completar nombres de clases desde la base de datos si están en "all"
        if config.get("classes") == "all" or config.get("classes") is None:
            clases_docs = list(db["Clases"].find({}, {"_id": 0, "planta": 1, "nombre_comun": 1}))
            clases_unicas = set()
            for doc in clases_docs:
                planta = doc.get("planta", "").strip()
                nombre_comun = doc.get("nombre_comun", "").strip()
                if planta and nombre_comun:
                    clases_unicas.add(f"{planta}___{nombre_comun}")
            config["classes"] = sorted(clases_unicas)

        # Cargar modelo
        model = build_model(config)
        model.load_state_dict(torch.load(modelo_path, map_location=device))
        model.eval().to(device)

        # Transformación
        transform = transforms.Compose([
            transforms.Resize(tuple(config["image_size"])),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])
        tensor_img = transform(image).unsqueeze(0).to(device)

        # Inferencia - Clasificación simple (una cabeza, una salida)
        with torch.no_grad():
            output = model(tensor_img)
            probs = torch.softmax(output, dim=1).squeeze()

            class_to_idx = {c: i for i, c in enumerate(config["classes"])}
            idx_to_class = {i: c for c, i in class_to_idx.items()}

            # Predicción: tomar la clase con mayor probabilidad
            idx_class = probs.argmax().item()
            class_prediction = idx_to_class[idx_class]
            confidence = probs[idx_class].item()

        return jsonify({
            "success": True,
            "class_predicted": class_prediction,
            "confidence": confidence
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    

@app.route("/validar_imagen", methods=["POST"])
def validar_imagen():
    try:
        data = request.get_json(force=True)
        id_doc = data.get("id_doc")

        if not id_doc:
            return jsonify({"success": False, "error": "Falta el ID del documento"})

        # Actualizar en MongoDB
        db.Docs.update_one({"_id": ObjectId(id_doc)}, {"$set": {"validada": True}})
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    
@app.route("/classification_classes", methods=["GET"])
def classification_classes():
    """
    Devuelve la lista única de todas las clases/etiquetas disponibles para clasificación simple.
    Combina valores históricos de 'planta' y 'nombre_comun' en una lista única.
    """
    # Obtener todas las combinaciones únicas planta___nombre_comun como clase única
    clases_docs = list(db.Clases.find({}, {"_id": 0, "planta": 1, "nombre_comun": 1}))
    clases_unicas = set()
    for doc in clases_docs:
        planta = doc.get("planta", "").strip()
        nombre_comun = doc.get("nombre_comun", "").strip()
        if planta and nombre_comun:
            clases_unicas.add(f"{planta}___{nombre_comun}")
    return jsonify(sorted(clases_unicas))

@app.route("/opciones_formatos", methods=["GET"])
def opciones_formatos():
    formatos = list(db.Formato.distinct("formato"))
    return jsonify_serialized(formatos)

@app.route("/opciones_fuentes", methods=["GET"])
def opciones_fuentes():
    fuentes = list(db.Fuente.distinct("fuente"))
    return jsonify_serialized(fuentes)

@app.route("/opciones_modelos", methods=["GET"])
def opciones_modelos():
    modelos = ["MobileNetV2"] # De momento solo MobileNetV2
    return jsonify_serialized(modelos)

@app.route("/opciones_filtros_docs", methods=["GET"])
def opciones_filtros_docs():
    """
    Descubre filtros disponibles en Docs de forma dinamica.
    - Excluye campos no filtrables.
    - Devuelve 'formato' aparte para tratarlo como seleccion unica en UI.
    """
    try:
        excluded_fields = {"_id", "imagen_rgb", "validada", "usuario"}
        max_docs_scan = 1000
        docs_muestreados = 0
        keys_detectadas = set()

        def is_scalar_value(v):
            return v is not None and isinstance(v, (str, int, float, bool)) and str(v).strip() != ""

        def resolve_collection_name(field_name, collection_names_lower):
            candidates = [
                field_name,
                field_name.capitalize(),
                field_name.title(),
                field_name.lower(),
                field_name.upper(),
            ]
            if field_name.endswith("s") and len(field_name) > 1:
                singular = field_name[:-1]
                candidates.extend([singular, singular.capitalize(), singular.title(), singular.lower()])

            for c in candidates:
                c_low = c.lower()
                if c_low in collection_names_lower:
                    return collection_names_lower[c_low]
            return None

        def pick_label_field(collection_name, field_name):
            sample = db[collection_name].find_one({}, {"_id": 0}) or {}
            priority = [
                field_name,
                "nombre",
                "name",
                "valor",
                "descripcion",
                "fuente",
                "formato",
                "planta",
                "nombre_comun",
            ]
            for p in priority:
                if p in sample:
                    return p
            return next(iter(sample.keys()), None)

        # Escanear docs repartiendo la muestra por fuente para evitar sesgo por orden de insercion.
        fuentes_docs = [f for f in db["Docs"].distinct("fuente") if is_scalar_value(f)]

        if fuentes_docs:
            fuentes_ordenadas = sorted(fuentes_docs, key=lambda x: str(x).lower())

            if len(fuentes_ordenadas) > max_docs_scan:
                # Si hay mas fuentes que cupo, muestrear al menos 1 doc de tantas fuentes como permita el limite.
                fuentes_ordenadas = fuentes_ordenadas[:max_docs_scan]
                per_source_limit = 1
            else:
                per_source_limit = max(1, max_docs_scan // len(fuentes_ordenadas))

            for fuente_id in fuentes_ordenadas:
                if docs_muestreados >= max_docs_scan:
                    break
                remaining = max_docs_scan - docs_muestreados
                limit_fuente = min(per_source_limit, remaining)

                for doc in db["Docs"].find({"fuente": fuente_id}, {"_id": 0}).limit(limit_fuente):
                    docs_muestreados += 1
                    keys_detectadas.update(doc.keys())

            # Completar con documentos sin fuente definida si queda cupo.
            if docs_muestreados < max_docs_scan:
                remaining = max_docs_scan - docs_muestreados
                for doc in db["Docs"].find({"fuente": {"$exists": False}}, {"_id": 0}).limit(remaining):
                    docs_muestreados += 1
                    keys_detectadas.update(doc.keys())
        else:
            # Fallback: si no hay campo fuente, usar muestreo simple.
            for doc in db["Docs"].find({}, {"_id": 0}).limit(max_docs_scan):
                docs_muestreados += 1
                keys_detectadas.update(doc.keys())

        keys_permitidas = sorted(k for k in keys_detectadas if k not in excluded_fields)
        collection_names = db.list_collection_names()
        collection_names_lower = {c.lower(): c for c in collection_names}

        filtros_multiseleccion = {}
        formato_opciones = []
        mapeos_ids = {}

        # Campos principales: clases únicas combinadas para clasificación simple
        # sin depender del muestreo de Docs.
        clases_todas = list(db["Clases"].find({}, {"_id": 1, "planta": 1, "nombre_comun": 1}))

        # Construir clases únicas: combinación planta___nombre_comun
        clases_unicas = set()
        class_to_ids = {}
        for c in clases_todas:
            planta = str(c.get("planta", "")).strip()
            nombre_comun = str(c.get("nombre_comun", "")).strip()
            if planta and nombre_comun:
                class_label = f"{planta}___{nombre_comun}"
                clases_unicas.add(class_label)
                if class_label not in class_to_ids:
                    class_to_ids[class_label] = []
                class_to_ids[class_label].append(c["_id"])

        clases_ordenadas = sorted(clases_unicas, key=lambda x: x.lower())
        if clases_ordenadas:
            filtros_multiseleccion["class_label"] = clases_ordenadas
            mapeos_ids["class_label"] = {
                cl: class_to_ids.get(cl, [])
                for cl in clases_ordenadas
            }

        fuentes_todas_docs = list(db["Fuente"].find({}, {"_id": 1, "fuente": 1}))
        fuentes_todas = sorted(
            set(str(f.get("fuente")) for f in fuentes_todas_docs if is_scalar_value(f.get("fuente"))),
            key=lambda x: x.lower(),
        )
        if fuentes_todas:
            filtros_multiseleccion["fuente"] = fuentes_todas
            mapeos_ids["fuente"] = {
                fuente_nombre: [
                    f["_id"]
                    for f in fuentes_todas_docs
                    if is_scalar_value(f.get("fuente")) and str(f.get("fuente")) == fuente_nombre
                ]
                for fuente_nombre in fuentes_todas
            }

        for key in keys_permitidas:
            # Omitir 'clase', 'planta' y 'nombre_comun' - ya procesados como class_label único
            if key in {"clase", "planta", "nombre_comun"}:
                continue

            # Estos campos se construyen desde sus colecciones completas.
            if key == "fuente":
                continue

            raw_values = [v for v in db["Docs"].distinct(key) if is_scalar_value(v)]
            if not raw_values:
                continue

            collection_name = resolve_collection_name(key, collection_names_lower)

            if collection_name:
                label_field = pick_label_field(collection_name, key)
                if label_field:
                    docs_ref = list(
                        db[collection_name].find(
                            {"_id": {"$in": raw_values}},
                            {"_id": 1, label_field: 1},
                        )
                    )
                    id_to_label = {
                        d.get("_id"): d.get(label_field)
                        for d in docs_ref
                        if is_scalar_value(d.get(label_field))
                    }

                    labels = sorted(set(str(id_to_label[v]) for v in raw_values if v in id_to_label), key=lambda x: x.lower())
                    if labels:
                        if key == "formato":
                            formato_opciones = labels
                        else:
                            filtros_multiseleccion[key] = labels
                        mapeos_ids[key] = {
                            str(id_to_label[v]): [v]
                            for v in raw_values
                            if v in id_to_label
                        }
                        continue

            # Campo escalar directo en Docs (sin coleccion de referencia).
            labels_directos = sorted(set(str(v) for v in raw_values), key=lambda x: x.lower())
            if key == "formato":
                formato_opciones = labels_directos
            else:
                filtros_multiseleccion[key] = labels_directos
            mapeos_ids[key] = {str(v): [v] for v in raw_values}

        return jsonify_serialized({
            "success": True,
            "filtros_multiseleccion": filtros_multiseleccion,
            "formato_opciones": formato_opciones,
            "mapeos_ids": mapeos_ids,
            "meta": {
                "docs_muestreados": docs_muestreados,
                "campos_detectados": len(keys_detectadas),
                "campos_filtrables": len(keys_permitidas),
            },
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/subida_masiva", methods=["POST"])
def subida_masiva():
    data = request.get_json(force=True)
    fuente = data.get("fuente")
    procesar = data.get("procesar", False)
    usuario = data.get("usuario")

    if not fuente:
        return jsonify({"success": False, "error": "Falta el nombre de la fuente"}), 400

    script_path = os.path.join(ROOT, "scripts", "subida_masiva_app.py")

    cmd = ["python", script_path, "--fuente", fuente, "--usuario", usuario or "desconocido"]
    if procesar:
        cmd.append("--procesar")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        log_dir = os.path.join(ROOT, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, f"subida_{fuente}.log")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(result.stdout)
            if result.stderr:
                f.write("\n[STDERR]\n" + result.stderr)

        return jsonify({
            "success": True,
            "message": f"Subida completada correctamente para '{fuente}'. Se guardó el log en '{log_path}'."
        })

    except subprocess.CalledProcessError as e:
        output = (e.stdout or "") + (e.stderr or "")
        if "No se encontró la carpeta" in output:
            return jsonify({
                "success": False,
                "error": "No se encontró la carpeta indicada en data/. Verifica el nombre de la fuente y vuelve a intentarlo."
            }), 400

        # Error genérico
        log_dir = os.path.join(ROOT, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, f"subida_error_{fuente}.log")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(output)
        return jsonify({
            "success": False,
            "error": f"Ocurrió un error durante la subida. Revisa el log en '{log_path}'."
        }), 500

@app.route("/listar_fuentes_importadas", methods=["GET"])
def listar_fuentes_importadas():
    try:
        data_dir = os.path.join(ROOT, "data")
        
        if not os.path.isdir(data_dir):
            return jsonify({
                "success": True,
                "fuentes": []
            })

        def _es_fuente_valida(path_fuente):
            color_dir = os.path.join(path_fuente, "color")
            if os.path.isdir(color_dir):
                return True
            if not os.path.isdir(path_fuente):
                return False
            # Compatibilidad: permitir fuentes sin carpeta color si contienen clases directamente.
            return any(
                os.path.isdir(os.path.join(path_fuente, d)) and "___" in d
                for d in os.listdir(path_fuente)
            )
        
        # Listar solo carpetas de datasets (no archivos ni carpetas internas del proyecto)
        carpetas = [
            f for f in os.listdir(data_dir)
            if os.path.isdir(os.path.join(data_dir, f)) and _es_fuente_valida(os.path.join(data_dir, f))
        ]
        carpetas.sort()
        
        return jsonify({
            "success": True,
            "fuentes": carpetas
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/subida_masiva_zip", methods=["POST"])
def subida_masiva_zip():
    try:
        # Validaciones iniciales
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "Falta el archivo ZIP"}), 400
        
        nombre_fuente = request.form.get("nombre_fuente", "").strip()
        if not nombre_fuente:
            return jsonify({"success": False, "error": "Falta el nombre de la fuente"}), 400
        
        zip_file = request.files['file']
        if zip_file.filename == '':
            return jsonify({"success": False, "error": "Archivo no seleccionado"}), 400
        
        if not zip_file.filename.lower().endswith('.zip'):
            return jsonify({"success": False, "error": "El archivo debe ser un ZIP"}), 400
        
        # Validar tamaño (máximo 500MB)
        max_size = 500 * 1024 * 1024
        zip_file.seek(0, os.SEEK_END)
        size = zip_file.tell()
        zip_file.seek(0)
        
        if size > max_size:
            return jsonify({
                "success": False,
                "error": f"El archivo ZIP es demasiado grande. Máximo: 500MB, Actual: {size / (1024*1024):.2f}MB"
            }), 400
        
        if size == 0:
            return jsonify({"success": False, "error": "El archivo ZIP está vacío"}), 400
        
        # Carpeta destino (sin timestamp, solo nombre de fuente)
        dest_dir = os.path.join(ROOT, "data", nombre_fuente)
        
        # Si ya existe, avisar
        if os.path.isdir(dest_dir):
            return jsonify({
                "success": False,
                "error": f"La fuente '{nombre_fuente}' ya existe. Elige otro nombre o elimina la carpeta existente."
            }), 400
        
        os.makedirs(dest_dir, exist_ok=True)
        
        try:
            # Descomprimir ZIP
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(dest_dir)

            # Detectar base de clases válida:
            # 1) data/<fuente>/color/<Planta___Enfermedad>/...
            # 2) data/<fuente>/<Planta___Enfermedad>/...
            # 3) con carpeta contenedora adicional en el ZIP
            color_path = os.path.join(dest_dir, "color")
            candidate_base = None

            if os.path.isdir(color_path):
                candidate_base = color_path
            else:
                root_dirs = [d for d in os.listdir(dest_dir) if os.path.isdir(os.path.join(dest_dir, d)) and d != "__MACOSX"]
                root_class_dirs = [d for d in root_dirs if "___" in d]

                if root_class_dirs:
                    candidate_base = dest_dir
                elif len(root_dirs) == 1:
                    wrapper_dir = os.path.join(dest_dir, root_dirs[0])
                    wrapper_color = os.path.join(wrapper_dir, "color")
                    if os.path.isdir(wrapper_color):
                        candidate_base = wrapper_color
                    else:
                        wrapper_dirs = [d for d in os.listdir(wrapper_dir) if os.path.isdir(os.path.join(wrapper_dir, d)) and d != "__MACOSX"]
                        wrapper_class_dirs = [d for d in wrapper_dirs if "___" in d]
                        if wrapper_class_dirs:
                            candidate_base = wrapper_dir

            if not candidate_base:
                shutil.rmtree(dest_dir, ignore_errors=True)
                return jsonify({
                    "success": False,
                    "error": "Estructura inválida. El ZIP debe contener carpetas 'Planta___Enfermedad' (directamente o dentro de 'color/')."
                }), 400

            # Validar carpetas Planta___Enfermedad con imágenes
            subdirs = [d for d in os.listdir(candidate_base) if os.path.isdir(os.path.join(candidate_base, d))]
            valid_class_dirs = []
            for subdir in subdirs:
                if "___" not in subdir:
                    continue
                subdir_path = os.path.join(candidate_base, subdir)
                contains_images = False
                for _, _, files in os.walk(subdir_path):
                    if any(f.lower().endswith((".jpg", ".jpeg", ".png")) for f in files):
                        contains_images = True
                        break
                if contains_images:
                    valid_class_dirs.append(subdir)

            if not valid_class_dirs:
                shutil.rmtree(dest_dir, ignore_errors=True)
                return jsonify({
                    "success": False,
                    "error": "No se encontraron carpetas válidas 'Planta___Enfermedad' con imágenes .jpg/.jpeg/.png."
                }), 400

            # Normalizar siempre a data/<fuente>/color/<Planta___Enfermedad>/...
            final_color_path = os.path.join(dest_dir, "color")
            os.makedirs(final_color_path, exist_ok=True)
            if candidate_base != final_color_path:
                for class_dir in valid_class_dirs:
                    src = os.path.join(candidate_base, class_dir)
                    dst = os.path.join(final_color_path, class_dir)
                    if os.path.exists(dst):
                        shutil.rmtree(dest_dir, ignore_errors=True)
                        return jsonify({
                            "success": False,
                            "error": f"Conflicto al normalizar estructura: la carpeta '{class_dir}' ya existe en color/."
                        }), 400
                    shutil.move(src, dst)
            
            # Guardar backup del ZIP en logs/zips/
            zips_backup_dir = os.path.join(ROOT, "logs", "zips")
            os.makedirs(zips_backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_zip_path = os.path.join(zips_backup_dir, f"{timestamp}_{nombre_fuente}.zip")
            zip_file.seek(0)
            with open(backup_zip_path, 'wb') as f:
                f.write(zip_file.read())
            
            return jsonify({
                "success": True,
                "message": f"ZIP descomprimido correctamente en 'data/{nombre_fuente}/'. Backup guardado en '{backup_zip_path}'."
            })
        
        except zipfile.BadZipFile:
            shutil.rmtree(dest_dir, ignore_errors=True)
            return jsonify({
                "success": False,
                "error": "El archivo ZIP está corrompido o no es válido"
            }), 400
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error inesperado: {str(e)}"
        }), 500

@app.route("/editar_clases", methods=["GET"])
def editar_clases():
    try:
        clases_cursor = db.Clases.find()
        clases = []
        for c in clases_cursor:
            doc = {}
            for k, v in c.items():
                if isinstance(v, ObjectId):
                    doc[k] = str(v)
                else:
                    doc[k] = v
            clases.append(doc)
        return jsonify({"success": True, "clases": clases})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/reemplazar_clases", methods=["POST"])
def reemplazar_clases():
    try:
        data = request.get_json(force=True)
        nuevas_clases = data.get("clases", [])
        if not isinstance(nuevas_clases, list):
            return jsonify({"success": False, "error": "Formato inválido: 'clases' debe ser una lista"}), 400

        existing = list(db.Clases.find())
        orig_map = {doc["_id"]: doc for doc in existing}

        incoming_ids = [c.get("_id") for c in nuevas_clases if "_id" in c]
        if len(incoming_ids) != len(set(incoming_ids)):
            return jsonify({"success": False, "error": "IDS duplicados en el payload"}), 400

        # crear un backup único (documento) y rotarlo manteniendo N backups
        backup_obj_id, backup_id = store_clases_backup_single(db, existing, max_backups=5, ttl_days=30)

        ops = []
        ids_editados = set()

        # sincronizar contador con el máximo actual antes de asignar nuevos ids
        max_doc = db.Clases.find_one(sort=[("_id", -1)])
        max_id = max_doc["_id"] if max_doc else -1
        ensure_counter_at_least(db, "clases_counter", max_id)

        for c in nuevas_clases:
            doc = dict(c)  
            if "_id" in doc and doc["_id"] in orig_map:
                idv = doc["_id"]
                ids_editados.add(idv)
                new_fields = {k: v for k, v in doc.items() if k != "_id"}
                if new_fields:
                    ops.append(UpdateOne({"_id": idv}, {"$set": new_fields}))
            else:
                if "_id" not in doc:
                    doc["_id"] = get_next_id(db, "clases_counter")
                ids_editados.add(doc["_id"])
                ops.append(InsertOne(doc))

        ids_to_delete = [i for i in orig_map.keys() if i not in ids_editados]
        for i in ids_to_delete:
            ops.append(DeleteOne({"_id": i}))

        if ops:
            result = db.Clases.bulk_write(ops)
            resp = {
                "success": True,
                "matched_count": getattr(result, "matched_count", 0),
                "modified_count": getattr(result, "modified_count", 0),
                "inserted_count": getattr(result, "inserted_count", 0) if hasattr(result, "inserted_count") else len([op for op in ops if isinstance(op, InsertOne)]),
                "deleted_count": getattr(result, "deleted_count", 0),
                "backup_id": backup_id
            }
            return jsonify(resp)
        else:
            return jsonify({"success": True, "message": "No hay cambios", "backup_id": backup_id})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/add_class", methods=["POST"])
def add_class():
    data = request.get_json()
    required = ["planta", "nombre_comun"]
    if not all(k in data for k in required):
        return jsonify({"success": False, "error": "Faltan campos obligatorios"}), 400

    new_doc = dict(data)

    max_doc = db.Clases.find_one(sort=[("_id", -1)])
    max_id = max_doc["_id"] if max_doc else -1
    ensure_counter_at_least(db, "clases_counter", max_id)

    for attempt in range(3):
        nuevo_id = get_next_id(db, "clases_counter")
        new_doc["_id"] = nuevo_id
        try:
            db.Clases.insert_one(new_doc)
            return jsonify({"success": True, "clase": new_doc})
        except DuplicateKeyError:
            continue

    ensure_counter_at_least(db, "clases_counter", db.Clases.find_one(sort=[("_id", -1)])["_id"])
    return jsonify({"success": False, "error": "No se pudo asignar un id único, inténtalo de nuevo"}), 500

@app.route("/crear_experimento", methods=["POST"])
def crear_experimento():
    try:
        data = request.get_json(force=True)
        experiment_name = data.get("experiment_name")
        config_variables = data.get("config_variables", {})

        if not experiment_name:
            return jsonify({"success": False, "error": "Falta el nombre del experimento"}), 400
        
        if config_variables.get("imagenes_por_clase") == "all":
            clases = db["Clases"].distinct("planta")
            total_imagenes = {}
            for clase in clases:
                total_imagenes[clase] = db["Docs"].count_documents({"clase": clase})
            config_variables["imagenes_por_clase"] = max(total_imagenes.values())

        mapeo_modelos = {
            "MobileNetV2": "MobileNet_V2_Weights.DEFAULT"
        }

        # Renombrar "modelo" a "weights" si existe
        if "modelo" in config_variables:
            modelo = config_variables.pop("modelo")
            config_variables["weights"] = mapeo_modelos.get(modelo, modelo)

        script_path = os.path.join(os.path.dirname(__file__), "scripts", "make_experiment.py")
        cmd = ["python", script_path, experiment_name]

        if config_variables:
            cmd.append("--config")
            cmd.append(json.dumps(config_variables))

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return jsonify({"success": False, "error": result.stderr}), 500

        return jsonify({"success": True, "message": f"Experimento '{experiment_name}' creado correctamente."})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
@app.route("/obtener_experimentos", methods=["GET"])
def obtener_experimentos():
    """
    Devuelve la lista de experimentos actuales, incluyendo config y metrics.
    """
    try:
        base_path = "./experiments"
        experimentos = []
        for nombre in os.listdir(base_path):
            if not os.path.isdir(os.path.join(base_path, nombre)) or nombre == "comparison":
                continue

            exp_info = {"nombre": nombre, "config": None, "metrics": None}

            exp_info["config"] = load_yaml_config(os.path.join(base_path, nombre, "config.yaml"))

            metrics_path = os.path.join(base_path, nombre, "results", "metrics.json")
            if os.path.exists(metrics_path):
                try:
                    with open(metrics_path, "r", encoding="utf-8") as f:
                        exp_info["metrics"] = json.load(f)
                except Exception as e:
                    exp_info["metrics"] = {"error": f"No se pudo leer metrics.json: {str(e)}"}

            experimentos.append(exp_info)

        return jsonify({"success": True, "experimentos": experimentos})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
@app.route("/solicitar_entrenamiento", methods=["POST"])
def solicitar_entrenamiento():
    """
    Registra una solicitud de entrenamiento de un modelo.
    """
    try:
        data = request.get_json()
        nombre_experimento = data.get("nombre")
        usuario = data.get("usuario")
        disponible_prediccion = data.get("disponible_prediccion", False)

        if not nombre_experimento:
            return jsonify({"success": False, "error": "Falta el nombre del experimento"}), 400

        db["Entrenamientos"].insert_one({
            "nombre": nombre_experimento,
            "usuario": usuario,
            "disponible_prediccion": disponible_prediccion,
            "created_at": datetime.utcnow()
        })

        return jsonify({"success": True, "message": f"Solicitud de entrenamiento para '{nombre_experimento}' registrada correctamente."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
@app.route("/obtener_solicitudes_entrenamiento", methods=["GET"])
def obtener_solicitudes_entrenamiento():
    """
    Devuelve la lista de solicitudes de entrenamiento.
    """
    try:
        solicitudes = list(db["Entrenamientos"].find().sort("created_at", -1))
        return jsonify_serialized({"success": True, "solicitudes": solicitudes})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
@app.route("/entrenar_modelo", methods=["POST"])
def entrenar_modelo():
    """
    Ejecuta el entrenamiento de un modelo.
    Si el entrenamiento termina correctamente, elimina el experimento de la colección 'Experimentos'.
    El admin decide si acepta hacer el modelo disponible para predicción mediante el parámetro aceptar_disponible_prediccion.
    """
    try:
        data = request.get_json()
        nombre_experimento = data.get("nombre")
        aceptar_disponible_prediccion = data.get("aceptar_disponible_prediccion", False)

        if not nombre_experimento:
            return jsonify({"success": False, "error": "Falta el nombre del experimento"}), 400
        
        if not os.path.exists(os.path.join("experiments", nombre_experimento)):
            try:
                deleted = db["Entrenamientos"].delete_one({"nombre": nombre_experimento})
                if deleted.deleted_count:
                    return jsonify({
                        "success": False,
                        "error": f"El experimento '{nombre_experimento}' no existe. Se eliminaron {deleted.deleted_count} solicitud(es) de entrenamiento asociada(s)."
                    }), 404
            except Exception:
                    pass
            return jsonify({"success": False, "error": f"El experimento '{nombre_experimento}' no existe"}), 404

        # Ejecutar el script run_experiment.py
        script_path = os.path.join(os.path.dirname(__file__), "experiments", nombre_experimento, "run_experiment.py")
        print("Ejecutando script de entrenamiento:", script_path)
        if not os.path.exists(script_path):
            return jsonify({"success": False, "error": "No se encontró el script de entrenamiento para este experimento"}), 404

        # Silenciar la salida del proceso (se guarda en result.stdout / result.stderr y no aparece por pantalla)
        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print("Error en el entrenamiento:", result.stderr)
            return jsonify({"success": False, "error": result.stderr}), 500

        # Normalizar nombre del modelo entrenado a <experimento>.pth.
        models_dir = os.path.join("experiments", nombre_experimento, "models")
        modelo_best = os.path.join(models_dir, "best_model.pth")
        modelo_experimento = os.path.join(models_dir, f"{nombre_experimento}.pth")

        if os.path.exists(modelo_best):
            if os.path.exists(modelo_experimento):
                os.remove(modelo_experimento)
            os.replace(modelo_best, modelo_experimento)
            print(f"Modelo renombrado a {modelo_experimento}")

        # Si el entrenamiento fue correcto, verificar si el admin acepta disponibilidad para predicción
        try:
            solicitud = db["Entrenamientos"].find_one({"nombre": nombre_experimento})
            
            # Si el admin acepta hacer el modelo disponible para predicción, copiarlo a models/
            # Nota: El usuario puede haber solicitado disponibilidad (solicitud.get("disponible_prediccion")),
            # pero la decisión final es del admin (aceptar_disponible_prediccion)
            if aceptar_disponible_prediccion:
                modelo_origen = os.path.join("experiments", nombre_experimento, "models", f"{nombre_experimento}.pth")
                if not os.path.exists(modelo_origen):
                    # Compatibilidad con experimentos antiguos.
                    modelo_origen = os.path.join("experiments", nombre_experimento, "models", "best_model.pth")
                modelo_destino = os.path.join("models", f"{nombre_experimento}.pth")
                
                # Crear carpeta models/ si no existe
                os.makedirs("models", exist_ok=True)
                
                # Copiar el modelo
                if os.path.exists(modelo_origen):
                    shutil.copy2(modelo_origen, modelo_destino)
                    print(f"Modelo copiado a {modelo_destino} (aprobado por admin)")
                else:
                    print(f"Advertencia: No se encontró el modelo en {modelo_origen}")
            
            # Eliminar el documento de Entrenamientos
            delete_res = db["Entrenamientos"].delete_one({"nombre": nombre_experimento})
            lista = []
            for doc in db["Entrenamientos"].find():
                lista.append(serialize_value(doc))
            if delete_res.deleted_count > 0:
                msg = f"Modelo '{nombre_experimento}' entrenado correctamente. Experimento eliminado de la colección 'Entrenamientos'."
            else:
                msg = [f"Modelo '{nombre_experimento}' entrenado correctamente. No se encontró documento en 'Entrenamientos' para eliminar.", lista, nombre_experimento]
        except Exception as e:
            # Entrenamiento OK pero fallo al eliminar en la BBDD
            return jsonify({"success": True, "message": f"Modelo '{nombre_experimento}' entrenado correctamente, pero fallo al eliminar experimento: {str(e)}"})

        return jsonify({"success": True, "message": msg})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
@app.route("/obtener_modelos", methods=["GET"])
def obtener_modelos():
    """
    Devuelve la lista de modelos disponibles.
    """
    try:
        base_path = "./models"
        modelos = [
            nombre
            for nombre in os.listdir(base_path)
            if nombre.endswith(".pth")
        ]
        return jsonify({"success": True, "modelos": modelos})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    

@app.route("/cambiar_url_bbdd", methods=["POST"])
def cambiar_url_bbdd():
    nueva_url = request.json.get("url_bbdd")
    if not nueva_url:
        return jsonify({"success": False, "message": "No se proporcionó una URL válida"}), 400

    try:
        global db
        db = connect_to_database(uri=nueva_url)
        return jsonify({"success": True, "message": f"Conectado a la nueva base de datos: {nueva_url}"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error al conectar a la base de datos: {str(e)}"}), 500

@app.route("/obtener_resultados_experimento", methods=["GET"])
def obtener_resultados_experimento():
    try:
        nombre_experimento = request.args.get("nombre_experimento")
        if not nombre_experimento:
            return jsonify({"success": False, "error": "Falta el nombre del experimento"}), 400

        carpeta_resultados = Path(f"./experiments/{nombre_experimento}/results")
        if not carpeta_resultados.exists() or not carpeta_resultados.is_dir():
            return jsonify({"success": False, "error": "No se encontraron resultados para este experimento"}), 404

        archivos_resultados = [
            archivo.name for archivo in carpeta_resultados.iterdir()
            if archivo.suffix in [".png", ".jpg"]
        ]

        return jsonify({"success": True, "resultados": archivos_resultados})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
@app.route("/imagen_resultado", methods=["GET"])
def imagen_resultado():
    """
    Sirve una imagen de resultados de un experimento.
    Parámetros GET:
      - experimento: nombre del experimento
      - archivo: nombre del archivo de imagen (png/jpg)
    """
    experimento = request.args.get("experimento")
    archivo = request.args.get("archivo")
    if not experimento or not archivo:
        return jsonify({"success": False, "error": "Faltan parámetros"}), 400
    if "/" in archivo or ".." in archivo or "\\" in archivo:
        return jsonify({"success": False, "error": "Nombre de archivo no permitido"}), 400
    ruta = os.path.join("./experiments", experimento, "results", archivo)
    if not os.path.isfile(ruta):
        return jsonify({"success": False, "error": "Archivo no encontrado"}), 404
    mime, _ = mimetypes.guess_type(ruta)
    if not mime:
        mime = "application/octet-stream"
    return send_file(ruta, mimetype=mime)

@app.route("/imagen_comparacion", methods=["GET"])
def imagen_comparacion():
    """
    Sirve una imagen de comparación de experimento.
    Parámetros GET:
      - ruta: ruta absoluta o relativa al archivo de imagen de comparación
    """
    ruta = request.args.get("ruta")
    if not ruta:
        return jsonify({"success": False, "error": "Faltan parámetros"}), 400
    # Normaliza la ruta y comprueba que está dentro de experiments/comparison
    ruta_normalizada = os.path.normpath(ruta)
    ruta_normalizada = os.path.join(".", ruta_normalizada)
    base_dir = os.path.normpath(os.path.join(".", "experiments", "comparison"))
    abs_ruta = os.path.abspath(ruta_normalizada)
    abs_base = os.path.abspath(base_dir)

    if not abs_ruta.startswith(abs_base):
        print("Nombre no perimitido: Acceso denegado a la ruta:", abs_ruta)
        return jsonify({"success": False, "error": "Nombre de archivo no permitido"}), 400
    if not os.path.isfile(abs_ruta):
        return jsonify({"success": False, "error": "Archivo no encontrado"}), 404
    mime, _ = mimetypes.guess_type(abs_ruta)
    if not mime:
        mime = "application/octet-stream"
    return send_file(abs_ruta, mimetype=mime)
    
@app.route("/comparar_experimentos", methods=["POST"])
def comparar_experimentos():
    try:
        data = request.get_json(force=True)
        experimentos = data.get("experimentos", [])

        if len(experimentos) < 2:
            return jsonify({"success": False, "error": "Debes seleccionar al menos dos experimentos para comparar."}), 400

        base_path = os.path.join(ROOT, "experiments")
        comparison_folder = os.path.join(base_path, "comparison", "_vs_".join(experimentos))
        os.makedirs(comparison_folder, exist_ok=True)

        all_metrics = {}
        for experiment in experimentos:
            experiment_path = os.path.join(base_path, experiment)
            metrics_file = os.path.join(experiment_path, "results", "metrics.json")
            if os.path.exists(metrics_file):
                with open(metrics_file, "r") as f:
                    all_metrics[experiment] = json.load(f)

        if not all_metrics:
            return jsonify({"success": False, "error": "No se encontraron métricas para los experimentos seleccionados."}), 404

        combined_metrics = ["accuracy_planta", "accuracy_enfermedad", "accuracy_combinada"]
        x = range(len(experimentos))

        plt.figure()
        width = 0.2
        for i, metric in enumerate(combined_metrics):
            values = [
                all_metrics[experiment]["test"].get(metric, 0) for experiment in experimentos
            ]
            plt.bar([pos + i * width for pos in x], values, width=width, label=metric)

        plt.title("Comparación de Accuracy")
        plt.xlabel("Experimentos")
        plt.ylabel("Accuracy")
        plt.xticks([pos + width for pos in x], experimentos)
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        accuracy_path = os.path.join(comparison_folder, "comparison_accuracy_combined.png")
        plt.savefig(accuracy_path)
        plt.close()

        f1_metrics = ["f1_planta", "f1_enfermedad"]
        plt.figure()
        width = 0.3
        for i, metric in enumerate(f1_metrics):
            values = [
                all_metrics[experiment]["test"].get(metric, 0) for experiment in experimentos
            ]
            plt.bar([pos + i * width for pos in x], values, width=width, label=metric)

        plt.title("Comparación de F1-Score")
        plt.xlabel("Experimentos")
        plt.ylabel("F1-Score")
        plt.xticks([pos + width / 2 for pos in x], experimentos)
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        f1_path = os.path.join(comparison_folder, "comparison_f1_combined.png")
        plt.savefig(f1_path)
        plt.close()

        return jsonify({
            "success": True,
            "graficos": {
                "accuracy": str(accuracy_path),
                "f1_score": str(f1_path),
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
@app.route("/obtener_graficos_comparacion", methods=["GET"])
def obtener_graficos_comparacion():
    try:
        # Obtener los nombres de los experimentos desde los parámetros de la solicitud
        experimentos = request.args.getlist("experimentos")
        if len(experimentos) < 2:
            return jsonify({"success": False, "error": "Debes proporcionar al menos dos experimentos."}), 400

        # Construir la ruta de la carpeta de comparación
        base_path = Path("./experiments/comparison")
        comparison_folder = base_path / "_vs_".join(experimentos)

        # Verificar si la carpeta existe
        if not comparison_folder.exists() or not comparison_folder.is_dir():
            return jsonify({"success": False, "error": "No se encontraron gráficos para la comparación solicitada."}), 404

        # Obtener los archivos de gráficos en la carpeta
        graficos = [
            str(archivo) for archivo in comparison_folder.iterdir()
            if archivo.suffix in [".png", ".jpg"]
        ]

        if not graficos:
            return jsonify({"success": False, "error": "No se encontraron gráficos en la carpeta de comparación."}), 404

        return jsonify({"success": True, "graficos": graficos})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

### FIN NUEVOS ###
    

### IMÁGENES ###

@app.route("/recuperar_campos", methods=["GET"])
def recuperar_campos():
    res = db.Campos.find()
    return jsonify_serialized(res)

@app.route("/etiquetas", methods=["GET"])
def etiquetas():
    coleccion = db["Clases"]
    res = list(coleccion.find({}, {"_id": 1, "planta": 1, "clasificacion": 1, "nombre_comun": 1}))

    etiquetas_vistas = set()
    etiquetas = []

    for r in res:
        id = r.get("_id", "")
        if id not in etiquetas_vistas:
            etiquetas_vistas.add(id)
            etiquetas.append({
                "_id": id,
                "planta": r.get("planta", ""),
                "clasificacion": r.get("clasificacion", ""),
                "nombre": r.get("nombre_comun", "")
            })

    return jsonify(etiquetas)

@app.route("/recuperar_etiquetas/<nombre_coleccion>", methods=["GET"])
def devolver_etiquetas(nombre_coleccion):
    if nombre_coleccion not in db.list_collection_names():
        abort(400, description="El nombre de la coleccion no es correcto")
    coleccion = db[nombre_coleccion]
    res = coleccion.find()
    return jsonify_serialized(res)

@app.route("/add_etiqueta", methods=["POST"])
def add_etiqueta():
    nombre_coleccion = request.json["coleccion"]
    etiqueta = request.json.get("etiqueta")

    campo_guardado = db.Campos.find_one({"coleccion": nombre_coleccion})
    if campo_guardado is None:
        abort(400, description=f"No se ha encontrado ningun campo una coleccion {nombre_coleccion}")
    else:
        campos_etiqueta = campo_guardado["campos_etiqueta"]
        if sorted(etiqueta.keys()) != sorted(campos_etiqueta.keys()):
            abort(400, description=f"Los campos de la etiqueta proporcionada no son correctos")
        for campo in list(etiqueta.keys()):
            if not comprobar_tipo(type(etiqueta[campo]), campos_etiqueta[campo]):
                abort(400, f"El tipo del campo {campo}: {type(etiqueta[campo])} no coincide con el tipo almacenado: " + campos_etiqueta[campo])

    coleccion = db[nombre_coleccion]
    ultimo = coleccion.find_one(sort=[('_id', -1)])
    nuevo_id = (ultimo['_id'] + 1) if ultimo else 0

    etiqueta["_id"] = nuevo_id

    coleccion.insert_one(etiqueta)

    return jsonify(success=True, etiqueta=etiqueta)

@app.route("/modificar_etiqueta", methods=["POST"])
def modificar_etiqueta():
    nombre_coleccion = request.json["nombre_coleccion"]
    etiqueta = request.json.get("etiqueta")

    if type(etiqueta) != dict:
        abort(400, description="El formato de la etiqueta es incorrecto")

    campos_etiqueta = db.Campos.find_one({"coleccion": nombre_coleccion})
    if campos_etiqueta is None:
        abort(400, description=f"No se ha encontrado ningun campo con el nombre {nombre_coleccion}")
    else:
        campos_etiqueta = campos_etiqueta["campos_etiqueta"]
        if sorted(etiqueta.keys()) != sorted(campos_etiqueta.append("_id")):
            abort(400, description=f"Los campos de la etiqueta proporcionada no son correctos")


    coleccion = db[nombre_coleccion]

    coleccion.replace_one({"_id": etiqueta["_id"]}, etiqueta, upsert=False)

    return jsonify(success=True)

@app.route("/devolver_campos_etiqueta/<nombre_campo>", methods=["GET"])
def devolver_campos(nombre_campo):
    campos_etiqueta = db.Campos.find_one({"nombre": nombre_campo},{"campos_etiqueta": 1})
    if campos_etiqueta is None:
        abort(400, description=f"No se ha encontrado ningun campo con el nombre {nombre_campo}")
    return jsonify(campos_etiqueta["campos_etiqueta"])

@app.route("/add_campo", methods=["POST"])
def add_campo():
    nombre = request.json["nombre"]
    cod = int(request.json["cod"])

    campo = {
        "nombre": nombre,
        "cod": cod
    }

    if cod == 4 or cod == 0:
        # Este es un diccionario que tiene como clave el nombre del campo y como valor su tipo esperado en formato texto (str, bool o int, no se admiten más)
        campos_etiqueta = request.json.get("campos_etiqueta")
        nombre_coleccion = request.json["coleccion"]
        if campos_etiqueta is None:
            abort(400, "Falta por especificar los campos de la etiqueta")
        else:
            for nombre_campo in campos_etiqueta:
                if campos_etiqueta[nombre_campo] not in ["str", "bool", "int", "float"]:
                    abort(400, f"El campo {nombre_campo} tiene un tipo no admitido, solo se admiten valores 'str', 'bool' o 'int'")
        campo["campos_etiqueta"] = campos_etiqueta
        campo["coleccion"] = nombre_coleccion
        
    db.Campos.insert_one(campo)

    return jsonify(success=True)

@app.route("/eliminar_campo", methods=["POST"])
def eliminar_campo():
    nombre = request.json["nombre"]
    campo = db.Campos.find_one({"nombre": nombre})
    cod = int(campo["cod"])

    if cod == 0:
        abort(400, "No se puede eliminar este campo")
    elif db.Docs.find_one({nombre: {"$exists": True}}) is None:
        db.Campos.delete_one({"nombre": nombre})
        return jsonify(success=True)
    else:
        abort(400, "No se puede eliminar este campo porque hay al menos una imagen que lo posee")
    
@app.route("/add_dato", methods=["POST"])
def add_dato():
    # _id = ObjectId(request.json["id"])
    # nombre_campo = request.json["nombre_campo"]
    # valor = request.json["valor"]
    # cod = int(db.Campos.find_one({"nombre": nombre_campo})["cod"])

    # if cod != 3:
    #     db.Docs.update_one({"_id": _id}, {"$set": {f"{nombre_campo}": valor}})
    #     return jsonify(success=True)
    # if cod == 3:
    #     imagen = base64.b64decode(valor)

    #     nombre_imagen = time.strftime("%H-%M-%S-%f_%m_%d_%Y", time.localtime()) + ".png"

    #     with open(f"./imagenes/{nombre_imagen}", "wb") as f:
    #         f.write(imagen)

    #     uri_imagen = f"http://158.42.184.169:5001/imagen_base64/{nombre_imagen}",

    #     db.Docs.update_one({"_id": _id}, {"$set": {f"{nombre_campo}": uri_imagen}})
    #     return jsonify(success=True)
    _id = ObjectId(request.json["id"])
    campos_extra = request.json.get("campos_extra")
    if campos_extra is not None:
        imagenes_extra = []
        for nombre_campo in campos_extra:
            valor = campos_extra[nombre_campo]
            campo_almacenado = db.Campos.find_one({"nombre": nombre_campo})
            if campo_almacenado is None:
                abort(400, f"El campo {nombre_campo} no se encuentra en la base de datos")
            else:
                cod_campo = campo_almacenado["cod"]
                if cod_campo == 1 and type(valor) is not int:
                    abort(400, f"Tipo del campo {nombre_campo} incorrecto, se esperaba int pero se detectó {type(valor)}")
                elif cod_campo == 2 and type(valor) is not str:
                    abort(400, f"Tipo del campo {nombre_campo} incorrecto, se esperaba str pero se detectó {type(valor)}")
                elif cod_campo == 3:
                    correcto, res = validar_imagen_base64(valor)
                    if not correcto:
                        abort(400, f"La imagen {nombre_campo} ha provocado la siguiente excepcion: " + res)
                    nombre_imagen = str(uuid.uuid3(uuid.NAMESPACE_URL, res)) + ".png"
                    imagenes_extra.append((nombre_imagen, base64.b64decode(res)))
                    campos_extra[nombre_campo] = get_image_url(nombre_imagen)
                    # Nos guardamos en una lista el nombre de la imagen y la codificación para insertarla más tarde si no hay errores
                elif cod_campo == 0 or cod_campo == 4:
                    if type(valor) is not int:
                        abort(400, f"Tipo del campo {nombre_campo} incorrecto, los identificadores de las etiquetas son int pero se detectó {type(valor)}")
                    else:
                        etiqueta = db[campo_almacenado["coleccion"]].find_one({"_id": valor})
                        if etiqueta is None:
                            abort(400, f"No existe una etiqueta de {nombre_campo} con el identificador {valor}")

        for nombre_imagen, imagen in imagenes_extra:
            os.makedirs(IMAGES_DIR, exist_ok=True)
            with open(os.path.join(IMAGES_DIR, nombre_imagen), "wb") as f:
                f.write(imagen)

    db.Docs.update_one({"_id": _id}, {"$set": campos_extra})
    return jsonify(success=True)

@app.route("/eliminar_dato", methods=["POST"])
def eliminar_dato():
    _id = ObjectId(request.json["id"])
    nombre_campo = request.json["nombre_campo"]
    cod = int(db.Campos.find_one({"nombre": nombre_campo})["cod"])

    if cod != 3:
        db.Docs.update_one({"_id": _id}, {"$unset": {f"{nombre_campo}": ""}})
        return jsonify(success=True)
    if cod == 3:
        archivo = db.Docs.find_one({"_id": _id})
        nombre_imagen = re.search(r"[^/]+$", archivo[f"{nombre_campo}"]).group()
        os.remove(os.path.join(IMAGES_DIR, nombre_imagen))
        db.Docs.update_one({"_id": _id}, {"$unset": {f"{nombre_campo}": ""}})

        return jsonify(success=True)


@app.route("/docs", methods=["GET"])
def devolver_docs():
    clasificacion = request.args.get('clasificacion', None)
    nombre = request.args.get('nombre', None)

    res = None
    if clasificacion is not None:
        if nombre is not None:
            etiqueta = db.Etiquetas.find_one({"clasificacion": clasificacion, "nombre": nombre}, {"_id": 1})
            if not etiqueta:
                return jsonify_serialized([])
            res = db.Docs.find({"clase": etiqueta["_id"]},{})
        else:
            id_etiqueta = db.Etiquetas.find({"clasificacion": clasificacion}, {"_id": 1})
            res = []
            for etiqueta in id_etiqueta:
                res.append(db.Docs.find_one({"clase": etiqueta["_id"]},{}))
            res = filter(None, res)
    else:
        res = db.Docs.find()

    return jsonify_serialized(list(res))

@app.route("/clasificar", methods=["POST"])
def etiquetar_doc():
    id_etiqueta = request.json["etiqueta"]
    id_doc = request.json["doc"]
    try:
        id_doc = ObjectId(id_doc)
    except Exception:
        return jsonify({"success": False, "error": "El ID del documento no es válido"}), 400

    db.Docs.update_one({"_id": id_doc}, {"$set": {"clase": id_etiqueta}})

    return jsonify({"success": True})

@app.route("/imagen_base64/<nombre_imagen>", methods=["GET"])
def devolver_imagen_base64(nombre_imagen):
    imagen = Image.open(os.path.join(IMAGES_DIR, nombre_imagen), mode='r')
    bytes_array = io.BytesIO()
    imagen.save(bytes_array, format=imagen.format)
    #bytes_array = bytes_array.getvalue()
    b64_image = base64.b64encode(bytes_array.getvalue())

    return jsonify({"imagen_b64": b64_image.decode("utf-8")})

@app.route("/servir_n_archivos", methods=["GET"])
def devolver_x_archivos():
    inicio = request.args.get('inicio', 0, type=int)
    n_archivos = request.args.get('n_archivos', 10, type=int)

    planta = request.args.get('planta')
    enfermedad = request.args.get('enfermedad')
    formato = request.args.get('formato')
    fuente = request.args.get('fuente')

    filtros = {}

    if planta or enfermedad:
        clase_query = {}
        if planta:
            clase_query["planta"] = planta
        if enfermedad:
            clase_query["nombre_comun"] = enfermedad

        clases_ids = [c["_id"] for c in db.Clases.find(clase_query, {"_id": 1})]
        if clases_ids:
            filtros["clase"] = {"$in": clases_ids}
        else:
            return jsonify([])

    if formato:
        formato_doc = db.Formato.find_one({
            "$or": [
                {"formato": formato},
                {"nombre": formato},
            ]
        })
        if formato_doc:
            filtros["formato"] = formato_doc["_id"]
        else:
            return jsonify_serialized([])

    if fuente:
        fuente_doc = db.Fuente.find_one({
            "$or": [
                {"fuente": fuente},
                {"nombre": fuente},
            ]
        })
        if fuente_doc:
            filtros["fuente"] = fuente_doc["_id"]
        else:
            return jsonify_serialized([])

    res = list(db.Docs.find(filtros).skip(inicio).limit(n_archivos))
    return jsonify_serialized(res)

@app.route("/servir_n_archivos_sin_validar", methods=["GET"])
def devolver_x_archivos_sin_validar():
    inicio = request.args.get('inicio', 0, type=int)
    n_archivos = request.args.get('n_archivos', 10, type=int)

    planta = request.args.get('planta')
    enfermedad = request.args.get('enfermedad')
    formato = request.args.get('formato')
    fuente = request.args.get('fuente')

    filtros = {"validada": False}

    if planta or enfermedad:
        clase_query = {}
        if planta:
            clase_query["planta"] = planta
        if enfermedad:
            clase_query["nombre_comun"] = enfermedad

        clases_ids = [c["_id"] for c in db.Clases.find(clase_query, {"_id": 1})]
        if clases_ids:
            filtros["clase"] = {"$in": clases_ids}
        else:
            return jsonify([])

    if formato:
        formato_doc = db.Formato.find_one({
            "$or": [
                {"formato": formato},
                {"nombre": formato},
            ]
        })
        if formato_doc:
            filtros["formato"] = formato_doc["_id"]
        else:
            return jsonify(serialize_value([]))

    if fuente:
        fuente_doc = db.Fuente.find_one({
            "$or": [
                {"fuente": fuente},
                {"nombre": fuente},
            ]
        })
        if fuente_doc:
            filtros["fuente"] = fuente_doc["_id"]
        else:
            return jsonify(serialize_value([]))

    res = list(db.Docs.find(filtros).skip(inicio).limit(n_archivos))
    return jsonify(serialize_value(res))

@app.route("/subir_imagen", methods=["POST"])
def subir_imagen():
    data = request.get_json(force=True)
    correcto, res = validar_imagen_base64(data["imagen_b64"])
    if not correcto:
        abort(400, f"La imagen principal ha provocado la siguiente excepcion: " + res)
    #imagen = base64.b64decode(res)

    clase = int(data["clase"])
    usuario = data.get("usuario")

    nombre_imagen = str(uuid.uuid3(uuid.NAMESPACE_URL, data["imagen_b64"])) + ".png"
    image_path = os.path.join(IMAGES_DIR, nombre_imagen)
    image_url = get_image_url(nombre_imagen)

    if os.path.isfile(image_path):
        # Borra posible doc previo con esa imagen, independientemente del host guardado en la URL.
        db.Docs.delete_one({"imagen_rgb": {"$regex": f"/imagen_base64/{re.escape(nombre_imagen)}$"}})

    guardar_como_png(imagen_bytes=res, ruta_salida=image_path)

    doc = {
        "imagen_rgb": image_url,
        "validada": False,
        "usuario": usuario,
        "clase": clase
    }

    campos_extra = request.json.get("campos_extra")
    if campos_extra is not None:
        imagenes_extra = []
        for nombre_campo in campos_extra:
            valor = campos_extra[nombre_campo]
            campo_almacenado = db.Campos.find_one({"nombre": nombre_campo})
            if campo_almacenado is None:
                abort(400, f"El campo {nombre_campo} no se encuentra en la base de datos")
            else:
                cod_campo = campo_almacenado["cod"]
                if cod_campo == 1 and type(valor) is not int:
                    abort(400, f"Tipo del campo {nombre_campo} incorrecto, se esperaba int pero se detectó {type(valor)}")
                elif cod_campo == 2 and type(valor) is not str:
                    abort(400, f"Tipo del campo {nombre_campo} incorrecto, se esperaba str pero se detectó {type(valor)}")
                elif cod_campo == 3:
                    correcto, res = validar_imagen_base64(valor)
                    if not correcto:
                        abort(400, f"La imagen {nombre_campo} ha provocado la siguiente excepcion: " + res)
                    nombre_imagen = str(uuid.uuid3(uuid.NAMESPACE_URL, valor)) + ".png"
                    imagenes_extra.append((nombre_imagen, base64.b64decode(res)))
                    campos_extra[nombre_campo] = get_image_url(nombre_imagen)
                    # Nos guardamos en una lista el nombre de la imagen y la codificación para insertarla más tarde si no hay errores
                elif cod_campo == 0 or cod_campo == 4:
                    if type(valor) is not int:
                        abort(400, f"Tipo del campo {nombre_campo} incorrecto, los identificadores de las etiquetas son int pero se detectó {type(valor)}")
                    else:
                        etiqueta = db[campo_almacenado["coleccion"]].find_one({"_id": valor})
                        if etiqueta is None:
                            abort(400, f"No existe una etiqueta de {nombre_campo} con el identificador {valor}")

        for nombre_imagen, imagen in imagenes_extra:
            os.makedirs(IMAGES_DIR, exist_ok=True)
            with open(os.path.join(IMAGES_DIR, nombre_imagen), "wb") as f:
                f.write(imagen)

        doc.update(campos_extra)        

    db.Docs.insert_one(doc)

    return jsonify(success=True)

@app.route("/eliminar_imagen", methods=["POST"])
def eliminar_imagen():
    id = request.json["id"]
    _id = ObjectId(id)
    archivo = db.Docs.find_one({"_id": _id})
    nombre_imagen = re.search(r"[^/]+$", archivo["imagen_rgb"]).group()
    os.remove(os.path.join(IMAGES_DIR, nombre_imagen))
    db.Docs.delete_one({"_id": _id})

    return jsonify(True)




### USUARIOS ###

bd_usuarios = connect_to_database(db_name="appPlantas")
col_usuarios = bd_usuarios["usuarios"]

@app.route("/iniciar_sesion", methods=["POST"])
@limiter.limit("10 per minute")
def inicio_sesion():
    data = request.get_json(force=True)
    nombre = data.get("nombre")
    password = data.get("password")
    rol = data.get("rol")

    usuario = col_usuarios.find_one({"nombre": nombre})
    if not usuario:
        return jsonify({"success": False}), 401
    if not check_password(password, usuario.get("password", "")):
        return jsonify({"success": False}), 401
    if rol and rol not in usuario.get("rol", []):
        return jsonify({"success": False}), 403

    roles = usuario.get("rol", [])
    active_role = rol if rol else (roles[0] if roles else None)
    token = create_access_token(nombre, roles, active_role)

    return jsonify({
        "success": True,
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": JWT_EXP_MINUTES * 60,
        "usuario": {"nombre": nombre, "rol": roles},
        "active_role": active_role,
    })


@app.route("/registro", methods=["POST"]) 
@limiter.limit("10 per minute")
def registro():
    data = request.get_json(force=True)
    nombre = data.get("nombre")
    password = data.get("password")

    if not nombre or not password:
        return jsonify({"success": False, "error": "Faltan datos"}), 400

    # Comprobar si ya existe
    if col_usuarios.find_one({"nombre": nombre}):
        return jsonify({"success": False, "error": "El usuario ya existe"}), 409

    # Insertar nuevo usuario
    col_usuarios.insert_one({
        "nombre": nombre,
        "password": hash_password(password),
        "rol": ["usuario"],
        "nombres_antiguos": []
    })

    return jsonify({"success": True})

@app.route("/add_rol", methods=["POST"])
def add_rol():
    auth_error = require_any_role("admin")
    if auth_error:
        return auth_error

    data = request.get_json(force=True)
    nombre = data.get("nombre")
    rol = data.get("rol")

    if not nombre or not rol:
        return jsonify({"success": False, "error": "Faltan nombre o rol"}), 400

    usuario = col_usuarios.find_one({"nombre": nombre})
    if not usuario:
        return jsonify({"success": False, "error": "Usuario no encontrado"}), 404

    if rol in usuario.get("rol", []):
        return jsonify({"success": False, "error": f"El usuario ya tiene el rol '{rol}'"}), 409

    col_usuarios.update_one({"nombre": nombre}, {"$addToSet": {"rol": rol}})
    return jsonify({"success": True, "message": f"Rol '{rol}' añadido correctamente"})

@app.route("/eliminar_rol", methods=["POST"])
def eliminar_rol():
    auth_error = require_any_role("admin")
    if auth_error:
        return auth_error

    data = request.get_json(force=True)
    nombre = data.get("nombre")
    rol = data.get("rol")

    if not nombre or not rol:
        return jsonify({"success": False, "error": "Faltan nombre o rol"}), 400

    usuario = col_usuarios.find_one({"nombre": nombre})
    if not usuario:
        return jsonify({"success": False, "error": "Usuario no encontrado"}), 404

    if rol not in usuario.get("rol", []):
        return jsonify({"success": False, "error": f"El usuario no tiene el rol '{rol}'"}), 409

    col_usuarios.update_one({"nombre": nombre}, {"$pull": {"rol": rol}})
    return jsonify({"success": True, "message": f"Rol '{rol}' eliminado correctamente"})

# GET endpoint
@app.route("/buscar_usuarios", methods=["GET"]) 
#def buscar_usuarios(tipo_busqueda: str = None, nombre: str = None, rol: str = None):
#    query = {}

#    if tipo_busqueda and nombre:
#        query[tipo_busqueda] = {"$regex": nombre, "$options": "i"}  

def buscar_usuarios():
    auth_error = require_any_role("admin")
    if auth_error:
        return auth_error

    nombre = request.args.get("nombre")
    rol = request.args.get("rol")
    
    query = {}

    if nombre:
        query["nombre"] = {"$regex": nombre, "$options": "i"}
    if rol and rol.lower() != "todos":
        query["rol"] = {"$in": [rol]}  

    try:
        res = col_usuarios.find(query, {"_id": 0, "password": 0})
    except Exception as e:
        return {"error": str(e)}

    return list(res)

@app.route("/eliminar_usuario", methods=["POST"])
def eliminar_usuario():
    auth_error = require_any_role("admin")
    if auth_error:
        return auth_error

    data = request.get_json(force=True)
    nombre = data.get("nombre")

    query = {"nombre": nombre}

    try:
        res = col_usuarios.delete_one(query)
    except Exception as e:
        return jsonify(False)
    
    return jsonify(True)

@app.route("/cambiar_nombre_usuario", methods=["POST"]) 
def cambiar_nombre_usuario():
    data = request.get_json(force=True)
    nombre = data.get("nombre")
    nuevo_nombre = data.get("nuevo_nombre")
    password = data.get("password")
    nueva_password = data.get("nueva_password")

    auth_error = require_self_or_admin(nombre)
    if auth_error:
        return auth_error

    usuario = col_usuarios.find_one({"nombre": nombre})
    if not usuario or not check_password(password, usuario.get("password", "")):
        return jsonify({"success": False, "error": "Contraseña Incorrecta"}), 401

    if col_usuarios.find_one({"nombre": nuevo_nombre}):
        return jsonify({"success": False, "error": "Nombre de usuario ya en uso"}), 409

    col_usuarios.update_one(
        {"nombre": nombre},
        {"$set": {"nombre": nuevo_nombre, "password": hash_password(nueva_password)}, "$addToSet": {"nombres_antiguos": nombre}}
    )
    return jsonify({"success": True, "error": ""})

@app.route("/cambiar_password", methods=["POST"]) 
def cambiar_password():
    data = request.get_json(force=True)
    nombre = data.get("nombre")
    password = data.get("password")
    nueva_password = data.get("nueva_password")

    auth_error = require_self_or_admin(nombre)
    if auth_error:
        return auth_error

    usuario = col_usuarios.find_one({"nombre": nombre})
    if not usuario or not check_password(password, usuario.get("password", "")):
        return jsonify({"success": False, "error": "Contraseña Incorrecta"}), 401

    col_usuarios.update_one({"nombre": nombre}, {"$set": {"password": hash_password(nueva_password)}})
    return jsonify({"success": True, "error": ""})

@app.route("/seleccionar_usuario", methods=["POST"])
def seleccionar_usuario():
    data = request.get_json(force=True)
    nombre = data.get("nombre")

    auth_error = require_self_or_admin(nombre)
    if auth_error:
        return auth_error

    if not nombre:
        return jsonify({"success": False, "error": "Falta el nombre de usuario"}), 400

    usuario = col_usuarios.find_one({"nombre": nombre}, {"_id": 0})
    if not usuario:
        return jsonify({"success": False, "error": "Usuario no encontrado"}), 404
    return jsonify({"success": True, "usuario": usuario})

@app.route("/verificar_rol", methods=["POST"])
def verificar_rol():
    try:
        data = request.get_json(force=True)
        usuario = data.get("usuario")
        rol = data.get("rol")

        auth_error = require_self_or_admin(usuario)
        if auth_error:
            return auth_error

        if not usuario or not rol:
            return jsonify({"success": False, "error": "Faltan parámetros (usuario o rol)"}), 400

        # Consultar la base de datos
        user_data = col_usuarios.find_one({"nombre": usuario})
        if not user_data:
            return jsonify({"success": False, "error": "Usuario no encontrado"}), 404

        tiene_rol = rol in user_data.get("rol", [])
        return jsonify({"success": True, "tiene_rol": tiene_rol})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
@app.route("/logos", methods=["GET"])
def logos():
    try:
        ruta_logos = "./src/assets/logos.png"
        
        if not os.path.exists(ruta_logos):
            return jsonify({"success": False, "error": "Archivo de logos no encontrado"}), 404
        
        with open(ruta_logos, "rb") as f:
            imagen_bytes = f.read()
        
        imagen_b64 = base64.b64encode(imagen_bytes).decode("utf-8")
        
        return jsonify({"success": True, "imagen_b64": imagen_b64})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

# Usar run_server.py para ejecutar este servidor
# python run_server.py              # HTTP simple
# python run_server.py --https      # HTTPS (recomendado)
# python run_server.py --https --port 8000  # HTTPS en puerto 8000
