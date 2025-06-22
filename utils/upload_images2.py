import os
import base64
import requests
import sys
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# Argumentos
parser = argparse.ArgumentParser(description="Subida de imágenes a la base de datos")
parser.add_argument("formato", choices=["Color", "Grayscale", "Segmented"], help="Formato de imagen")
parser.add_argument("--fuente", default=None, help="Fuente de las imágenes (subcarpeta en data/importada)")
args = parser.parse_args()

formato_nombre = args.formato
formato_ids = {"Color": 0, "Grayscale": 1, "Segmented": 2}
formato_id = formato_ids[formato_nombre]

# Directorio base
if args.fuente:
    DATASET_DIR = os.path.join("data", "importada", args.fuente, formato_nombre.lower())
    LOG_PATH = f"upload_log_{formato_nombre}_{args.fuente}.txt"
else:
    DATASET_DIR = f"C:/Users/Pablo/Documents/Universidad/TFG/Repositorios/Repo/Data/PlantVillage/{formato_nombre}"
    LOG_PATH = f"upload_log_{formato_nombre}_PlantVillage.txt" 

# Tiene más sentido tener muchos archivos log o solo uno?

BACKEND_URL = "http://localhost:5000/subir_imagen"

clase_id_dict = {
    'Apple___Apple_scab': 0, 'Apple___Black_rot': 1, 'Apple___Cedar_apple_rust': 2, 'Apple___healthy': 3,
    'Blueberry___healthy': 4, 'Cherry_(including_sour)___healthy': 5, 'Cherry_(including_sour)___Powdery_mildew': 6,
    'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot': 7, 'Corn_(maize)___Common_rust_': 8,
    'Corn_(maize)___healthy': 9, 'Corn_(maize)___Northern_Leaf_Blight': 10, 'Grape___Black_rot': 11,
    'Grape___Esca_(Black_Measles)': 12, 'Grape___healthy': 13, 'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)': 14,
    'Orange___Haunglongbing_(Citrus_greening)': 15, 'Peach___Bacterial_spot': 16, 'Peach___healthy': 17,
    'Pepper,_bell___Bacterial_spot': 18, 'Pepper,_bell___healthy': 19, 'Potato___Early_blight': 20,
    'Potato___healthy': 21, 'Potato___Late_blight': 22, 'Raspberry___healthy': 23, 'Soybean___healthy': 24,
    'Squash___Powdery_mildew': 25, 'Strawberry___healthy': 26, 'Strawberry___Leaf_scorch': 27,
    'Tomato___Bacterial_spot': 28, 'Tomato___Early_blight': 29, 'Tomato___healthy': 30, 'Tomato___Late_blight': 31,
    'Tomato___Leaf_Mold': 32, 'Tomato___Septoria_leaf_spot': 33, 'Tomato___Spider_mites Two-spotted_spider_mite': 34,
    'Tomato___Target_Spot': 35, 'Tomato___Tomato_mosaic_virus': 36, 'Tomato___Tomato_Yellow_Leaf_Curl_Virus': 37
}

uploaded = set()
if os.path.exists(LOG_PATH):
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        uploaded = set(f.read().splitlines())

def subir_imagen(ruta_img, clase_id, formato_id):
    with open(ruta_img, "rb") as f:
        imagen_b64 = base64.b64encode(f.read()).decode("utf-8")
    payload = {
        "imagen_b64": imagen_b64,
        "clase": "003",
        "etiqueta": clase_id,
        "formato": formato_id
    }
    try:
        res = requests.post(BACKEND_URL, json=payload)
        return ruta_img, res.status_code, res.text
    except Exception as e:
        return ruta_img, "ERROR", str(e)

tareas = []
if args.fuente:
    for archivo in os.listdir(DATASET_DIR):
        ruta_img = os.path.join(DATASET_DIR, archivo)
        if ruta_img in uploaded or not archivo.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        tareas.append((ruta_img, "003", formato_id))  # Clase 003 = imagen
else:
    for clase_nombre, clase_id in clase_id_dict.items():
        clase_dir = os.path.join(DATASET_DIR, clase_nombre)
        if not os.path.isdir(clase_dir):
            continue
        for archivo in os.listdir(clase_dir):
            ruta_img = os.path.join(clase_dir, archivo)
            if ruta_img in uploaded or not archivo.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            tareas.append((ruta_img, clase_id, formato_id))

total = len(tareas)
print(f"🔄 Subiendo {total} imágenes en formato '{formato_nombre}'...")

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
        print(f"🕒 Progreso: {i}/{total} | Tiempo: {int(elapsed)}s | ETA: {int(remaining)}s")
