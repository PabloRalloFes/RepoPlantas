import base64
import io
from PIL import Image
from flask import Flask, request, jsonify, abort
import re
import os
from bson.objectid import ObjectId
from io import BytesIO
import uuid
from utils.model import build_model
from utils.database import load_yaml_config, connect_to_database
from torchvision import transforms
from PIL import Image
import torch
import pandas as pd
from pathlib import Path
import json
from datetime import datetime, timezone, timedelta
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

app = Flask(__name__)
db = connect_to_database(db_name="Repositorio_Plantas")  # por defecto usa "Repositorio_Plantas"

ROOT = os.path.dirname(os.path.abspath(__file__))

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
        with Image.open(BytesIO(imagen_bytes)) as imagen:
            imagen.load()  # Fuerza la carga completa
        return jsonify(True), imagen_bytes
    except Exception as e:
        return jsonify(False), str(e)
    
def guardar_como_png(imagen_bytes, ruta_salida):
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
    Endpoint para predecir planta y enfermedad a partir de una imagen base64.
    Requiere que el modelo y la configuración estén definidos en una carpeta de experimento.
    """
    try:
        data = request.get_json(force=True)
        image_b64 = data.get("imagen")
        modelo_seleccionado = data.get("modelo", None)
        known_planta = data.get("planta", None)

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
        data_path = os.path.join(experiment_path, "data")

        if not os.path.exists(modelo_path):
            return jsonify({"success": False, "error": f"El modelo '{modelo_seleccionado}' no existe"}), 404

        if not os.path.exists(experiment_path):
            return jsonify({"success": False, "error": f"El experimento '{experiment_path}' no existe"}), 404
        config = load_yaml_config(config_path)

        # Completar nombres de clases desde la base de datos si están en "all"
        if config["plantas"] == "all":
            config["plantas"] = sorted(db["Clases"].distinct("planta"))
        if config["enfermedades"] == "all":
            config["enfermedades"] = sorted(db["Clases"].distinct("nombre_comun"))

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

        # Inferencia
        with torch.no_grad():
            out_cultivo, out_enfermedad = model(tensor_img)
            probs_c = torch.softmax(out_cultivo, dim=1).squeeze()
            probs_e = torch.softmax(out_enfermedad, dim=1).squeeze()

            cultivo_to_idx = {c: i for i, c in enumerate(config["plantas"])}
            enfermedad_to_idx = {e: i for i, e in enumerate(config["enfermedades"])}
            idx_to_cultivo = {i: c for c, i in cultivo_to_idx.items()}
            idx_to_enfermedad = {i: e for e, i in enfermedad_to_idx.items()}

            if known_planta:
                if known_planta not in cultivo_to_idx:
                    return jsonify({"success": False, "error": f"La planta '{known_planta}' no está en el config."}), 400
                idx_cultivo = cultivo_to_idx[known_planta]
                cultivo_pred = known_planta
                prob_planta = 1.0  # La planta es conocida, por lo que su probabilidad es 100%
            else:
                idx_cultivo = probs_c.argmax().item()
                cultivo_pred = idx_to_cultivo[idx_cultivo]
                prob_planta = probs_c[idx_cultivo].item()

            # Filtrar enfermedades válidas para ese cultivo
            df_train = pd.read_csv(Path(data_path) / "train.csv")
            combinaciones_validas = set(zip(df_train["planta"], df_train["nombre_comun"]))
            enfermedades_validas = [e for (p, e) in combinaciones_validas if p == cultivo_pred]

            probs_filtradas = {e: probs_e[enfermedad_to_idx[e]].item() for e in enfermedades_validas}
            enfermedad_pred = max(probs_filtradas, key=probs_filtradas.get)
            prob_enfermedad = probs_filtradas[enfermedad_pred]

            # Calcular probabilidad conjunta si se proporciona known_planta
            probabilidad_final = prob_enfermedad * prob_planta if not known_planta else prob_enfermedad

        return jsonify({
            "success": True,
            "planta_predicha": cultivo_pred,
            "enfermedad_predicha": enfermedad_pred,
            "probabilidad": probabilidad_final
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
    
@app.route("/opciones_plantas", methods=["GET"])
def opciones_plantas():
    plantas = sorted(db.Clases.distinct("planta"))
    return jsonify(plantas)

@app.route("/opciones_enfermedades", methods=["GET"])
def opciones_enfermedades():
    enfermedades = sorted(db.Clases.distinct("nombre_comun"))
    return jsonify(enfermedades)

@app.route("/opciones_formatos", methods=["GET"])
def opciones_formatos():
    formatos = list(db.Formato.distinct("formato"))
    return jsonify_serialized(formatos)

@app.route("/opciones_fuentes", methods=["GET"])
def opciones_fuentes():
    fuentes = list(db.Fuente.distinct("fuente"))
    return jsonify_serialized(fuentes)

@app.route("/subida_masiva", methods=["POST"])
def subida_masiva():
    data = request.get_json(force=True)
    fuente = data.get("fuente")
    procesar = data.get("procesar", False)

    if not fuente:
        return jsonify({"success": False, "error": "Falta el nombre de la fuente"}), 400

    script_path = os.path.join(ROOT, "scripts", "subida_masiva_app.py")

    cmd = ["python", script_path, "--fuente", fuente]
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
                "error": "No se encontró la carpeta indicada en data/Imported/. Verifica el nombre y vuelve a intentarlo."
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

        if not nombre_experimento:
            return jsonify({"success": False, "error": "Falta el nombre del experimento"}), 400

        db["Entrenamientos"].insert_one({
            "nombre": nombre_experimento,
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
    """
    try:
        data = request.get_json()
        nombre_experimento = data.get("nombre")

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

        # Si el entrenamiento fue correcto, intentar eliminar el experimento de la colección Experimentos.
        try:
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
                    campos_extra[nombre_campo] = f"http://158.42.184.169:5001/imagen_base64/{nombre_imagen}"
                    # Nos guardamos en una lista el nombre de la imagen y la codificación para insertarla más tarde si no hay errores
                elif cod_campo == 0 or cod_campo == 4:
                    if type(valor) is not int:
                        abort(400, f"Tipo del campo {nombre_campo} incorrecto, los identificadores de las etiquetas son int pero se detectó {type(valor)}")
                    else:
                        etiqueta = db[campo_almacenado["coleccion"]].find_one({"_id": valor})
                        if etiqueta is None:
                            abort(400, f"No existe una etiqueta de {nombre_campo} con el identificador {valor}")

        for nombre_imagen, imagen in imagenes_extra:
            with open(f"./imagenes/{nombre_imagen}", "wb") as f:
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
        os.remove(f"./imagenes/" + nombre_imagen)
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
            res = db.Docs.find({"clase": etiqueta["_id"]},{})
        else:
            id_etiqueta = db.Etiquetas.find({"clasificacion": clasificacion}, {"_id": 1})
            res = []
            for etiqueta in id_etiqueta:
                res.append(db.Docs.find_one({"clase": etiqueta["_id"]},{}))
            res = filter(None, res)
    else:
        res = db.Docs.find()

    return list(res)

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
    imagen = Image.open(f"./imagenes/{nombre_imagen}", mode='r')
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
        formato_doc = db.Formato.find_one({"nombre": formato})
        if formato_doc:
            filtros["formato"] = formato_doc["_id"]

    if fuente:
        fuente_doc = db.Fuente.find_one({"nombre": fuente})
        if fuente_doc:
            filtros["fuente"] = fuente_doc["_id"]

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
        formato_doc = db.Formato.find_one({"nombre": formato})
        if formato_doc:
            filtros["formato"] = formato_doc["_id"]

    if fuente:
        fuente_doc = db.Fuente.find_one({"nombre": fuente})
        if fuente_doc:
            filtros["fuente"] = fuente_doc["_id"]

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

    if os.path.isfile(f"C:/Users/Pablo/Documents/Universidad/TFG/Repositorios/Repo/imagenes/{nombre_imagen}"):
        db.Docs.delete_one({"imagen_rgb": f"http://127.0.0.1:5001/imagen_base64/{nombre_imagen}"})

    guardar_como_png(imagen_bytes=res, ruta_salida=f"C:/Users/Pablo/Documents/Universidad/TFG/Repositorios/Repo/imagenes/{nombre_imagen}")

    doc = {
        "imagen_rgb": f"http://127.0.0.1:5001/imagen_base64/{nombre_imagen}",
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
                    campos_extra[nombre_campo] = f"http://127.0.0.1:5001/imagen_base64/{nombre_imagen}"
                    # Nos guardamos en una lista el nombre de la imagen y la codificación para insertarla más tarde si no hay errores
                elif cod_campo == 0 or cod_campo == 4:
                    if type(valor) is not int:
                        abort(400, f"Tipo del campo {nombre_campo} incorrecto, los identificadores de las etiquetas son int pero se detectó {type(valor)}")
                    else:
                        etiqueta = db[campo_almacenado["coleccion"]].find_one({"_id": valor})
                        if etiqueta is None:
                            abort(400, f"No existe una etiqueta de {nombre_campo} con el identificador {valor}")

        for nombre_imagen, imagen in imagenes_extra:
            with open(f"./imagenes/{nombre_imagen}", "wb") as f:
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
    os.remove(f"./imagenes/" + nombre_imagen)
    db.Docs.delete_one({"_id": _id})

    return jsonify(True)




### USUARIOS ###

bd_usuarios = connect_to_database(db_name="appPlantas")
col_usuarios = bd_usuarios["usuarios"]

@app.route("/iniciar_sesion", methods=["POST"])
def inicio_sesion():
    data = request.get_json(force=True)
    nombre = data.get("nombre")
    password = data.get("password")
    rol = data.get("rol")

    query = {"nombre": nombre, "password": password, "rol": rol}

    res = list(col_usuarios.find(query))

    return jsonify(True) if len(res) == 1 else jsonify(False)


@app.route("/registro", methods=["POST"]) 
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
        "password": password,
        "rol": ["usuario"],
        "nombres_antiguos": [],
        "contenido": []
    })

    return jsonify({"success": True})

@app.route("/add_rol", methods=["POST"])
def add_rol():
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

    res = col_usuarios.find({"nombre": nombre, "password": password})
    if len(list(res)) != 1:
        return (False, "Contraseña Incorrecta")

    res = col_usuarios.find({"nombre": nuevo_nombre})
    if len(list(res)) == 1:
        return(False, "Nombre de usuario ya en uso")
    
    col_usuarios.update_one({"nombre": nombre},{"$set": {"nombre": nuevo_nombre, "password": nueva_password}, "$addToSet":{"nombres_antiguos": nombre}})
    
    return jsonify({"success": True, "error": ""})

@app.route("/cambiar_password", methods=["POST"]) 
def cambiar_password():
    data = request.get_json(force=True)
    nombre = data.get("nombre")
    password = data.get("password")
    nueva_password = data.get("nueva_password")

    res = col_usuarios.find({"nombre": nombre, "password": password})
    if len(list(res)) != 1:
        return (False, "Contraseña Incorrecta")
    
    col_usuarios.update_one({"nombre": nombre}, {"$set": {"password": nueva_password}})
    
    return jsonify({"success": True, "error": ""})

@app.route("/seleccionar_usuario", methods=["POST"])
def seleccionar_usuario():
    data = request.get_json(force=True)
    nombre = data.get("nombre")

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
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
"""
@app.route("/test", methods=["GET"])
def test():
    print(db.Etiquetas.find_one({"clasificacion": "Sin_clasificar"}, {"_id": 1})["_id"])

    return ""
"""

if __name__ == "__main__":
    app.run(debug=True)
