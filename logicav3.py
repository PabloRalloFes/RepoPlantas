import urllib.parse
import httpx
import urllib
import base64
import json

class LogicaApp:
    

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

        respuesta = httpx.post(url_registro, json=params, headers=self.headers)

        return respuesta.json()  

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

        self.usuario_seleccionado = respuesta.json()[0]
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

        res = httpx.get(url_imagen)

        return str(res.content)[2:-1]
    
    def avanzar_puntero_repo(self, reverso=False):

        if not reverso and len(self.batch_archivos) == self.max_archivos:
            self.puntero_repo += self.max_archivos
            return True

        if reverso and self.puntero_repo > 0:
            self.puntero_repo -= self.max_archivos
            return True
        
        return False


    def recuperar_n_archivos(self):

        url_recuperar_n_img = self.crear_url("/servir_n_archivos_sin_validar", self.url_api)

        res = httpx.get(url_recuperar_n_img, params={"inicio": self.puntero_repo, "n_archivos": self.max_archivos})

        archivos = json.loads(res.content)

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

        res = httpx.post(url_subir_foto, json={"imagen_b64": self.foto_b64, "clase": id_etiqueta, "campos_extra": {"fuente": fuente, "formato": formato}})

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
        #self.url_usuarios = "http://127.0.0.1:8000"
        #self.url_repo = "http://127.0.0.1:5001"
        self.url_api = "http://10.236.50.53:5001"

        self.api_key = "9ZQtYqJV/sevWZ+qL7pQMlur0NoXQK3ZQ9UT46ycxIE="
        self.headers = {"Authorization": "Bearer " + self.api_key}

        self.foto_b64 = ""

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