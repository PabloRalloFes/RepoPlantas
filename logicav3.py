import urllib.parse
import httpx
import urllib
import base64
import os
from urllib.parse import urlparse

URL_API="http://localhost:5001"
URL_BBDD="mongodb://localhost:27017"

class LogicaApp:
    
    ### NUEVOS ###

    def predecir_imagen(self, modelo_seleccionado, known_planta=None):
        url_predict = self.crear_url("/predict_image", self.url_api)
        payload = {
            "imagen": self.foto_b64, 
            "modelo": modelo_seleccionado,
            "planta": known_planta,
        }
        res = httpx.post(url_predict, json=payload)
        return res.json()
    
    def validar_imagen(self, id_doc):
        if isinstance(id_doc, dict) and "$oid" in id_doc:
            id_doc = id_doc["$oid"]

        url_validar = self.crear_url("/validar_imagen", self.url_api)
        res = httpx.post(url_validar, json={"id_doc": str(id_doc)})

        try:
            return res.json()
        except Exception:
            return {"success": False, "error": f"Respuesta no válida: {res.text}"}

    def obtener_opciones_plantas(self):
        url = self.crear_url("/opciones_plantas", self.url_api)
        res = httpx.get(url)
        return res.json()

    def obtener_opciones_enfermedades(self):
        url = self.crear_url("/opciones_enfermedades", self.url_api)
        res = httpx.get(url)
        return res.json()

    def obtener_opciones_formatos(self):
        url = self.crear_url("/opciones_formatos", self.url_api)
        res = httpx.get(url)
        return res.json()

    def obtener_opciones_fuentes(self):
        url = self.crear_url("/opciones_fuentes", self.url_api)
        res = httpx.get(url)
        return res.json()
    
    def set_url_api(self, nueva_url: str):
        if not nueva_url.startswith("http://") and not nueva_url.startswith("https://"):
            nueva_url = "http://" + nueva_url
        self.url_api = nueva_url.rstrip("/")
        return {"success": True, "message": f"URL de la API actualizada a {self.url_api}"}
    
    def set_url_bbdd(self, nueva_url: str):
        if not nueva_url.startswith("mongodb://") and not nueva_url.startswith("mongodb+srv://"):
            nueva_url = "mongodb://" + nueva_url
        self.url_bbdd = nueva_url.rstrip("/")
        return {"success": True, "message": f"URL de la base de datos actualizada a {self.url_bbdd}"}

    def obtener_clases(self):
        url = self.crear_url("/editar_clases", self.url_api)
        res = httpx.get(url)
        return res.json()

    def reemplazar_clases(self, clases_modificadas):
        url = self.crear_url("/reemplazar_clases", self.url_api)
        res = httpx.post(url, json={"clases": clases_modificadas})
        return res.json()
    
    def agregar_clase(self, clase_dict):
        url = self.crear_url("/add_class", self.url_api)
        res = httpx.post(url, json=clase_dict)
        return res.json()


    def crear_experimento(self, experiment_name, config_variables):
        """
        Llama al backend para crear un nuevo experimento.
        """
        url = self.crear_url("/crear_experimento", self.url_api)
        payload = {
            "experiment_name": experiment_name,
            "config_variables": config_variables,
        }

        if config_variables.get("imagenes_por_clase") == "Todas":
            payload["config_variables"]["imagenes_por_clase"] = "all"

        response = httpx.post(url, json=payload)
        return response.json()

    def obtener_experimentos(self):
        """
        Llama al backend para obtener la lista de experimentos actuales.
        """
        url = self.crear_url("/obtener_experimentos", self.url_api)
        response = httpx.get(url)
        return response.json().get("experimentos", [])
    
    def solicitar_entrenamiento(self, nombre_experimento):
        """
        Envía una solicitud al backend para registrar la petición de entrenamiento de un modelo.
        """
        url = self.crear_url("/solicitar_entrenamiento", self.url_api)
        payload = {"nombre": nombre_experimento}
        response = httpx.post(url, json=payload)
        return response.json()
    
    def obtener_solicitudes_entrenamiento(self):
        """
        Llama al backend para obtener la lista de solicitudes de entrenamiento.
        """
        url = self.crear_url("/obtener_solicitudes_entrenamiento", self.url_api)
        response = httpx.get(url)
        return response.json().get("solicitudes", [])
    
    def entrenar_modelo(self, nombre_experimento):
        """
        Llama al backend para ejecutar el entrenamiento de un modelo.
        """
        url = self.crear_url("/entrenar_modelo", self.url_api)
        payload = {"nombre": nombre_experimento}
        response = httpx.post(url, json=payload, timeout=3600)
        return response.json()
    
    def obtener_modelos(self):
        """
        Llama al backend para obtener la lista de modelos disponibles.
        """
        url = self.crear_url("/obtener_modelos", self.url_api)
        response = httpx.get(url)
        if response.status_code == 200:
            return response.json().get("modelos", [])
        else:
            return []
        
    def cambiar_url_bbdd(self):
        """
        Llama al backend para cambiar la URL de la base de datos.
        """
        url = self.crear_url("/cambiar_url_bbdd", self.url_api)
        payload = {"url_bbdd": self.url_bbdd}
        try:
            response = httpx.post(url, json=payload)
            if response.status_code == 200:
                return {"success": True, "message": "URL de la base de datos actualizada correctamente en el backend"}
            else:
                return {"success": False, "message": response.json().get("message", "Error desconocido")}
        except Exception as e:
            return {"success": False, "message": f"Error al conectar con el backend: {str(e)}"}
        
    def obtener_resultados_experimento(self, nombre_experimento):
        """
        Llama al backend para obtener los resultados de un experimento.
        """
        url = self.crear_url("/obtener_resultados_experimento", self.url_api)
        try:
            response = httpx.get(url, params={"nombre_experimento": nombre_experimento})
            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": response.json().get("error", "Error desconocido")}
        except Exception as e:
            return {"success": False, "error": f"Error al conectar con el backend: {str(e)}"}
        
    def get_url_imagen_resultado(self, nombre_experimento, archivo):
            """
            Devuelve la URL absoluta para obtener la imagen de resultados de un experimento.
            """
            params = {"experimento": nombre_experimento, "archivo": archivo}
            return self.crear_url("/imagen_resultado", self.url_api, params)
    
    def get_url_imagen_comparacion(self, ruta):
            """
            Devuelve la URL absoluta para obtener la imagen de resultados de una comparación de experimentos.
            """
            params = {"ruta": ruta}
            return self.crear_url("/imagen_comparacion", self.url_api, params)
        
    def comparar_experimentos(self, experimentos):
        """
        Llama al backend para comparar experimentos y obtener los gráficos generados.
        """
        url = self.crear_url("/comparar_experimentos", self.url_api)
        try:
            response = httpx.post(url, json={"experimentos": experimentos})
            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": response.json().get("error", "Error desconocido")}
        except Exception as e:
            return {"success": False, "error": f"Error al conectar con el backend: {str(e)}"}
    
    def obtener_graficos_comparacion(self, experimentos):
        """
        Llama al backend para obtener las rutas de los gráficos comparativos de los experimentos seleccionados.
        """
        url = self.crear_url("/obtener_graficos_comparacion", self.url_api)
        try:
            response = httpx.get(url, params={"experimentos": experimentos})
            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": response.json().get("error", "Error desconocido")}
        except Exception as e:
            return {"success": False, "error": f"Error al conectar con el backend: {str(e)}"}
        
    def verificar_rol(self, rol):
        """
        Verifica si el usuario actual tiene un rol específico consultando el backend.
        """
        url = self.crear_url("/verificar_rol", self.url_api)
        payload = {"usuario": self.usuario["nombre"], "rol": rol}

        try:
            response = httpx.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                return data.get("tiene_rol", False)
            else:
                return False
        except Exception as e:
            print(f"Error al verificar el rol: {e}")
            return False
    
    ### FIN NUEVOS ###


    def crear_url(self, path, url, params={}):

        partes_url = list(urllib.parse.urlparse(url))
        partes_url[2] = path
        partes_url[4] = urllib.parse.urlencode(params)
        return urllib.parse.urlunparse(partes_url)

    def hash_func(self, usuario: str, password: str):
        '''
        cadena = usuario + "HOLAAAA" + password
        
        return str(abs(hash(cadena)))
        '''
        cadena = usuario + "HOLAAAA" + password
        hash_res = ""

        for i in range(len(cadena)):
            c = ord(cadena[i]) * (i+1) * (i+1)
            hash_res += str(c)
        hash_res = hash_res.zfill(20)
        hash_res = hash_res[-20:]
        return hash_res

    def inicio_sesion(self, nombre: str, password: str, rol: str):
        if nombre == "" or password == "" or rol == None:
            return False
        
        params = {"nombre": nombre, "password": self.hash_func(nombre, password), "rol": rol}
        url_inciar_sesion = self.crear_url("/iniciar_sesion", self.url_api)

        respuesta = httpx.post(url_inciar_sesion, json=params, headers=self.headers)
       
        inicio_correcto = respuesta.json()

        if inicio_correcto:
            self.usuario["nombre"] = nombre
            return True
        else:
            return False


    def registro(self, nombre: str, password: str):
        
        params = {"nombre": nombre, "password": self.hash_func(nombre, password)}
        url_registro = self.crear_url("/registro", self.url_api)

        try:
            respuesta = httpx.post(url_registro, json=params, headers=self.headers)
            data = respuesta.json()
            return data
        except Exception:
            return {"success": False, "error": f"Error en la conexión ({respuesta.status_code})"}

    def add_rol(self, nombre: str, rol: str):

        params = {"nombre": nombre, "rol": rol}
        url_add_rol = self.crear_url("/add_rol", self.url_api)

        respuesta = httpx.post(url_add_rol, json=params, headers=self.headers)

        operacion_correcta = respuesta.json()

        if operacion_correcta:
            self.usuario_seleccionado[f"rol_{rol}"] = 1
            return operacion_correcta
        else:
            return operacion_correcta

    def eliminar_rol(self, nombre: str, rol: str):

        params = {"nombre": nombre, "rol": rol}
        url_eliminar_rol = self.crear_url("/eliminar_rol", self.url_api)

        respuesta = httpx.post(url_eliminar_rol, json=params, headers=self.headers)

        operacion_correcta = respuesta.json()

        if operacion_correcta:
            self.usuario_seleccionado[f"rol_{rol}"] = 0
            return operacion_correcta
        else:
            return operacion_correcta

    def buscar_usuarios(self, nombre: str = None, rol: str= None):
        self.busqueda_anterior = lambda : self.buscar_usuarios(nombre, rol)
        #params = {"tipo_busqueda": None, "nombre": None, "rol": None}
        params = {"nombre": None, "rol": None}
        if nombre is not None and nombre != "":
            params.update({"nombre": nombre})
        if rol is not None:
            params.update({"rol":rol})
        
        url_lista_usuarios = self.crear_url("/buscar_usuarios", self.url_api)

        respuesta = httpx.get(url_lista_usuarios, params=params, headers=self.headers)

        self.lista_usuarios = respuesta.json()
        return True
        
    def seleccionar_usuario(self, nombre: str):
        params = {"nombre": nombre}
        url_seleccionar_usuario = self.crear_url("/seleccionar_usuario", self.url_api)

        respuesta = httpx.post(url_seleccionar_usuario, json=params, headers=self.headers)

        try:
            data = respuesta.json()
        except Exception:
            self.usuario_seleccionado = {}
        else:
            self.usuario_seleccionado = data.get("usuario", {})
        return True
    
    def eliminar_usuario(self, usuario: dict):

        params = {"nombre": usuario["nombre"]}

        url_eliminar_usuario = self.crear_url("/eliminar_usuario", self.url_api)

        respuesta = httpx.post(url_eliminar_usuario, json=params, headers=self.headers)

        return respuesta.json()
    
    def cambiar_nombre_usuario(self, nuevo_nombre: str, password: str):
        if nuevo_nombre == "" or password == "":
            return False, "Faltan por introducir datos"

        params = {"nombre": self.usuario["nombre"], "nuevo_nombre": nuevo_nombre, "password": self.hash_func(self.usuario["nombre"], password), "nueva_password": self.hash_func(nuevo_nombre, password)}

        url_cambiar_nombre_usuario = self.crear_url("/cambiar_nombre_usuario", self.url_api)

        respuesta = httpx.post(url_cambiar_nombre_usuario, json=params, headers=self.headers)
        
        cambio_correcto = respuesta.json()
        
        if cambio_correcto:
            self.usuario["nombre"] = nuevo_nombre
            return True, "Se ha cambiado el nombre de usuario"
        else:
            return False, "No se ha podido cambiar el nombre de usuario"
        
    
    def cambiar_password(self, nueva_password: str, nueva_password_repetida: str, password: str):
        if password == "" or nueva_password_repetida == "" or nueva_password == "":
            return False, "Faltan introducir datos"
        
        if nueva_password != nueva_password_repetida:
            return False, "Las contraseñas no coinciden"
        
        params = {"nombre": self.usuario["nombre"], "password": self.hash_func(self.usuario["nombre"], password), "nueva_password": self.hash_func(self.usuario["nombre"], nueva_password)}

        url_cambiar_password = self.crear_url("/cambiar_password", self.url_api)

        respuesta = httpx.post(url_cambiar_password, json=params, headers=self.headers)
        
        cambio_correcto = respuesta.json()

        if cambio_correcto:
            return True, "Se ha cambiado la contraseña"
        else:
            return False, "Contraseña actual introducida incorrecta"
        
    def recuperar_etiquetas(self):

        url_recuperar_etiquetas = self.crear_url("/etiquetas", self.url_api)

        respuesta = httpx.get(url_recuperar_etiquetas)

        return respuesta.json()
    
    def recuperar_docs(self, clasificacion = "", nombre = ""):

        url_recuperar_docs = self.crear_url("/docs", self.url_api)

        params = {}
        if clasificacion != "":
            params.update({"clasificacion": clasificacion})
            if nombre != "":
                params.update({"nombre": nombre})


        respuesta = httpx.get(url_recuperar_docs, params=params)

        return respuesta.json()

    def recuperar_imagen_base64(self, url_imagen):        

        # Obtener la ruta del endpoint desde la url local
        parsed = urlparse(url_imagen)
        # self.url_api puede tener http(s)://ip:puerto
        base_api = self.url_api.rstrip('/')
        # Usar solo la ruta del endpoint
        nueva_url = base_api + parsed.path
        if parsed.query:
            nueva_url += '?' + parsed.query

        res = httpx.get(nueva_url)

        data = res.json()
        if "imagen_b64" in data:
            return data["imagen_b64"]
        else:
            # Si el backend aún devuelve texto plano, usar res.text
            return res.text
        

    
    def avanzar_puntero_repo(self, reverso=False):

        if not reverso and len(self.batch_archivos) == self.max_archivos:
            self.puntero_repo += self.max_archivos
            return True

        if reverso and self.puntero_repo > 0:
            self.puntero_repo -= self.max_archivos
            return True
        
        return False


    def recuperar_n_archivos(self, planta=None, enfermedad=None, formato=None, fuente=None):
        url_recuperar_n_img = self.crear_url("/servir_n_archivos_sin_validar", self.url_api)

        params = {
            "inicio": self.puntero_repo,
            "n_archivos": self.max_archivos
        }
        if planta: params["planta"] = planta
        if enfermedad: params["enfermedad"] = enfermedad
        if formato: params["formato"] = formato
        if fuente: params["fuente"] = fuente

        res = httpx.get(url_recuperar_n_img, params=params)
        archivos = res.json()
        self.batch_archivos = archivos

        return True
    
    def seleccionar_archivo(self, archivo):
        self.archivo_seleccionado = archivo
        return True
    
    def procesar_nombre_key_etiquetas(self):
        etiquetas = self.recuperar_etiquetas()

        res = []
        for etiqueta in etiquetas:
            if etiqueta["clasificacion"] == "healthy":
                res.append({"key": etiqueta["_id"], "texto": f"{etiqueta['planta']}, {etiqueta['clasificacion']}"})
            else:
                res.append({"key": etiqueta["_id"], "texto": f"{etiqueta['planta']}, {etiqueta['clasificacion']}, {etiqueta['nombre']}"})
        return res
    
    def procesar_nombre_una_etiqueta(self, id_etiqueta):
        etiquetas = self.recuperar_etiquetas()
        etiqueta = None
        for et in etiquetas:
            if et["_id"] == id_etiqueta:
                etiqueta = et
                pass

        if etiqueta["clasificacion"] == "healthy":
            texto = f"{etiqueta['planta']}, {etiqueta['clasificacion']}"
        else:
            texto = f"{etiqueta['planta']}, {etiqueta['clasificacion']}, {etiqueta['nombre']}"
        
        return texto

    def etiquetar_imagen(self, id_etiqueta: int):

        url_etiquetar_imagen = self.crear_url("/clasificar", self.url_api)
        res = httpx.post(url_etiquetar_imagen, json={"etiqueta": id_etiqueta, "doc": self.archivo_seleccionado["_id"]})
        return res.json()
    
    def procesar_foto(self, img):
        base64_image = base64.b64encode(img).decode("utf-8")
        self.foto_b64 = base64_image

    def subir_foto(self, id_etiqueta, fuente=2, formato=0): # Por defecto fuente App, formato Color
        if id_etiqueta == None:
            for etiqueta in self.recuperar_etiquetas():
                if etiqueta["clasificacion"] == "Sin_clasificar":
                    id_etiqueta = etiqueta["_id"]
                    pass

        url_subir_foto = self.crear_url("/subir_imagen", self.url_api)

        res = httpx.post(url_subir_foto, json={"imagen_b64": self.foto_b64, "clase": id_etiqueta, "campos_extra": {"fuente": fuente, "formato": formato}, "usuario": self.usuario["nombre"]})

        return res.json()

    def __init__(self):
        self.usuario = {"nombre": ""}

        self.lista_usuarios = None
        self.busqueda_anterior = None
        self.usuario_seleccionado={"placeholder": "placeholder"}

        self.puntero_repo = 0
        self.max_archivos = 5
        self.batch_archivos = []

        self.archivo_seleccionado = {}

        # Usar https:// para produccion
        self.url_api = os.getenv("URL_API")
        self.url_bbdd = os.getenv("URL_BBDD")

        self.api_key = "9ZQtYqJV/sevWZ+qL7pQMlur0NoXQK3ZQ9UT46ycxIE="
        self.headers = {"Authorization": "Bearer " + self.api_key}

        self.foto_b64 = ""

        self.evitar_recarga = False
        self.cargando_datos = False

#test = LogicaApp()
#print(test.registro("prueba1", "prueba1"))
#print(test.inicio_sesion("admin", "admin", "admin"))
#print(test.add_rol("hola1", "etiquetador"))
#print(eliminar_rol("hola1", "etiquetador"))
#print(test.buscar_usuarios(nombre="a", rol="admin"))
#print(test.lista_usuarios)
#print(test.hash_func("admin", "admin"))

#test.usuario["nombre"] = "admin"
#print(test.cambiar_nombre_usuario("admin1", "admin"))

#REGISTRO DE UN ADMIN
#test.registro("admin", "admin")
#test.add_rol("admin", "admin")


#print(test.recuperar_etiquetas())
#print(test.recuperar_docs(clasificacion="Sana"))
#print(test.recuperar_imagen_base64())

#print(test.procesar_nombre_key_etiquetas())
#print(test.etiquetar_imagen({'$oid': '67d2c4910c7cd1f092e43269'}, 12))