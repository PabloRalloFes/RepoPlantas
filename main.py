import base64
import io
from PIL import Image
from flask_pymongo import PyMongo
from flask import Flask, request, jsonify, abort
import re
import os
from bson.objectid import ObjectId
from io import BytesIO
import uuid

app = Flask(__name__)

app.config["MONGO_URI"] = "mongodb://localhost:27017/Repositorio_Plantas"
mongo = PyMongo(app)

def validar_imagen_base64(cadena_base64):
    try:
        imagen_bytes = base64.b64decode(cadena_base64)
        imagen = Image.open(BytesIO(imagen_bytes))
        imagen.verify()
        return True, imagen_bytes
    except Exception as e:
        return False, str(e)

@app.route("/recuperar_campos", methods=["GET"])
def recuperar_campos():
    res = mongo.db.Campos.find()
    return jsonify(res)

@app.route("/recuperar_etiquetas/<nombre_coleccion>", methods=["GET"])
def devolver_etiquetas(nombre_coleccion):
    if nombre_coleccion not in mongo.db.list_collection_names():
        abort(400, description="El nombre de la coleccion no es correcto")
    coleccion = mongo.db[nombre_coleccion]
    res = coleccion.find()
    return jsonify(res)

@app.route("/add_etiqueta", methods=["POST"])
def add_etiqueta():
    nombre_coleccion = request.json["nombre_coleccion"]
    etiqueta = request.json.get("etiqueta")

    campos_etiqueta = mongo.db.Campos.find_one({"coleccion": nombre_coleccion})
    if campos_etiqueta is None:
        return abort(400, description=f"No se ha encontrado ningun campo con el nombre {nombre_coleccion}")
    else:
        campos_etiqueta = campos_etiqueta["campos_etiqueta"]
        if sorted(etiqueta.keys()) != sorted(campos_etiqueta):
            return abort(400, description=f"Los campos de la etiqueta proporcionada no son correctos")

    coleccion = mongo.db[nombre_coleccion]
    ultimo = coleccion.find_one(sort=[('_id', -1)])
    nuevo_id = (ultimo['_id'] + 1) if ultimo else 0

    etiqueta["_id"] = nuevo_id

    coleccion.insert_one(etiqueta)

    return jsonify(success=True)

@app.route("/modificar_etiqueta", methods=["POST"])
def modificar_etiqueta():
    nombre_coleccion = request.json["nombre_coleccion"]
    etiqueta = request.json.get("etiqueta")

    if type(etiqueta) != dict:
        abort(400, description="El formato de la etiqueta es incorecto")

    campos_etiqueta = mongo.db.Campos.find_one({"coleccion": nombre_coleccion})
    if campos_etiqueta is None:
        return abort(400, description=f"No se ha encontrado ningun campo con el nombre {nombre_coleccion}")
    else:
        campos_etiqueta = campos_etiqueta["campos_etiqueta"]
        if sorted(etiqueta.keys()) != sorted(campos_etiqueta.append("_id")):
            return abort(400, description=f"Los campos de la etiqueta proporcionada no son correctos")


    coleccion = mongo.db[nombre_coleccion]

    coleccion.replace_one({"_id": etiqueta["_id"]}, etiqueta, upsert=False)

    return jsonify(success=True)

@app.route("/devolver_campos_etiqueta/<nombre_campo>", methods=["GET"])
def devolver_campos(nombre_campo):
    campos_etiqueta = mongo.db.Campos.find_one({"nombre": nombre_campo},{"campos_etiqueta": 1})
    if campos_etiqueta is None:
        return abort(400, description=f"No se ha encontrado ningun campo con el nombre {nombre_campo}")
    return jsonify(campos_etiqueta["campos_etiqueta"])

@app.route("/add_campo", methods=["POST"])
def add_campo():
    nombre = request.json["nombre"]
    cod = int(request.json["cod"])

    campo = {
        "nombre": nombre,
        "cod": cod
    }

    if cod == 4:
        # Este es un diccionario que tiene como clave el nombre del campo y como valor su tipo esperado en formato texto (str, bool o int, no se admiten más)
        campos_etiqueta = request.json.get("campos_etiqueta")
        if campos_etiqueta is None:
            abort(400, "Falta por especificar los campos de la etiqueta")
        else:
            for nombre_campo in campos_etiqueta:
                if campos_etiqueta[nombre_campo] not in ["str", "bool", "int"]:
                    abort(400, f"El campo {nombre_campo} tiene un tipo no admitido, solo se admiten valores 'str', 'bool' o 'int'")
        campo["campos_etiqueta"] = campos_etiqueta
        
    mongo.db.Campos.insert_one(campo)

    jsonify(success=True)

@app.route("/eliminar_campo", methods=["POST"])
def eliminar_campo():
    nombre = request.json["nombre"]
    campo = mongo.db.Campos.find_one({"nombre": nombre})
    cod = int(campo["cod"])

    if cod == 0:
        return abort(400, "No se puede eliminar este campo")
    elif mongo.db.Docs.find_one({nombre: {"$exists": True}}) is None:
        mongo.db.Campos.delete_one({"nombre": nombre})
        return jsonify(success=True)
    else:
        return abort(400, "No se puede eliminar este campo porque hay al menos una imagen que lo posee")
    
@app.route("/add_dato", methods=["POST"])
def add_dato():
    # _id = ObjectId(request.json["id"])
    # nombre_campo = request.json["nombre_campo"]
    # valor = request.json["valor"]
    # cod = int(mongo.db.Campos.find_one({"nombre": nombre_campo})["cod"])

    # if cod != 3:
    #     mongo.db.Docs.update_one({"_id": _id}, {"$set": {f"{nombre_campo}": valor}})
    #     return jsonify(success=True)
    # if cod == 3:
    #     imagen = base64.b64decode(valor)

    #     nombre_imagen = time.strftime("%H-%M-%S-%f_%m_%d_%Y", time.localtime()) + ".png"

    #     with open(f"./imagenes/{nombre_imagen}", "wb") as f:
    #         f.write(imagen)

    #     uri_imagen = f"http://158.42.184.169:5001/imagen_base64/{nombre_imagen}",

    #     mongo.db.Docs.update_one({"_id": _id}, {"$set": {f"{nombre_campo}": uri_imagen}})
    #     return jsonify(success=True)
    _id = ObjectId(request.json["id"])
    campos_extra = request.json.get("campos_extra")
    if campos_extra is not None:
        imagenes_extra = []
        for nombre_campo in campos_extra:
            valor = campos_extra[nombre_campo]
            campo_almacenado = mongo.db.Campos.find_one({"nombre": nombre_campo})
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
                        etiqueta = mongo.db[campo_almacenado["coleccion"]].find_one({"_id": valor})
                        if etiqueta is None:
                            abort(400, f"No existe una etiqueta de {nombre_campo} con el identificador {valor}")

        for nombre_imagen, imagen in imagenes_extra:
            with open(f"./imagenes/{nombre_imagen}", "wb") as f:
                f.write(imagen)

    mongo.db.Docs.update_one({"_id": _id}, {"$set": campos_extra})
    return jsonify(success=True)

@app.route("/eliminar_dato", methods=["POST"])
def eliminar_dato():
    _id = ObjectId(request.json["id"])
    nombre_campo = request.json["nombre_campo"]
    cod = int(mongo.db.Campos.find_one({"nombre": nombre_campo})["cod"])

    if cod != 3:
        mongo.db.Docs.update_one({"_id": _id}, {"$unset": {f"{nombre_campo}": ""}})
        return jsonify(success=True)
    if cod == 3:
        archivo = mongo.Docs.find_one({"_id": _id})
        nombre_imagen = re.search(r"[^/]+$", archivo[f"{nombre_campo}"]).group()
        os.remove(f"./imagenes/" + nombre_imagen)
        mongo.db.Docs.update_one({"_id": _id}, {"$unset": {f"{nombre_campo}": ""}})

        return jsonify(success=True)


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
    correcto, res = validar_imagen_base64(request.json["imagen_b64"])
    if not correcto:
        abort(400, f"La imagen principal ha provocado la siguiente excepcion: " + res)
    imagen = base64.b64decode(res)

    clase = int(request.json["clase"])

    nombre_imagen = str(uuid.uuid3(uuid.NAMESPACE_URL, res)) + ".png"

    with open(f"./imagenes/{nombre_imagen}", "wb") as f:
        f.write(imagen)

    doc = {
        "imagen_rgb": f"http://158.42.184.169:5001/imagen_base64/{nombre_imagen}",
        "validada": 0,
        "clase": clase
    }

    campos_extra = request.json.get("campos_extra")
    if campos_extra is not None:
        imagenes_extra = []
        for nombre_campo in campos_extra:
            valor = campos_extra[nombre_campo]
            campo_almacenado = mongo.db.Campos.find_one({"nombre": nombre_campo})
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
                        etiqueta = mongo.db[campo_almacenado["coleccion"]].find_one({"_id": valor})
                        if etiqueta is None:
                            abort(400, f"No existe una etiqueta de {nombre_campo} con el identificador {valor}")

        for nombre_imagen, imagen in imagenes_extra:
            with open(f"./imagenes/{nombre_imagen}", "wb") as f:
                f.write(imagen)

    doc.update(campos_extra)        

    mongo.db.Docs.insert_one(doc)

    return jsonify(success=True)

@app.route("/eliminar_imagen", methods=["POST"])
def eliminar_imagen():
    id = request.json["id"]
    _id = ObjectId(id)
    archivo = mongo.Docs.find_one({"_id": _id})
    nombre_imagen = re.search(r"[^/]+$", archivo["imagen_rgb"]).group()
    os.remove(f"./imagenes/" + nombre_imagen)
    mongo.db.Docs.delete_one({"_id": _id})

    return "True"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
"""
@app.route("/test", methods=["GET"])
def test():
    print(mongo.db.Etiquetas.find_one({"clasificacion": "Sin_clasificar"}, {"_id": 1})["_id"])

    return ""
"""