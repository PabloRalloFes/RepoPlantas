import numpy
import base64
import io
from PIL import Image
from flask_pymongo import PyMongo
from flask import Flask, request
import time
from bson.objectid import ObjectId

app = Flask(__name__)

app.config["MONGO_URI"] = "mongodb://localhost:27017/Repositorio_Plantas"
mongo = PyMongo(app)


@app.route("/etiquetas", methods=["GET"])
def devolver_etiquetas():
    res = mongo.db.Etiquetas.find()
    return list(res)

@app.route("/variedades", methods=["GET"])
def devolver_variedades():
    res = mongo.db.Variedades.find()
    return list(res)

@app.route("/docs", methods=["GET"])
def devolver_docs():
    clasificacion = request.args.get('clasificacion', None)
    nombre = request.args.get('nombre', None)

    res = None
    if clasificacion is not None:
        if nombre is not None:
            etiqueta = mongo.db.Etiquetas.find_one({"clasificacion": clasificacion, "nombre": nombre}, {"_id": 1})
            res = mongo.db.Docs.find({"clase": etiqueta["_id"]},{})
        else:
            id_etiqueta = mongo.db.Etiquetas.find({"clasificacion": clasificacion}, {"_id": 1})
            res = []
            for etiqueta in id_etiqueta:
                res.append(mongo.db.Docs.find_one({"clase": etiqueta["_id"]},{}))
            res = filter(None, res)
    else:
        res = mongo.db.Docs.find()

    return list(res)

@app.route("/clasificar", methods=["POST"])
def etiquetar_doc():
    id_etiqueta = request.json["etiqueta"]
    id_doc = request.json["doc"]

    mongo.db.Docs.update_one({"_id": id_doc}, {"$set": {"clase": id_etiqueta}})

    return "True"

@app.route("/imagen_base64/<nombre_imagen>", methods=["GET"])
def devolver_imagen_base64(nombre_imagen):
    imagen = Image.open(f"./imagenes/{nombre_imagen}", mode='r')
    bytes_array = io.BytesIO()
    imagen.save(bytes_array, format=imagen.format)
    #bytes_array = bytes_array.getvalue()
    b64_image = base64.b64encode(bytes_array.getvalue())
    return b64_image

@app.route("/servir_n_archivos", methods=["GET"])
def devolver_x_archivos():
    inicio = request.args.get('inicio', None, type=int)
    n_archivos = request.args.get('n_archivos', None, type=int)

    if inicio == None or n_archivos == None:
        return []
    
    res = mongo.db.Docs.find().skip(inicio).limit(n_archivos)

    return list(res)

@app.route("/servir_n_archivos_sin_validar", methods=["GET"])
def devolver_x_archivos_sin_validar():
    inicio = request.args.get('inicio', None, type=int)
    n_archivos = request.args.get('n_archivos', None, type=int)

    if inicio == None or n_archivos == None:
        return []
    
    res = mongo.db.Docs.find({"validada": 0},{}).skip(inicio).limit(n_archivos)

    return list(res)

@app.route("/subir_imagen", methods=["POST"])
def subir_imagen():
    imagen_b64 = request.json["imagen_b64"]
    imagen = base64.b64decode(imagen_b64)

    clase = int(request.json["clase"])

    # PARA LA VERSION FINAL AÑADIR %f DESPUÉS DE LOS SEGUNDOS
    nombre_imagen = time.strftime("%H-%M-%S_%m_%d_%Y", time.localtime()) + ".png"

    with open(f"./imagenes/{nombre_imagen}", "wb") as f:
        f.write(imagen)

    doc = {
        "imagen_rgb": f"http://158.42.184.169:5001/imagen_base64/{nombre_imagen}",
        "validada": 0,
        "clase": clase
    }

    mongo.db.Docs.insert_one(doc)

    return "True"
"""
@app.route("/test", methods=["GET"])
def test():
    print(mongo.db.Etiquetas.find_one({"clasificacion": "Sin_clasificar"}, {"_id": 1})["_id"])

    return ""
"""