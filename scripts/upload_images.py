import os
import base64
import requests
import sys
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess
import json
from pathlib import Path
import urllib3

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_BASE_CANDIDATES = []
_api_env = os.getenv("API_BASE_URL", "").strip().rstrip("/")
if _api_env:
    API_BASE_CANDIDATES.append(_api_env)
API_BASE_CANDIDATES.extend(["https://localhost:5001", "http://localhost:5001"])

_dedup = []
for base in API_BASE_CANDIDATES:
    if base and base not in _dedup:
        _dedup.append(base)
API_BASE_CANDIDATES = _dedup

def request_api(method, path, **kwargs):
    last_exc = None
    for base in API_BASE_CANDIDATES:
        url = f"{base}{path}"
        request_kwargs = dict(kwargs)
        request_kwargs.setdefault("timeout", 30)
        if url.startswith("https://"):
            request_kwargs.setdefault("verify", False)
        # Añadir headers globales si existen (token de autenticación)
        headers = globals().get("_REQUEST_HEADERS", {}) or {}
        if "headers" in request_kwargs:
            merged = dict(headers)
            merged.update(request_kwargs["headers"])
            request_kwargs["headers"] = merged
        elif headers:
            request_kwargs["headers"] = dict(headers)
        try:
            return requests.request(method, url, **request_kwargs)
        except Exception as e:
            last_exc = e
            continue
    if last_exc:
        raise last_exc
    raise RuntimeError("No se pudo construir la URL de backend")

def carpeta_vacia_o_incompleta(path):
    if not os.path.isdir(path):
        return True
    for root, _, files in os.walk(path):
        if any(f.lower().endswith((".jpg", ".jpeg", ".png")) for f in files):
            return False  # hay al menos una imagen
    return True  # no se encontró ninguna

def procesar_fuente_si_falta(fuente):
    base_path = os.path.join("data", fuente)
    rutas = {
        "color": os.path.join(base_path, "color"),
        "grayscale": os.path.join(base_path, "grayscale"),
        "segmented": os.path.join(base_path, "segmented")
    }

    faltan = (
        carpeta_vacia_o_incompleta(rutas["grayscale"])
        or carpeta_vacia_o_incompleta(rutas["segmented"])
    )

    if faltan:
        print(f"Procesando imágenes para la fuente '{fuente}'...")
        try:
            subprocess.run(["python", "scripts/process_imported_images.py", "--fuente", fuente], check=True)
            print("Procesamiento de imágenes completado.")
        except subprocess.CalledProcessError as e:
            print(f"Error al procesar imágenes: {e}")
            sys.exit(1)


def _hash_for_login(usuario: str, password: str) -> str:
    # Misma función de hashing simple usada por la app cliente (logicav3.hash_func)
    cadena = usuario + "HOLAAAA" + password
    hash_res = ""
    for i in range(len(cadena)):
        c = ord(cadena[i]) * (i+1) * (i+1)
        hash_res += str(c)
    hash_res = hash_res.zfill(20)
    hash_res = hash_res[-20:]
    return hash_res


def perform_login(api_user: str, api_password: str, api_role: str | None = None):
    """Intenta iniciar sesión en la API y guarda el token global para futuras peticiones.
    Devuelve True si el login fue exitoso, False en caso contrario."""
    if not api_user or not api_password:
        return False
    login_payload = {"nombre": api_user, "password": _hash_for_login(api_user, api_password)}
    if api_role:
        login_payload["rol"] = api_role
    try:
        res = request_api("POST", "/iniciar_sesion", json=login_payload)
        res.raise_for_status()
        data = res.json()
        token = data.get("access_token")
        if token:
            globals()['_REQUEST_HEADERS'] = {"Authorization": f"Bearer {token}"}
            return True
    except Exception as e:
        print("Error iniciando sesion en API:", e)
    return False

# Función para obtener el ID de la fuente o crearla si no existe
def obtener_o_crear_id_fuente(nombre):
    try:
        res = request_api("GET", "/recuperar_etiquetas/Fuente")
        res.raise_for_status()
        etiquetas = res.json()
        for etq in etiquetas:
            if etq["fuente"] == nombre:
                return etq["_id"]
        
        # No existe, así que la creamos
        payload = {
            "coleccion": "Fuente",
            "etiqueta": {"fuente": nombre}
        }
        res = request_api("POST", "/add_etiqueta", json=payload)
        res.raise_for_status()
        return res.json()["etiqueta"]["_id"]
    except Exception as e:
        print("Error al registrar o recuperar la fuente:", e)
        sys.exit(1)


def subir_imagen(ruta_img, clase_id, formato_id, fuente, usuario):
    with open(ruta_img, "rb") as f:
        imagen_b64 = base64.b64encode(f.read()).decode("utf-8")
    
    payload = {
        "imagen_b64": imagen_b64,
        "clase": clase_id,
        "campos_extra": {
            "fuente": fuente,
            "formato": formato_id,
        },
        "usuario": usuario
    }

    try:
        res = request_api("POST", "/subir_imagen", json=payload)
        return ruta_img, res.status_code, res.text
    except Exception as e:
        return ruta_img, "ERROR", str(e)


# Argumentos
parser = argparse.ArgumentParser(description="Subida de imágenes a la base de datos")
parser.add_argument("formato", choices=["Color", "Grayscale", "Segmented"], help="Formato de imagen")
parser.add_argument("--fuente", default="PlantVillage", help="Fuente de las imágenes (carpeta dentro de data/)" )
parser.add_argument("--usuario", default="desconocido", help="Usuario que realiza la subida")
parser.add_argument("--start", type=int, default=0, help="Índice de inicio del batch (por clase o carpeta)")
parser.add_argument("--limit", type=int, default=None, help="Número máximo de imágenes a subir (por clase o carpeta)")
parser.add_argument("--no_auto_process", action="store_true", help="No procesar automáticamente si faltan carpetas")
parser.add_argument("--api-user", help="Usuario API para autenticación (o usa env API_USER)")
parser.add_argument("--api-password", help="Password API (texto plano) o usa env API_PASSWORD")
parser.add_argument("--api-role", help="Rol a usar en el login (opcional) o usa env API_ROLE")
args = parser.parse_args()

formato_nombre = args.formato
formato_ids = {"Color": 0, "Grayscale": 1, "Segmented": 2}
formato_id = formato_ids[formato_nombre]
if not args.no_auto_process:
    procesar_fuente_si_falta(args.fuente)
# Autenticación API:
# 1) Reutilizar token ya emitido (p. ej. enviado desde /subida_masiva en backend).
# 2) Si no hay token, hacer login con credenciales CLI/env.
bearer_token = (os.getenv("API_BEARER_TOKEN") or "").strip()
if bearer_token:
    globals()['_REQUEST_HEADERS'] = {"Authorization": f"Bearer {bearer_token}"}
else:
    api_user = args.api_user or os.getenv("API_USER")
    api_password = args.api_password or os.getenv("API_PASSWORD")
    api_role = args.api_role or os.getenv("API_ROLE")
    if api_user and api_password:
        ok = perform_login(api_user, api_password, api_role)
        if not ok:
            print("No se pudo autenticar en la API. Comprueba API_USER/API_PASSWORD/API_ROLE.")
            sys.exit(1)
    else:
        print("No se proporcionaron credenciales API ni API_BEARER_TOKEN.")
        print("Define --api-user/--api-password, API_USER/API_PASSWORD o API_BEARER_TOKEN.")
        sys.exit(1)

fuente_id = obtener_o_crear_id_fuente(args.fuente)


# Directorio base y log
DATASET_DIR = os.path.join(ROOT, "data", args.fuente, formato_nombre.lower())
LOG_PATH = os.path.join(ROOT, f"logs/upload_log_{formato_nombre}_{args.fuente}.txt")

if not os.path.isdir(DATASET_DIR):
    print(f"No existe el directorio de dataset: {DATASET_DIR}")
    sys.exit(1)

with open("src/clases.json", "r", encoding="utf-8") as f:
    clase_id_dict = json.load(f)

# Imágenes ya subidas
uploaded = set()
if os.path.exists(LOG_PATH):
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        uploaded = set(f.read().splitlines())

carpetas_detectadas = os.listdir(DATASET_DIR)
for carpeta in carpetas_detectadas:
    if carpeta not in clase_id_dict:
        print(f"Clase nueva detectada: {carpeta}. Ejecutando add_class.py")
        subprocess.run(["python", "scripts/add_class.py", carpeta], check=True)

with open("src/clases.json", "r", encoding="utf-8") as f:
    clase_id_dict = json.load(f)

# Generar tareas
tareas = []
start, limit = args.start, args.limit
for clase_nombre, clase_id in clase_id_dict.items():
    clase_dir = os.path.join(DATASET_DIR, clase_nombre)
    if not os.path.isdir(clase_dir):
        continue
    archivos = sorted([a for a in os.listdir(clase_dir) if a.lower().endswith((".jpg", ".jpeg", ".png"))])
    for archivo in archivos[start:(start+limit if limit else None)]:
        ruta_img = os.path.join(clase_dir, archivo)
        if ruta_img in uploaded:
            continue
        tareas.append((ruta_img, clase_id, formato_id, fuente_id, args.usuario))

# Subida concurrente
total = len(tareas)
print(f"Subiendo {total} imágenes en formato '{formato_nombre}'...")

start_time = time.perf_counter()
with ThreadPoolExecutor(max_workers=8) as executor, open(LOG_PATH, "a", encoding="utf-8") as logf:
    futures = {executor.submit(subir_imagen, *args): args[0] for args in tareas}
    for i, future in enumerate(as_completed(futures), 1):
        ruta_img, status, mensaje = future.result()
        if status == 200:
            logf.write(ruta_img + "\n")

        elapsed = time.perf_counter() - start_time
        avg_time = elapsed / i
        remaining = avg_time * (total - i)
        print(f"Progreso: {i}/{total} | Tiempo: {int(elapsed)}s | ETA: {int(remaining)}s")
