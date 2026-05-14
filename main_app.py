import flet as ft
import httpx
import logicav3 as logica
import os
import threading
import time
from datetime import datetime
from pathlib import Path

nombre_app = "PLANT-AID"


if __name__ == "__main__":

    logica_app = logica.LogicaApp()

    def _is_docker_internal_url(value: str) -> bool:
        if not value:
            return False
        lowered = value.strip().lower()
        return "://api:" in lowered or "://mongo:" in lowered

    def main(page: ft.Page):
        def safe_client_storage_get(key: str):
            try:
                return page.client_storage.get(key)
            except TimeoutError:
                return None
            except Exception:
                return None

        def safe_client_storage_remove(key: str):
            try:
                page.client_storage.remove(key)
            except Exception:
                pass

        saved_url_api = safe_client_storage_get("url_api")
        if saved_url_api and not _is_docker_internal_url(saved_url_api):
            logica_app.set_url_api(saved_url_api)
        elif saved_url_api:
            safe_client_storage_remove("url_api")

        saved_url_bbdd = safe_client_storage_get("url_bbdd")
        if saved_url_bbdd and not _is_docker_internal_url(saved_url_bbdd):
            previous_url_bbdd = logica_app.url_bbdd
            logica_app.set_url_bbdd(saved_url_bbdd)
            if saved_url_bbdd != previous_url_bbdd:
                logica_app.cambiar_url_bbdd()
        elif saved_url_bbdd:
            safe_client_storage_remove("url_bbdd")

        def mostrar_cargando(page, visible=True):
            if visible:
                page.overlay.append(
                    ft.Container(
                        alignment=ft.alignment.center,
                        bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.WHITE),
                        content=ft.Column(
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.ProgressRing(width=60, height=60),
                                ft.Text("Cargando...", size=18, color=ft.Colors.BLACK54)
                            ],
                        ),
                    )
                )
            else:
                page.overlay.clear()
            page.update()
        page.title = nombre_app

        page.theme = ft.Theme(color_scheme_seed=ft.Colors.GREEN)
        page.dark_theme = ft.Theme(color_scheme_seed=ft.Colors.GREEN)

        def view_pop(view):
            if len(page.views) > 1:
                page.views.pop()
                top_view = page.views[-1]
                page.go(top_view.route)
            else:
                page.go("/")
        
        alerta_cerrar_sesion = ft.AlertDialog(
            modal = True,
            title = ft.Text("¿Desea cerrar sesión?"),
            actions = [
                ft.TextButton(
                    "CERRAR SESIÓN",
                    on_click = view_pop
                ),
                ft.TextButton(
                    "MANTENER SESIÓN",
                    on_click = lambda _: page.close(alerta_cerrar_sesion)
                )
            ]
        )

        nombre_is = ft.TextField(
            label="Nombre de usuario",
        )
        password_is = ft.TextField(
            label="Contraseña",
            password=True,
            can_reveal_password=True
        )
        rol_is = ft.RadioGroup(
            content=ft.Row(
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Radio(value="usuario", label="Usuario"),
                    ft.Radio(value="etiquetador", label="Etiquetador"),
                    ft.Radio(value="admin", label="Admin"),
                ]
            )
        )

        nombre_r = ft.TextField(
            label = "Introduzca un nombre de usuario. NO INTRODUZCAS TU NOMBRE REAL. Max. 15 caracteres",
            max_length = 15,
            counter_text = "{max_length} caracteres máximos / {symbols_left} caracteres restantes",
        )
        password_r_1 = ft.TextField(
            label = "Introduzca una contraseña. Max 10 caracteres",
            max_length = 10,
            password=True,
            can_reveal_password=True,
            counter_text = "{max_length} caracteres máximos / {symbols_left} caracteres restantes",
        )
        password_r_2 = ft.TextField(
            label = "Vuelva a introducir la contraseña",
            max_length = 10,
            password=True,
            can_reveal_password=True,
            counter_text = "{max_length} caracteres máximos / {symbols_left} caracteres restantes",
        )

        buscador_nombre_admin = ft.TextField(
            label="Introducir nombre",
            visible=True,
        )

        buscar_usuario_rol_admin = ft.RadioGroup(
            value=None,
            content=ft.Row(
                [
                    ft.Radio(value=None, label="Cualquiera"),
                    ft.Radio(value="usuario", label="Usuario"),
                    ft.Radio(value="etiquetador", label="Etiquetador"),
                    ft.Radio(value="admin", label="Admin"),
                    ft.Radio(value="usuario+", label="Usuario+"),
                ],
                scroll=ft.ScrollMode.AUTO,
            )
        )

        alerta_no_resultados_busqueda = ft.AlertDialog(
            modal = True,
            title = ft.Text("No se encontraron resultados"),
            actions = [
                ft.TextButton(
                    "Aceptar",
                    on_click = lambda _: page.close(alerta_no_resultados_busqueda)
                )
            ]
        )

        def buscar_usuarios(nombre: str = None, rol: str= None):
            logica_app.buscar_usuarios(nombre, rol)
            if len(logica_app.lista_usuarios) == 0:
                page.open(alerta_no_resultados_busqueda)
            else: 
                page.route = "/main_admin/busqueda"
                route_change(page.route)

        def iniciar_sesion(e, nombre, password, rol, campos_borrar):
            if nombre == "" or password == "" or rol == None:
                campos_faltantes = f""
                if nombre == "": campos_faltantes += f"Nombre de usuario\n"
                if password == "": campos_faltantes += f"Contraseña\n"
                if rol == None: campos_faltantes += f"Rol\n"
                alerta_faltan_campos = ft.AlertDialog(
                    modal = True,
                    title = ft.Text("Falta por indicar:"),
                    content=ft.Text(campos_faltantes),
                    actions=[
                        ft.TextButton("Aceptar", on_click= lambda _: page.close(alerta_faltan_campos))
                    ]
                )
                page.open(alerta_faltan_campos)
            else:
                try:
                    if logica_app.inicio_sesion(nombre, password, rol):
                        if rol == "etiquetador":
                            # ahora va al menú principal del etiquetador
                            page.go("/main_etiquetador")
                        else:
                            page.go(f"/main_{rol}")
                    else:
                        alerta_error_inicio_sesion = ft.AlertDialog(
                            modal = True,
                            title = ft.Text("Datos de inicio de sesión incorrectos"),
                            actions=[
                                ft.TextButton("Aceptar", on_click= lambda _: page.close(alerta_error_inicio_sesion))
                            ]
                        )
                        page.open(alerta_error_inicio_sesion)
                except httpx.ConnectTimeout:
                    page.open(ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Error de conexión"),
                        content=ft.Text("Tiempo de espera agotado al conectar con el servidor.\n\nRevisa que la IP sea correcta en la configuración o verifica tu red."),
                        actions=[ft.TextButton("Aceptar", on_click= lambda e: page.close(e.control.parent))]
                    ))
                except httpx.RequestError as e:
                    page.open(ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Servidor inaccesible"),
                        content=ft.Text(f"No se pudo conectar con el servidor en {logica_app.url_api}.\n\nRevisa la IP en la configuración."),
                        actions=[ft.TextButton("Aceptar", on_click= lambda e: page.close(e.control.parent))]
                    ))
                except Exception as e:
                    page.open(ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Error inesperado"),
                        content=ft.Text(f"Ocurrió un error: {str(e)}"),
                        actions=[ft.TextButton("Aceptar", on_click=lambda e: page.close(e.control.parent))]
                    ))
            for x in campos_borrar: x.value = ""
            page.update()

        def registrarse(e, nombre, password_1, password_2, campos_borrar):
            if nombre == "" or password_1 == "" or password_2 == "":
                campos_faltantes = f""
                if nombre == "": campos_faltantes += f"Nombre de usuario\n"
                if password_1 == "": campos_faltantes += f"Contraseña\n"
                if password_2 == "": campos_faltantes += f"Repetir Contraseña\n"
                alerta_faltan_campos = ft.AlertDialog(
                    modal = True,
                    title = ft.Text("Falta por indicar:"),
                    content=ft.Text(campos_faltantes),
                    actions=[
                        ft.TextButton("Aceptar", on_click= lambda _: page.close(alerta_faltan_campos))
                    ]
                )
                page.open(alerta_faltan_campos)
            elif password_1 != password_2:
                alerta_passwords_distintas = ft.AlertDialog(
                    modal = True,
                    title = ft.Text("Las contraseñas no coinciden"),
                    actions=[
                        ft.TextButton("Aceptar", on_click= lambda _: page.close(alerta_passwords_distintas))
                    ]
                )
                page.open(alerta_passwords_distintas)
            else:
                res = logica_app.registro(nombre, password_1)
                if res.get("success"):
                    alerta_registro_correcto = ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Registro completado"),
                        content=ft.Text("Por favor, inicie sesión"),
                        actions=[ft.TextButton("Aceptar", on_click=view_pop)]
                    )
                    page.open(alerta_registro_correcto)
                else:
                    mensaje = res.get("error", "No se ha podido completar el registro")
                    alerta_usuario_existente = ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Error en el registro"),
                        content=ft.Text(mensaje),
                        actions=[ft.TextButton("Aceptar", on_click=lambda _: page.close(alerta_usuario_existente))]
                    )
                    page.open(alerta_usuario_existente)
            for x in campos_borrar: x.value = ""
            page.update()

        def seleccionar_usuario(e):
            logica_app.seleccionar_usuario(e)
            page.route = "/main_admin/busqueda/datos_usuario"
            route_change(page.route)

        def info_usuario_seleccionado():
            doc = getattr(logica_app, "usuario_seleccionado", {}) or {}
            name = doc.get("nombre", "")
            roles = doc.get("rol", [])
            roles_text = ", ".join(str(r) for r in roles)
            return [ft.Text(f"Nombre: {name}\nRoles: {roles_text}")]

        def crear_columnas(datos: list[dict]):
            if len(datos) == 0: return []
            datos.sort(key=len, reverse=True)
            refe = datos[0]

            # Mapeo de nombres de campos a etiquetas legibles
            nombre_columnas = {
                "nombre": "Nombre",
                "nombres_antiguos": "Nombres Antiguos",
                "rol": "Roles"
            }

            columnas = []
            for campo in refe.keys():
                etiqueta = nombre_columnas.get(campo, campo)
                columnas.append( ft.DataColumn(ft.Text(f"{etiqueta}", weight=ft.FontWeight.BOLD)) )
            
            return columnas
        
        def crear_filas(datos: list[dict]):
            filas = []

            for entrada in datos:
                celdas = []
                for val in entrada.values():
                    celdas.append(ft.DataCell(ft.Text(f"{val}")))
                filas.append(
                    ft.DataRow(
                        cells=celdas,
                        on_select_changed=lambda e, nombre=entrada.get("nombre"): seleccionar_usuario(nombre)
                    )
                )

            return filas

        def eliminar_usuario():
            resultado = logica_app.eliminar_usuario(logica_app.usuario_seleccionado)
            logica_app.busqueda_anterior()
            page.update()
            view_pop(page.views[-1])
            page.update()

            if resultado:
                page.open(ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Usuario eliminado correctamente"),
                    actions=[ft.TextButton("Aceptar", on_click=lambda e: page.close(e.control.parent))]
                ))
            else:
                page.open(ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Error al eliminar el usuario"),
                    actions=[ft.TextButton("Aceptar", on_click=lambda e: page.close(e.control.parent))]
                ))


        ### NUEVAS ###

        def predecir_foto(modelo_seleccionado, known_planta=None):
            if known_planta == "Ninguna":
                known_planta = None
            resultado = logica_app.predecir_imagen(modelo_seleccionado, known_planta)
            if resultado["success"]:
                pred = resultado["enfermedad_predicha"]
                planta = resultado["planta_predicha"]
                prob = round(resultado["probabilidad"] * 100, 2)
                page.open(ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Predicción del modelo", weight=ft.FontWeight.BOLD),
                    content=ft.Column(
                        tight=True,
                        spacing=8,
                        controls=[
                            ft.Row(spacing=10, controls=[ft.Text("Planta:", weight=ft.FontWeight.BOLD), ft.Text(planta)]),
                            ft.Row(spacing=10, controls=[ft.Text("Enfermedad:", weight=ft.FontWeight.BOLD), ft.Text(pred)]),
                            ft.Row(spacing=10, controls=[ft.Text("Probabilidad:", weight=ft.FontWeight.BOLD), ft.Text(f"{prob}%")])
                        ]
                    ),
                    actions=[ft.TextButton("Aceptar", on_click=lambda e: page.close(e.control.parent))]
                ))
            else:
                page.open(ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Error en la predicción"),
                    content=ft.Text(resultado.get("error", "Error desconocido")),
                    actions=[ft.TextButton("Aceptar", on_click=lambda e: page.close(e.control.parent))]
                ))

        def validar_imagen_actual():
            id_doc = logica_app.archivo_seleccionado["_id"]
            resultado = logica_app.validar_imagen(id_doc)

            if resultado["success"]:
                mostrar_cargando(page, True)
                cargar_datos_no_validados()
                page.open(ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Imagen validada"),
                    actions=[ft.TextButton("Aceptar", on_click=lambda e: page.go("/main_etiquetador/seleccion_imagenes"))]
                ))
            else:
                page.open(ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Error al validar"),
                    content=ft.Text(resultado.get("error", "Error desconocido")),
                    actions=[ft.TextButton("Aceptar", on_click=lambda e: page.close(e.control.parent))]
                ))
            
            page.update()

        def cargar_fuentes_dropdown(fuente_dropdown):
            try:
                resultado = logica_app.listar_fuentes_importadas()
                if resultado.get("success"):
                    fuentes = resultado.get("fuentes", [])
                    fuente_dropdown.options = [ft.dropdown.Option(f) for f in fuentes]
                    if fuente_dropdown.value not in fuentes:
                        fuente_dropdown.value = None
                else:
                    fuente_dropdown.options = []
            except Exception:
                fuente_dropdown.options = []
            page.update()

        def cargar_formatos_dropdown(formato_dropdown):
            try:
                resultado = logica_app.obtener_opciones_formatos()
                # Resultado puede ser lista o dict
                if isinstance(resultado, dict):
                    formatos = resultado.get("formatos") or resultado.get("options") or resultado
                else:
                    formatos = resultado

                opciones = []
                if isinstance(formatos, list):
                    for f in formatos:
                        if isinstance(f, dict):
                            key = f.get("_id", f.get("id", f.get("key", f.get("nombre", str(f)))))
                            text = f.get("nombre") or f.get("text") or str(f)
                        else:
                            key = f
                            text = str(f)
                        opciones.append(ft.dropdown.Option(key=key, text=text))

                formato_dropdown.options = opciones
                if opciones:
                    available_keys = {opt.key for opt in opciones}
                    if formato_dropdown.value not in available_keys:
                        formato_dropdown.value = opciones[0].key
                else:
                    formato_dropdown.value = None
            except Exception:
                formato_dropdown.options = []
                formato_dropdown.value = None
            page.update()

        def subir_zip(page, logica_app, zip_picker, nombre_fuente_input, fuente_dropdown):
            """Sube el ZIP al servidor y lo descomprime"""
            if not zip_picker.result or not zip_picker.result.files:
                page.open(ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Error"),
                    content=ft.Text("Selecciona un archivo ZIP."),
                    actions=[ft.TextButton("Aceptar", on_click=lambda e: page.close(e.control.parent))]
                ))
                return
            
            nombre_fuente = nombre_fuente_input.value.strip()
            if not nombre_fuente:
                page.open(ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Error"),
                    content=ft.Text("Introduce el nombre de la fuente."),
                    actions=[ft.TextButton("Aceptar", on_click=lambda e: page.close(e.control.parent))]
                ))
                return
            
            file_path = zip_picker.result.files[0].path
            
            page.open(ft.AlertDialog(
                modal=True,
                title=ft.Text("Subiendo ZIP..."),
                content=ft.Text("Esto puede tardar unos minutos según el tamaño."),
                actions=[]
            ))
            page.update()
            
            try:
                with open(file_path, 'rb') as f:
                    zip_bytes = f.read()
                
                data = logica_app.subida_masiva_zip(zip_bytes, nombre_fuente)
                
                if data.get("success"):
                    page.open(ft.AlertDialog(
                        modal=True,
                        title=ft.Text("ZIP subido correctamente"),
                        content=ft.Text(data.get("message")),
                        actions=[ft.TextButton("Aceptar", on_click=lambda e: page.close(e.control.parent))]
                    ))
                    # Limpiar campos
                    nombre_fuente_input.value = ""
                    # Recargar dropdown de fuentes
                    cargar_fuentes_dropdown(fuente_dropdown)
                else:
                    page.open(ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Error al subir ZIP"),
                        content=ft.Text(data.get("error", "Error desconocido")),
                        actions=[ft.TextButton("Aceptar", on_click=lambda e: page.close(e.control.parent))]
                    ))
            except Exception as e:
                page.open(ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Error de conexión"),
                    content=ft.Text(str(e)),
                    actions=[ft.TextButton("Aceptar", on_click=lambda e: page.close(e.control.parent))]
                ))
            
            page.update()

        def ejecutar_subida_masiva(page, logica_app, fuente_input, procesar_switch, validada_switch):
            fuente = fuente_input.value.strip()
            procesar = procesar_switch.value
            validada = validada_switch.value

            if not fuente:
                page.open(ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Error"),
                    content=ft.Text("Selecciona una fuente."),
                    actions=[ft.TextButton("Aceptar", on_click=lambda e: page.close(e.control.parent))]
                ))
                return

            page.open(ft.AlertDialog(
                modal=True,
                title=ft.Text("Ejecutando subida..."),
                content=ft.Text("Esto puede tardar unos minutos."),
                actions=[]
            ))
            page.update()

            try:
                data = logica_app.subida_masiva(fuente, procesar, validada)
                if data.get("success"):
                    page.open(ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Subida completada"),
                        content=ft.Text(data.get("message")),
                        actions=[ft.TextButton("Aceptar", on_click=lambda e: page.go("/main_usuario"))]
                    ))
                else:
                    page.open(ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Error durante la subida"),
                        content=ft.Text(data.get("error")),
                        actions=[ft.TextButton("Aceptar", on_click=lambda e: page.close(e.control.parent))]
                    ))
            except Exception as e:
                page.open(ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Error de conexión"),
                    content=ft.Text(str(e)),
                    actions=[ft.TextButton("Aceptar", on_click=lambda e: page.close(e.control.parent))]
                ))

            page.update()

        def abrir_dialogo_add_class(e):
            planta_input = ft.TextField(label="Planta")
            comun_input = ft.TextField(label="Nombre común")
            clasif_input = ft.TextField(label="Clasificación")
            cient_input = ft.TextField(label="Nombre científico")

            def confirmar_add(ev):
                nueva = {
                    "planta": planta_input.value.strip(),
                    "nombre_comun": comun_input.value.strip(),
                    "clasificacion": clasif_input.value.strip(),
                    "nombre_cientifico": cient_input.value.strip()
                }
                res = logica_app.agregar_clase(nueva)
                if res.get("success"):
                    page.close(dialogo)

                    def recargar(e):
                        page.close(dialogo_exito)
                        page.go("/main_etiquetador")

                    dialogo_exito = ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Clase añadida"),
                        content=ft.Text("La nueva clase se ha guardado correctamente."),
                        actions=[ft.TextButton("Aceptar", on_click=recargar)]
                    )

                    page.open(dialogo_exito)
                else:
                    page.open(ft.AlertDialog(
                        title=ft.Text("Error"),
                        content=ft.Text(res.get("error", "No se pudo añadir la clase.")),
                        actions=[ft.TextButton("Aceptar", on_click=lambda e: page.close(e.control.parent))]
                    ))

            dialogo = ft.AlertDialog(
                modal=True,
                title=ft.Text("Añadir nueva clase"),
                content=ft.Column([
                    planta_input,
                    comun_input,
                    clasif_input,
                    cient_input,
                ], tight=True),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: page.close(dialogo)),
                    ft.TextButton("Añadir", on_click=confirmar_add)
                ],
            )

            page.open(dialogo)

        def aplicar_filtros_handler(page, dropdown_planta, dropdown_enfermedad, dropdown_formato, dropdown_fuente, dropdown_num_imagenes):
            def _handler(e=None):
                if not dropdown_num_imagenes.value:
                    page.open(ft.AlertDialog(title=ft.Text("Selecciona el número de imágenes")))
                    return

                logica_app.filtros_actuales = {
                    "planta": None if dropdown_planta.value == "Cualquiera" else dropdown_planta.value,
                    "enfermedad": None if dropdown_enfermedad.value == "Cualquiera" else dropdown_enfermedad.value,
                    "formato": None if dropdown_formato.value == "Cualquiera" else dropdown_formato.value,
                    "fuente": None if dropdown_fuente.value == "Cualquiera" else dropdown_fuente.value,
                    "num": int(dropdown_num_imagenes.value)
                }
                logica_app.max_archivos = int(dropdown_num_imagenes.value)
                logica_app.puntero_repo = 0

                mostrar_cargando(page, True)
                cargar_datos_no_validados()
                page.update()
                page.go("/main_etiquetador/seleccion_imagenes")
            return _handler
        
        def crear_experimento(nombre_experimento, config_variables, entrenar_modelo, disponible_prediccion, page):
            if not nombre_experimento:
                alerta_nombre_faltante = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Error"),
                    content=ft.Text("El nombre del experimento es obligatorio."),
                    actions=[ft.TextButton("Aceptar", on_click=lambda _: page.close(alerta_nombre_faltante))]
                )
                page.open(alerta_nombre_faltante)
                return
            elif nombre_experimento in [exp["nombre"] for exp in logica_app.obtener_experimentos()]:
                alerta_nombre_existente = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Error"),
                    content=ft.Text("El nombre del experimento ya existe. Elige otro nombre."),
                    actions=[ft.TextButton("Aceptar", on_click=lambda _: page.close(alerta_nombre_existente))]
                )
                page.open(alerta_nombre_existente)
                return

            try:
                response = logica_app.crear_experimento(nombre_experimento, config_variables)
                if response.get("success"):
                    if entrenar_modelo:
                        logica_app.solicitar_entrenamiento(nombre_experimento, disponible_prediccion)
                    alerta_exito = ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Éxito"),
                        content=ft.Text(f"Experimento '{nombre_experimento}' creado con éxito."),
                        actions=[ft.TextButton("Aceptar", on_click=lambda _: (mostrar_cargando(page, True), page.close(alerta_exito), page.go("/main_usuario/experimentos")))]
                    )
                    page.open(alerta_exito)
                else:
                    alerta_error = ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Error"),
                        content=ft.Text(f"Error: {response.get('error')}"),
                        actions=[ft.TextButton("Aceptar", on_click=lambda _: page.close(alerta_error))]
                    )
                    page.open(alerta_error)
            except Exception as ex:
                alerta_excepcion = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Error inesperado"),
                    content=ft.Text(f"Error al crear el experimento: {str(ex)}"),
                    actions=[ft.TextButton("Aceptar", on_click=lambda _: page.close(alerta_excepcion))]
                )
                page.open(alerta_excepcion)  
            page.update()

        def entrenar_modelo(nombre_experimento, aceptar_disponible_prediccion=False):
            dialogo_entrenamiento = ft.AlertDialog(
                modal=True,
                title=ft.Text("Entrenamiento en progreso"),
                content=ft.Text("El entrenamiento puede tardar un tiempo. Por favor, espere."),
                actions=[],
            )

            # Mostrar el diálogo de entrenamiento
            page.open(dialogo_entrenamiento)

            try:
                resultado = logica_app.entrenar_modelo(nombre_experimento, aceptar_disponible_prediccion)
                if resultado["success"]:
                    page.open(ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Entrenamiento completado"),
                        content=ft.Text(f"El modelo '{nombre_experimento}' se ha entrenado correctamente."),
                        actions=[ft.TextButton("Aceptar", on_click=lambda _: (mostrar_cargando(page, True), setattr(page, 'route', '/main_admin/entrenamientos'), route_change(page.route)))]
                    ))
                else:
                    page.open(ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Error en el entrenamiento"),
                        content=ft.Text(resultado.get("error", "Error desconocido")),
                        actions=[ft.TextButton("Aceptar", on_click=lambda _: (mostrar_cargando(page, True), setattr(page, 'route', '/main_admin/entrenamientos'), route_change(page.route)))]
                    ))
            except Exception as ex:
                page.open(ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Error inesperado"),
                    content=ft.Text(f"Error: {str(ex)}"),
                    actions=[ft.TextButton("Aceptar", on_click=lambda _: (mostrar_cargando(page, True), setattr(page, 'route', '/main_admin/entrenamientos'), route_change(page.route)))]
                ))


        ### FIN NUEVAS ###



        alerta_borrar_usuario = ft.AlertDialog(
            modal = True,
            title = ft.Text("¿Seguro que quieres eliminar este usuario?"),
            actions = [
                ft.TextButton(
                    "ELMINAR",
                    on_click = lambda _: eliminar_usuario()
                ),
                ft.TextButton(
                    "Cancelar",
                    on_click = lambda _: page.close(alerta_borrar_usuario)
                )
            ]
        )

        selector_rol_editar_usuario = ft.RadioGroup(
            content=ft.Row(
                [
                    ft.Radio(value="usuario", label="Usuario"),
                    ft.Radio(value="etiquetador", label="Etiquetador"),
                    ft.Radio(value="admin", label="Admin"),
                    ft.Radio(value="usuario+", label="Usuario+"),
                ]
            )
        )

        def eliminar_rol():
            res = logica_app.eliminar_rol(logica_app.usuario_seleccionado['nombre'], selector_rol_editar_usuario.value)
            page.close(alerta_eliminar_rol)
            page.update()
            logica_app.busqueda_anterior()

            if res.get("success"):
                page.open(
                    ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Rol eliminado correctamente"),
                        content=ft.Text(res.get("message", "")),
                        actions=[ft.TextButton("Aceptar", on_click=lambda e: page.close(e.control.parent))]
                    )
                )
            else:
                page.open(
                    ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Error al eliminar rol"),
                        content=ft.Text(res.get("error", "Error desconocido")),
                        actions=[ft.TextButton("Aceptar", on_click=lambda e: page.close(e.control.parent))]
                    )
                )

        def add_rol():
            res = logica_app.add_rol(logica_app.usuario_seleccionado['nombre'], selector_rol_editar_usuario.value)
            page.close(alerta_add_rol)
            page.update()
            logica_app.busqueda_anterior()

            if res.get("success"):
                page.open(
                    ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Rol añadido correctamente"),
                        content=ft.Text(res.get("message", "")),
                        actions=[ft.TextButton("Aceptar", on_click=lambda e: page.close(e.control.parent))]
                    )
                )
            else:
                page.open(
                    ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Error al añadir rol"),
                        content=ft.Text(res.get("error", "Error desconocido")),
                        actions=[ft.TextButton("Aceptar", on_click=lambda e: page.close(e.control.parent))]
                    )
                )

        alerta_eliminar_rol = ft.AlertDialog(
            modal = True,
            title = ft.Text(f"¿Seguro que eliminar el rol?"),
            actions = [
                ft.TextButton(
                    "ELMINAR",
                    on_click = lambda _: eliminar_rol()
                ),
                ft.TextButton(
                    "Cancelar",
                    on_click = lambda _: page.close(alerta_eliminar_rol)
                )
            ]
        )

        alerta_add_rol = ft.AlertDialog(
            modal = True,
            title = ft.Text(f"¿Seguro que añadir el rol?"),
            actions = [
                ft.TextButton(
                    "AÑADIR",
                    on_click = lambda _: add_rol()
                ),
                ft.TextButton(
                    "Cancelar",
                    on_click = lambda _: page.close(alerta_add_rol)
                )
            ]
        )

        nuevo_usuario_modificar_usuario = ft.TextField(
            label = "Introduzca un nuevo nombre de usuario. NO INTRODUZCAS TU NOMBRE REAL. Max. 15 caracteres",
            max_length = 15,
            counter_text = "{max_length} caracteres máximos / {symbols_left} caracteres restantes",
        )

        nueva_password_modificar_usuario = ft.TextField(
            label = "Introduzca una nueva contraseña. Max 10 caracteres",
            max_length = 10,
            password=True,
            can_reveal_password=True,
            counter_text = "{max_length} caracteres máximos / {symbols_left} caracteres restantes",
        )

        nueva_password_modificar_usuario_repetir = ft.TextField(
            label = "Repita su nueva contraseña. Max 10 caracteres",
            max_length = 10,
            password=True,
            can_reveal_password=True,
            counter_text = "{max_length} caracteres máximos / {symbols_left} caracteres restantes",
        )
        
        password_modificar_usuario = ft.TextField(
            label = "Introduzca su contraseña actual.",
            password=True,
            can_reveal_password=True,
        )

        def cambiar_nombre_usuario():
            res = logica_app.cambiar_nombre_usuario(nuevo_usuario_modificar_usuario.value, password_modificar_usuario.value)
            password_modificar_usuario.value = ""
            nuevo_usuario_modificar_usuario.value = ""

            if not res[0]:
                page.open(
                    ft.AlertDialog(
                        modal = True,
                        title = ft.Text(f"{res[1]}"),
                        actions = [
                            ft.TextButton(
                                "Aceptar",
                                on_click = lambda e: page.close(e.control.parent)
                            ),
                        ]
                    )
                )
            else:
                page.close(alerta_cambiar_nombre_usuario)
                page.open(
                    ft.AlertDialog(
                        modal = True,
                        title = ft.Text("Nombre de usuario cambiado con éxito"),
                        actions = [
                            ft.TextButton(
                                "Aceptar",
                                on_click = lambda e: page.close(e.control.parent)
                            ),
                        ]
                    )
                )
            

        alerta_cambiar_nombre_usuario = ft.AlertDialog(
            modal = True,
            title = ft.Text("Introduce los siguientes datos para cambiar el nombre de usuario"),
            content = ft.Column(
                alignment = ft.MainAxisAlignment.CENTER,
                horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                controls=[
                    nuevo_usuario_modificar_usuario,
                    password_modificar_usuario
                ]
            ),
            actions = [
                ft.TextButton(
                    "Confirmar",
                    on_click = lambda _: cambiar_nombre_usuario()
                ),
                ft.TextButton(
                    "Cancelar",
                    on_click = lambda _: page.close(alerta_cambiar_nombre_usuario)
                )
            ]
        )

        def cambiar_password():
            res = logica_app.cambiar_password(nueva_password_modificar_usuario.value, nueva_password_modificar_usuario_repetir.value ,password_modificar_usuario.value)
            password_modificar_usuario.value = ""
            nueva_password_modificar_usuario.value = ""
            nueva_password_modificar_usuario_repetir.value = ""

            if not res[0]:
                page.open(
                    ft.AlertDialog(
                        modal = True,
                        title = ft.Text(f"{res[1]}"),
                        actions = [
                            ft.TextButton(
                                "Aceptar",
                                on_click = lambda e: page.close(e.control.parent)
                            ),
                        ]
                    )
                )
            else:
                page.close(alerta_cambiar_password)
                page.open(
                    ft.AlertDialog(
                        modal = True,
                        title = ft.Text("Contraseña cambiada con éxito"),
                        actions = [
                            ft.TextButton(
                                "Aceptar",
                                on_click = lambda e: page.close(e.control.parent)
                            ),
                        ]
                    )
                )

        alerta_cambiar_password = ft.AlertDialog(
            modal = True,
            title = ft.Text("Introduce los siguientes datos para cambiar la contraseña"),
            content = ft.Column(
                alignment = ft.MainAxisAlignment.CENTER,
                horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                controls=[
                    password_modificar_usuario,
                    nueva_password_modificar_usuario,
                    nueva_password_modificar_usuario_repetir
                ]
            ),
            actions = [
                ft.TextButton(
                    "Confirmar",
                    on_click = lambda _: cambiar_password()
                ),
                ft.TextButton(
                    "Cancelar",
                    on_click = lambda _: page.close(alerta_cambiar_password)
                )
            ]
        )

        icono_usuario = ft.IconButton(
            icon=ft.Icons.PERSON,
            icon_color=ft.Colors.WHITE,
            icon_size=30,
            tooltip="Datos Usuario",
            on_click=lambda _: page.open(
                ft.BottomSheet(
                    content=ft.Container(
                        padding=50,
                        content=ft.Column(
                            controls=[
                                ft.Text(
                                    "Datos Usuario:",
                                    size=18,
                                ),
                                ft.Divider(),
                                ft.Text(
                                    f"Nombre de usuario: {logica_app.usuario['nombre']}",
                                    size=16,
                                ),
                                ft.Divider(),
                                ft.ElevatedButton(
                                    "Cambiar nombre de usuario",
                                    color=ft.Colors.WHITE,
                                    bgcolor=ft.Colors.RED, 
                                    on_click=lambda _: page.open(alerta_cambiar_nombre_usuario)
                                ),
                                ft.ElevatedButton(
                                    "Cambiar contraseña",
                                    color=ft.Colors.WHITE,
                                    bgcolor=ft.Colors.RED, 
                                    on_click=lambda _: page.open(alerta_cambiar_password)
                                ),
                                ft.ElevatedButton(
                                    "Cerrar",
                                    color=ft.Colors.WHITE,
                                    bgcolor=ft.Colors.GREEN, 
                                    on_click=lambda e: page.close(e.control.parent.parent.parent)
                                ),
                            ],
                        ),
                    ),
                )
            )
        )

        def _load_about_info():
            try:
                about_path = Path(__file__).parent / "src" / "assets" / "colaboradores.txt"
                info = {}
                if about_path.exists():
                    for line in about_path.read_text(encoding="utf-8").splitlines():
                        if ":" in line:
                            k, v = line.split(":", 1)
                            info[k.strip().upper()] = v.strip()
                return info
            except Exception:
                return {}

        def _open_about(_=None):
            info = _load_about_info()
            autor = info.get("AUTOR", "")
            colaboradores = info.get("COLABORADORES", "")
            coordinador = info.get("COORDINADOR", "")

            # Determinar altura del BottomSheet (coincidir con límite inferior de ventana)
            sheet_height = getattr(page, "window_height", None) or getattr(page, "height", None) or 600

            page.open(
                ft.BottomSheet(
                    content=ft.Container(
                        height=sheet_height,
                        padding=20,
                        content=ft.Column(
                            scroll=ft.ScrollMode.AUTO,
                            controls=[
                                ft.Text("PLANT-AID", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
                                ft.Divider(),
                                ft.Text("Sobre nosotros", size=18, weight=ft.FontWeight.BOLD),
                                ft.Divider(),
                                ft.Text("AUTOR:", size=16, weight=ft.FontWeight.BOLD),
                                ft.Text(autor, size=14),
                                ft.Container(height=10),
                                ft.Text("COLABORADORES:", size=16, weight=ft.FontWeight.BOLD),
                                ft.Text(colaboradores, size=14),
                                ft.Container(height=10),
                                ft.Text("COORDINADOR:", size=16, weight=ft.FontWeight.BOLD),
                                ft.Text(coordinador, size=14),
                                ft.Container(height=20),
                                ft.ElevatedButton(
                                    "Cerrar",
                                    color=ft.Colors.WHITE,
                                    bgcolor=ft.Colors.GREEN,
                                    on_click=lambda e: page.close(e.control.parent.parent.parent),
                                ),
                            ],
                        ),
                    ),
                )
            )

        icono_about = ft.IconButton(
            icon=ft.Icons.INFO,
            icon_color=ft.Colors.WHITE,
            icon_size=30,
            tooltip="Sobre la aplicación",
            on_click=_open_about,
        )

        def foto_seleccionada(e: ft.FilePickerResultEvent):
            if seleccionar_foto.result is not None and seleccionar_foto.result is not None:
                for f in seleccionar_foto.result.files:
                    print(f"Nombre archivo: {f.name}")
                    print(f"Path archivo: {f.path}")

        seleccionar_foto = ft.FilePicker(
            on_result = foto_seleccionada
        )


        def seleccionar_imagen(e):
            mostrar_cargando(page, True)
            logica_app.seleccionar_archivo(e.control.data)
            #logica_app.evitar_recarga = True
            page.go("/main_etiquetador/seleccion_imagenes/etiquetar")
           

        def avanzar_imagenes(reverso=False):
            if logica_app.avanzar_puntero_repo(reverso):
                cargar_datos_no_validados()

                # Si se intentó avanzar más allá del final y no hay datos,
                # volvemos al último bloque válido.
                if not reverso and len(logica_app.batch_archivos) == 0 and logica_app.puntero_repo > 0:
                    logica_app.puntero_repo -= logica_app.max_archivos
                    cargar_datos_no_validados()
            else:
                mostrar_cargando(page, False)

            actualizar_estado_paginacion_imagenes()
            
            page.update()
            

        def retroceder_imagenes():
            avanzar_imagenes(reverso=True)

        boton_anterior_imagenes = None
        boton_siguiente_imagenes = None

        def actualizar_estado_paginacion_imagenes():
            if boton_anterior_imagenes is None or boton_siguiente_imagenes is None:
                return

            boton_anterior_imagenes.disabled = logica_app.puntero_repo <= 0
            boton_siguiente_imagenes.disabled = len(logica_app.batch_archivos) < logica_app.max_archivos
        
        tabla_docs_no_validados = ft.DataTable(
            columns=[
                ft.DataColumn(label=ft.Text("Imagen", size=16, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(label=ft.Text("Etiqueta Provisional", size=16, weight=ft.FontWeight.BOLD)),
            ],
            rows=[],
            column_spacing=32,
            horizontal_lines=ft.border.BorderSide(1, ft.Colors.GREY_700),
            data_row_max_height=96,
            data_row_min_height=96
        )

        def cargar_datos_no_validados(e=None):
            """if getattr(logica_app, "evitar_recarga", False):
                logica_app.evitar_recarga = False
                return"""
            logica_app.evitar_recarga = True
            if hasattr(logica_app, "filtros_actuales"):
                filtros = logica_app.filtros_actuales
                logica_app.recuperar_n_archivos(
                    planta=filtros.get("planta"),
                    enfermedad=filtros.get("enfermedad"),
                    formato=filtros.get("formato"),
                    fuente=filtros.get("fuente")
                )
            else:
                logica_app.recuperar_n_archivos()

            tabla_docs_no_validados.rows.clear()

            for item in logica_app.batch_archivos:
                fila = ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Container(
                                content=ft.Image(
                                    src_base64=logica_app.recuperar_imagen_base64(item["imagen_rgb"]),
                                    fit=ft.ImageFit.CONTAIN
                                ),
                                width=80,
                                height=80,
                                alignment=ft.alignment.center
                            )
                        ),
                        ft.DataCell(ft.Text(logica_app.procesar_nombre_una_etiqueta(item["clase"]), size=13, weight=ft.FontWeight.BOLD)),
                    ],
                    on_select_changed=seleccionar_imagen,
                    data=item
                )
                tabla_docs_no_validados.rows.append(fila)
            #logica_app.evitar_recarga = False
            actualizar_estado_paginacion_imagenes()
            page.update()

            import time
            time.sleep(0.3)
            mostrar_cargando(page, False)
            page.update()

        def dropdown_etiquetar_options(opcion_por_defecto=None):
            etiquetas_procesadas = logica_app.procesar_nombre_key_etiquetas()
            dropdown_etiquetar.options.clear()
            dropdown_etiquetar.options.append(ft.dropdown.Option(key="none", text="Sin clasificar"))
            for ep in etiquetas_procesadas:
                dropdown_etiquetar.options.append(ft.dropdown.Option(key=str(ep["key"]), text=ep["texto"]))

            valor_por_defecto = "none" if opcion_por_defecto is None else str(opcion_por_defecto)
            claves_disponibles = {str(opt.key) for opt in dropdown_etiquetar.options}
            dropdown_etiquetar.value = valor_por_defecto if valor_por_defecto in claves_disponibles else "none"
            dropdown_etiquetar.update()

        dropdown_etiquetar = ft.Dropdown(
            label="Etiqueta",
            hint_text=None,
            width=450,
            options=[ft.dropdown.Option(key="none", text="Sin clasificar")],
            value="none",
            border_color=ft.Colors.WHITE,
            focused_border_color=ft.Colors.GREEN,
            label_style=ft.TextStyle(color=ft.Colors.WHITE),
        )


        dropdown_formato = ft.Dropdown(
            label="Formato",
            hint_text=None,
            width=250,
            options=[
                ft.dropdown.Option(key=0, text="Color"),
                ft.dropdown.Option(key=1, text="Grayscale"),
                ft.dropdown.Option(key=2, text="Segmented"),
            ],
            value=0,
            border_color=ft.Colors.WHITE,
            focused_border_color=ft.Colors.GREEN,
            label_style=ft.TextStyle(color=ft.Colors.WHITE),
        )


        alerta_imagen_etiquetada = ft.AlertDialog(
            modal = True,
            title = ft.Text("Imagen etiquetada correctamente"),
            actions = [
                ft.TextButton(
                    "Aceptar",
                    on_click = lambda _: (mostrar_cargando(page, True), cargar_datos_no_validados(), page.update(), page.go("/main_etiquetador/seleccion_imagenes"))
                )
            ]
        )

        def etiquetar_imagen():
            if dropdown_etiquetar.value is None or dropdown_etiquetar.value == "none":
                page.open(ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Falta seleccionar una etiqueta"),
                    content=ft.Text("Selecciona una etiqueta valida antes de continuar."),
                    actions=[ft.TextButton("Aceptar", on_click=lambda e: page.close(e.control.parent))]
                ))
                return

            id_etiqueta = int(dropdown_etiquetar.value)
            res = logica_app.etiquetar_imagen(id_etiqueta)

            if res:
                mostrar_cargando(page, True)
                cargar_datos_no_validados()
                page.open(alerta_imagen_etiquetada)
            
            page.update()

        def on_image_selected(e: ft.FilePickerResultEvent):
            if not e.files:
                page.open(ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Ningún archivo seleccionado"),
                    actions=[ft.TextButton("Aceptar", on_click=lambda e: page.close(e.control.parent))]
                ))
                return

            file = e.files[0]
            img_bytes = None

            # En web, Flet 0.28 devuelve file.content (BytesIO)
            if hasattr(file, "content") and file.content is not None:
                img_bytes = file.content.read()
            elif getattr(file, "path", None):
                with open(file.path, "rb") as f:
                    img_bytes = f.read()
            else:
                page.open(ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Error al seleccionar imagen"),
                    content=ft.Text("No se pudo obtener el contenido del archivo."),
                    actions=[ft.TextButton("Aceptar", on_click=lambda e: page.close(e.control.parent))]
                ))
                return

            logica_app.procesar_foto(img_bytes)
            page.go("/main_usuario/foto")

        def subir_foto():
            if dropdown_etiquetar.value is None or dropdown_etiquetar.value == "none":
                page.open(ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Falta seleccionar una etiqueta"),
                    content=ft.Text("Por favor, selecciona una categoría antes de subir la imagen."),
                    actions=[ft.TextButton("Aceptar", on_click=lambda e: page.close(e.control.parent))]
                ))
                return

            try:
                id_etiqueta_sel = int(dropdown_etiquetar.value)
            except (TypeError, ValueError):
                page.open(ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Etiqueta inválida"),
                    content=ft.Text("La etiqueta seleccionada no tiene un identificador válido."),
                    actions=[ft.TextButton("Aceptar", on_click=lambda e: page.close(e.control.parent))]
                ))
                return

            # Obtener formato seleccionado (por defecto 0 = Color)
            try:
                formato_sel = int(dropdown_formato.value) if (dropdown_formato and dropdown_formato.value is not None) else 0
            except (TypeError, ValueError):
                formato_sel = 0

            subida_correcta = logica_app.subir_foto(id_etiqueta_sel, formato=formato_sel)

            if isinstance(subida_correcta, dict) and subida_correcta.get("success"):
                page.open(ft.AlertDialog(
                    modal = True,
                    title = ft.Text("Imagen subida correctamente"),
                    actions = [
                        ft.TextButton(
                            "Aceptar",
                            on_click = lambda _: page.go("/main_usuario")
                        )
                    ]
                ))
            else:
                mensaje_error = subida_correcta.get("error") if isinstance(subida_correcta, dict) else "No se ha podido subir la imagen"
                detalle_error = subida_correcta.get("detail") if isinstance(subida_correcta, dict) else None
                page.open(ft.AlertDialog(
                    modal = True,
                    title = ft.Text("No se ha podido subir la imagen"),
                    content=ft.Text(f"{mensaje_error}\n{detalle_error}" if detalle_error else mensaje_error),
                    actions = [
                        ft.TextButton(
                            "Aceptar",
                            on_click = lambda _: page.go("/main_usuario")
                        )
                    ]
                ))

        def obtener_logos():
            """try:
                logos_b64 = logica_app.logos()
            except Exception:
                logos_b64 = None

            if logos_b64:
                return ft.Container(
                    content=ft.Image(
                        src_base64=logos_b64,  # Aquí llega el base64
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    height=100,
                    bgcolor=ft.Colors.WHITE,
                    alignment=ft.alignment.center
                )"""

            return ft.Container(
                content=ft.Image(
                    src="./src/assets/logos.png",
                    fit=ft.ImageFit.CONTAIN,
                    height=100
                ),
                bgcolor=ft.Colors.WHITE,
                height=100,
                alignment=ft.alignment.center
            )

        def route_change(route):
            nonlocal dropdown_etiquetar, dropdown_formato
            page.views.clear()
            page.views.append(
               ft.View(
                    "/",
                    [
                        ft.AppBar(
                            title = ft.Text(nombre_app, size = 30, text_align= "end", weight=ft.FontWeight.BOLD),
                            toolbar_height = 50,
                            bgcolor = ft.Colors.GREEN,
                            center_title = True
                        ),
                        ft.Row(
                            expand = True,
                            alignment = ft.MainAxisAlignment.CENTER,
                            vertical_alignment = ft.CrossAxisAlignment.CENTER,
                            controls = [
                                ft.Column(
                                    alignment = ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                                    expand = True,
                                    scroll = ft.ScrollMode.AUTO,
                                    controls = [
                                        ft.Text(
                                            "¿No tienes cuenta de usuario? Regístrate",
                                            size = 18,
                                        ),
                                        ft.ElevatedButton(
                                            "Registrarse",
                                            bgcolor=ft.Colors.WHITE,
                                            color=ft.Colors.BLACK,
                                            on_click = lambda _: page.go("/registrarse")
                                        ),
                                        ft.Divider(),
                                        ft.Text(
                                            "INICIAR SESIÓN",
                                            size=18,
                                            weight=ft.FontWeight.BOLD
                                        ),
                                        ft.Divider(),
                                        ft.Text(
                                            "Seleccionar rol:",
                                            size = 14,
                                        ),
                                        rol_is,
                                        nombre_is,
                                        password_is,
                                        ft.ElevatedButton(
                                            "Iniciar Sesión",
                                            color=ft.Colors.WHITE,
                                            bgcolor=ft.Colors.GREEN,
                                            on_click = lambda e: iniciar_sesion(e, nombre_is.value, password_is.value, rol_is.value, [nombre_is, password_is])
                                        ),
                                        ft.ElevatedButton(
                                            "Configuración de conexión",
                                            bgcolor=ft.Colors.BLUE,
                                            color=ft.Colors.WHITE,
                                            on_click=lambda _: page.go("/configuracion"),
                                        ),
                                        obtener_logos()
                                    ]
                                )
                            ]
                        ),
                        ft.BottomAppBar(
                            height = 70.0,
                            bgcolor = ft.Colors.GREEN,
                        )
                    ]
                )
            )
            page.update()

            if page.route.startswith("/configuracion"):
                url_input = ft.TextField(
                    label="Dirección del servidor Flask (ej. 127.0.0.1:5001)",
                    value=logica_app.url_api,
                    width=400,
                )

                bbdd_url_input = ft.TextField(
                    label="Dirección de la base de datos MongoDB (ej. mongodb://localhost:27017)",
                    value=logica_app.url_bbdd,
                    width=400,
                )                

                def guardar_url_api(e):
                    res = logica_app.set_url_api(url_input.value.strip())
                    page.client_storage.set("url_api", logica_app.url_api)
                    page.open(ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Configuración guardada"),
                        content=ft.Text(res["message"]),
                        actions=[ft.TextButton("Aceptar", on_click=lambda e: page.go("/"))]
                    ))

                def guardar_url_bbdd(e):
                    res = logica_app.set_url_bbdd(bbdd_url_input.value.strip())
                    page.client_storage.set("url_bbdd", logica_app.url_bbdd)

                    resultado = logica_app.cambiar_url_bbdd()
                    page.open(ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Configuración guardada"),
                        content=ft.Text(res["message"]),
                        actions=[ft.TextButton("Aceptar", on_click=lambda e: page.go("/"))]
                    ))

                page.views.append(
                    ft.View(
                        "/configuracion",
                        [
                            ft.AppBar(
                                title = ft.Text(nombre_app, size = 30, text_align= "end", weight=ft.FontWeight.BOLD),
                                bgcolor=ft.Colors.GREEN,
                                center_title=True,
                                leading=ft.IconButton(
                                    icon=ft.Icons.ARROW_BACK,
                                    icon_color=ft.Colors.BLACK,
                                    on_click=lambda _: page.go("/")
                                )
                            ),
                            ft.Column(
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                expand=True,
                                scroll = ft.ScrollMode.AUTO,
                                controls=[
                                    ft.Divider(),
                                    ft.Text("CONFIGURACIÓN DE CONEXIÓN", size=24, weight=ft.FontWeight.BOLD),
                                    ft.Divider(),
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        vertical_alignment=ft.CrossAxisAlignment.START,
                                        expand=False,
                                        spacing=40,
                                        controls=[
                                            ft.Container(
                                                content=ft.Column(
                                                    alignment=ft.MainAxisAlignment.CENTER,
                                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                    spacing=15,
                                                    controls=[
                                                        ft.Text("Introduce la IP o dominio del servidor Flask:", size=18),
                                                        url_input,
                                                        ft.ElevatedButton(
                                                            text="Guardar",
                                                            bgcolor=ft.Colors.GREEN,
                                                            color=ft.Colors.WHITE,
                                                            on_click=guardar_url_api
                                                        )
                                                    ]
                                                ),
                                                border=ft.border.all(1, ft.Colors.GREY),
                                                padding=20,
                                                border_radius=10,
                                                width=450
                                            ),
                                            ft.Container(
                                                content=ft.Column(
                                                    alignment=ft.MainAxisAlignment.CENTER,
                                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                    spacing=15,
                                                    controls=[
                                                        ft.Text("Introduce la URL de la base de datos MongoDB:", size=18),
                                                        bbdd_url_input,
                                                        ft.ElevatedButton(
                                                            text="Guardar",
                                                            bgcolor=ft.Colors.GREEN,
                                                            color=ft.Colors.WHITE,
                                                            on_click=guardar_url_bbdd
                                                        )
                                                    ]
                                                ),
                                                border=ft.border.all(1, ft.Colors.GREY),
                                                padding=20,
                                                border_radius=10,
                                                width=450
                                            )
                                        ]
                                    ),
                                    ft.Divider(),
                                    ft.Text(
                                        "NOTAS:",
                                        size=18,
                                        weight=ft.FontWeight.BOLD
                                    ),
                                    ft.Text(
                                        "Cambia la direccion IP segun quieras trabajar con el backend central (servidor) o uno local",
                                        size=14,
                                    ),
                                    ft.Text(
                                        "Cambia la URL de la base de datos si quieres usar una en local",
                                        size=14,
                                    )
                                ]
                            ),
                            ft.BottomAppBar(
                                height = 70.0,
                                bgcolor = ft.Colors.GREEN,
                                content = ft.Row(
                                    alignment=ft.MainAxisAlignment.END,
                                )
                            )
                        ]
                    )
                )

            if page.route.startswith("/registrarse"):
                page.views.append(
                    ft.View(
                        "/registrarse",
                        [
                            ft.AppBar(
                                title = ft.Text(nombre_app, size = 30, text_align= "end", weight=ft.FontWeight.BOLD),
                                toolbar_height = 50,
                                bgcolor = ft.Colors.GREEN,
                                center_title = True,
                                automatically_imply_leading = False,
                                leading = ft.IconButton(
                                    icon = ft.Icons.ARROW_BACK,
                                    icon_color = ft.Colors.BLACK,
                                    on_click = view_pop
                                )
                            ),
                            ft.Row(
                                expand = True,
                                alignment = ft.MainAxisAlignment.CENTER,
                                vertical_alignment = ft.CrossAxisAlignment.CENTER,
                                controls = [
                                    ft.Column(
                                        alignment = ft.MainAxisAlignment.CENTER,
                                        horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                                        expand = True,
                                        scroll = ft.ScrollMode.AUTO,
                                        controls = [
                                            ft.Divider(),
                                            ft.Text("REGISTRARSE", size=24, weight=ft.FontWeight.BOLD),
                                            ft.Divider(),
                                            ft.Container(
                                                alignment=ft.alignment.center_left,
                                                padding=ft.padding.only(left=20),
                                                content=ft.Text(
                                                    "Introduzca los datos:",
                                                    size=20,
                                                ),
                                            ),
                                            nombre_r,
                                            password_r_1,
                                            password_r_2,
                                            ft.ElevatedButton(
                                                "Registrarme",
                                                color= ft.Colors.WHITE,
                                                bgcolor = ft.Colors.GREEN,
                                                on_click = lambda e: registrarse(e, nombre_r.value, password_r_1.value, password_r_2.value, [nombre_r, password_r_1, password_r_2])
                                            )
                                        ]
                                    )
                                ]
                            ),
                            ft.BottomAppBar(
                                height = 70.0,
                                bgcolor = ft.Colors.GREEN,
                                content = ft.Row(
                                    alignment=ft.MainAxisAlignment.END,
                                )
                            )
                        ]
                    )
                )

            if page.route == "/main_admin":
                page.views.append(
                    ft.View(
                        "/main_admin",
                        [
                            ft.AppBar(
                                title = ft.Text(nombre_app, size = 30, text_align= "end", weight=ft.FontWeight.BOLD),
                                toolbar_height = 50,
                                bgcolor = ft.Colors.GREEN,
                                center_title = True,
                                automatically_imply_leading = False,
                                leading = ft.IconButton(
                                        icon = ft.Icons.ARROW_BACK,
                                        icon_color = ft.Colors.BLACK,
                                        on_click =lambda _: page.open(alerta_cerrar_sesion)
                                    )
                            ),
                            ft.Row(
                                expand = True,
                                alignment = ft.MainAxisAlignment.CENTER,
                                vertical_alignment = ft.CrossAxisAlignment.CENTER,
                                controls = [
                                    ft.Column(
                                        alignment = ft.MainAxisAlignment.CENTER,
                                        horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                                        expand = True,
                                        spacing = 20,
                                        scroll = ft.ScrollMode.AUTO,
                                        controls = [
                                            ft.Divider(),
                                            ft.Text(
                                                "ADMINISTRADOR - MENÚ",
                                                size=30,
                                                weight=ft.FontWeight.BOLD,
                                                color=ft.Colors.WHITE
                                            ),
                                            ft.Divider(),
                                            ft.Row(
                                                alignment=ft.MainAxisAlignment.CENTER,
                                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                                spacing=30,
                                                controls=[
                                                    # Card Gestión de Usuarios
                                                    ft.Container(
                                                        width=550,
                                                        height=350,
                                                        padding=25,
                                                        border_radius=15,
                                                        border=ft.border.all(2, ft.Colors.GREEN),
                                                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREEN),
                                                        content=ft.Column(
                                                            spacing=12,
                                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                            controls=[
                                                                ft.Icon(
                                                                    name=ft.Icons.PEOPLE,
                                                                    size=40,
                                                                    color=ft.Colors.GREEN,
                                                                ),
                                                                ft.Text(
                                                                    "GESTIÓN DE USUARIOS",
                                                                    size=16,
                                                                    weight=ft.FontWeight.BOLD,
                                                                    color=ft.Colors.WHITE,
                                                                    text_align=ft.TextAlign.CENTER
                                                                ),
                                                                ft.Text(
                                                                    "Busca, edita y administra usuarios del sistema",
                                                                    size=12,
                                                                    color=ft.Colors.GREY_300,
                                                                    text_align=ft.TextAlign.CENTER
                                                                ),
                                                                ft.Divider(height=1),
                                                                ft.Row(
                                                                    alignment=ft.MainAxisAlignment.CENTER,
                                                                    spacing=8,
                                                                    controls=[
                                                                        ft.ElevatedButton(
                                                                            "Ver todos",
                                                                            color=ft.Colors.WHITE,
                                                                            bgcolor=ft.Colors.GREEN,
                                                                            width=90,
                                                                            on_click=lambda _: buscar_usuarios()
                                                                        ),
                                                                        ft.ElevatedButton(
                                                                            "Buscar",
                                                                            color=ft.Colors.WHITE,
                                                                            bgcolor=ft.Colors.GREEN_700,
                                                                            width=90,
                                                                            on_click=lambda _: buscar_usuarios(buscador_nombre_admin.value, buscar_usuario_rol_admin.value)
                                                                        ),
                                                                    ]
                                                                ),
                                                                ft.Column(
                                                                    spacing=6,
                                                                    controls=[
                                                                        ft.Text("Por nombre:", size=10, weight=ft.FontWeight.BOLD),
                                                                        buscador_nombre_admin,
                                                                        ft.Text("Por rol:", size=10, weight=ft.FontWeight.BOLD),
                                                                        buscar_usuario_rol_admin,
                                                                    ]
                                                                ),
                                                            ]
                                                        )
                                                    ),
                                                    # Card Solicitudes de Entrenamiento
                                                    ft.Container(
                                                        width=400,
                                                        height=350,
                                                        padding=25,
                                                        border_radius=15,
                                                        border=ft.border.all(2, ft.Colors.BLUE),
                                                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE),
                                                        content=ft.Column(
                                                            spacing=12,
                                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                            alignment=ft.MainAxisAlignment.SPACE_AROUND,
                                                            controls=[
                                                                ft.Icon(
                                                                    name=ft.Icons.PENDING_ACTIONS,
                                                                    size=40,
                                                                    color=ft.Colors.BLUE,
                                                                ),
                                                                ft.Text(
                                                                    "SOLICITUDES DE ENTRENAMIENTO",
                                                                    size=16,
                                                                    weight=ft.FontWeight.BOLD,
                                                                    color=ft.Colors.WHITE,
                                                                    text_align=ft.TextAlign.CENTER
                                                                ),
                                                                ft.Text(
                                                                    "Gestiona y ejecuta entrenamientos pendientes solicitados por los usuarios",
                                                                    size=12,
                                                                    color=ft.Colors.GREY_300,
                                                                    text_align=ft.TextAlign.CENTER
                                                                ),
                                                                ft.ElevatedButton(
                                                                    text="Ver solicitudes",
                                                                    color=ft.Colors.WHITE,
                                                                    bgcolor=ft.Colors.BLUE,
                                                                    width=280,
                                                                    on_click=lambda _: (mostrar_cargando(page, True), setattr(page, 'route', '/main_admin/entrenamientos'), route_change(page.route))
                                                                ),
                                                            ]
                                                        )
                                                    ),
                                                ]
                                            ),
                                        ]
                                    )
                                ]
                            ),
                            ft.BottomAppBar(
                                height = 70.0,
                                bgcolor = ft.Colors.GREEN,
                                content = ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls= [
                                        ft.IconButton(
                                            icon=ft.Icons.HOME,
                                            icon_color=ft.Colors.WHITE,
                                            icon_size=30,
                                            tooltip="Volver al inicio",
                                            on_click=lambda _: page.open(alerta_cerrar_sesion)
                                        ),
                                        icono_about,
                                        icono_usuario
                                    ]
                                )
                            )
                        ]
                    )
                )
            
            if page.route == "/main_admin/busqueda":
                # Crear tabla vacía
                tabla_usuarios = ft.DataTable(
                    columns = crear_columnas(logica_app.lista_usuarios),
                    rows = []
                )

                usuarios = logica_app.lista_usuarios
                usuarios_por_pagina = 5
                pagina_actual = 0

                # Indicador de página
                indicador_pagina = ft.Text(
                    "Página 1 de 1",
                    size=12,
                    color=ft.Colors.GREY_700,
                    text_align=ft.TextAlign.CENTER
                )

                # Dropdown para elegir filas por página
                dropdown_filas_por_pagina = ft.Dropdown(
                    label="Filas por página:",
                    options=[
                        ft.dropdown.Option("5"),
                        ft.dropdown.Option("7"),
                        ft.dropdown.Option("10"),
                        ft.dropdown.Option("15"),
                        ft.dropdown.Option("20")
                    ],
                    value="5",
                    width=150,
                    on_change=lambda e: cambiar_filas_por_pagina(e)
                )

                # Función para cargar los usuarios de la página actual
                def cargar_pagina():
                    nonlocal pagina_actual
                    inicio = pagina_actual * usuarios_por_pagina
                    fin = inicio + usuarios_por_pagina
                    usuarios_pagina = usuarios[inicio:fin]

                    # Calcular número total de páginas
                    total_paginas = (len(usuarios) + usuarios_por_pagina - 1) // usuarios_por_pagina
                    pagina_mostrada = pagina_actual + 1 if usuarios else 1
                    indicador_pagina.value = f"Página {pagina_mostrada} de {total_paginas}"

                    # Actualizar las filas de la tabla
                    tabla_usuarios.rows.clear()
                    for usuario in usuarios_pagina:
                        celdas = []
                        for campo, val in usuario.items():
                            if campo in ("nombres_antiguos", "rol") and isinstance(val, list):
                                texto = ", ".join(str(v) for v in val) if val else "Ninguno"
                            else:
                                texto = f"{val}"
                            celdas.append(ft.DataCell(ft.Text(texto)))
                        tabla_usuarios.rows.append(
                            ft.DataRow(
                                cells=celdas,
                                on_select_changed=lambda e, nombre=usuario.get("nombre"): seleccionar_usuario(nombre)
                            )
                        )

                    # Actualizar los botones de navegación
                    boton_anterior.disabled = pagina_actual == 0
                    boton_siguiente.disabled = fin >= len(usuarios)
                    page.update()

                # Función para cambiar el número de filas por página
                def cambiar_filas_por_pagina(e):
                    nonlocal pagina_actual, usuarios_por_pagina
                    usuarios_por_pagina = int(dropdown_filas_por_pagina.value)
                    pagina_actual = 0  # Reiniciar a la primera página
                    cargar_pagina()

                # Botones de navegación mejorados
                boton_anterior = ft.ElevatedButton(
                    text="⬆ Filas anteriores",
                    on_click=lambda _: cambiar_pagina(-1),
                    disabled=True,
                    width=150
                )
                boton_siguiente = ft.ElevatedButton(
                    text="Filas siguientes ⬇",
                    on_click=lambda _: cambiar_pagina(1),
                    disabled=len(usuarios) <= usuarios_por_pagina,
                    width=150
                )

                # Función para cambiar de página
                def cambiar_pagina(direccion):
                    nonlocal pagina_actual
                    pagina_actual += direccion
                    cargar_pagina()

                # Parte superior: Botones de navegación y dropdown
                fila_superior = ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        boton_anterior,
                        dropdown_filas_por_pagina,
                        boton_siguiente,
                    ],
                )

                # Indicador de página centrado
                fila_indicador = ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[indicador_pagina]
                )

                # Cargar la primera página
                cargar_pagina()

                page.views.append(
                    ft.View(
                        "/main_admin/busqueda",
                        [
                            ft.AppBar(
                                title = ft.Text(nombre_app, size = 30, text_align= "end", weight=ft.FontWeight.BOLD),
                                toolbar_height = 50,
                                bgcolor = ft.Colors.GREEN,
                                center_title = True,
                                automatically_imply_leading = False,
                                leading = ft.IconButton(
                                        icon = ft.Icons.ARROW_BACK,
                                        icon_color = ft.Colors.BLACK,
                                        on_click = lambda _: (setattr(page, 'route', '/main_admin'), route_change(page.route))
                                    )
                            ),
                            ft.Row(
                                expand = True,
                                alignment = ft.MainAxisAlignment.CENTER,
                                vertical_alignment = ft.CrossAxisAlignment.CENTER,
                                controls = [
                                    ft.Column(
                                        alignment = ft.MainAxisAlignment.CENTER,
                                        horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                                        expand = True,
                                        spacing = 15,
                                        scroll = ft.ScrollMode.AUTO,
                                        controls = [
                                            ft.Container(height=15),
                                            ft.Divider(),
                                            ft.Text(
                                                "RESULTADOS DE BÚSQUEDA",
                                                size=28,
                                                weight=ft.FontWeight.BOLD,
                                                color=ft.Colors.WHITE
                                            ),
                                            ft.Divider(),
                                            fila_superior,
                                            fila_indicador,
                                            ft.Container(
                                                content=ft.Column(
                                                    controls=[tabla_usuarios],
                                                    scroll=ft.ScrollMode.AUTO,
                                                    expand=True,
                                                ),
                                                expand=True,
                                            ),
                                        ]
                                    )
                                ]
                            ),
                            ft.BottomAppBar(
                                height = 70.0,
                                bgcolor = ft.Colors.GREEN,
                                content = ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls= [
                                        ft.IconButton(
                                            icon=ft.Icons.HOME,
                                            icon_color=ft.Colors.WHITE,
                                            icon_size=30,
                                            tooltip="Volver al inicio",
                                            on_click=lambda _: page.open(alerta_cerrar_sesion)
                                        ),
                                        icono_about,
                                        icono_usuario
                                    ]
                                )
                            )
                        ]
                    )
                )
            
            if page.route == "/main_admin/busqueda/datos_usuario":
                page.views.append(
                    ft.View(
                        "/main_admin/busqueda/datos_usuario",
                        [
                            ft.AppBar(
                                title = ft.Text(nombre_app, size = 30, text_align= "end", weight=ft.FontWeight.BOLD),
                                toolbar_height = 50,
                                bgcolor = ft.Colors.GREEN,
                                center_title = True,
                                automatically_imply_leading = False,
                                leading = ft.IconButton(
                                        icon = ft.Icons.ARROW_BACK,
                                        icon_color = ft.Colors.BLACK,
                                        on_click = lambda _: (setattr(page, 'route', '/main_admin'), route_change(page.route))
                                    )
                            ),
                            ft.Row(
                                expand = True,
                                alignment = ft.MainAxisAlignment.CENTER,
                                vertical_alignment = ft.CrossAxisAlignment.CENTER,
                                controls = [
                                    ft.Column(
                                        alignment = ft.MainAxisAlignment.CENTER,
                                        horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                                        expand = True,
                                        spacing = 30,
                                        scroll = ft.ScrollMode.AUTO,
                                        controls = [
                                            ft.Container(height=15),
                                            ft.Divider(),
                                            ft.Text(
                                                "DETALLES DEL USUARIO",
                                                size=28,
                                                weight=ft.FontWeight.BOLD,
                                                color=ft.Colors.WHITE
                                            ),
                                            ft.Divider(height=2),
                                            ft.Row(
                                                alignment=ft.MainAxisAlignment.CENTER,
                                                vertical_alignment=ft.CrossAxisAlignment.START,
                                                spacing=20,
                                                wrap=True,
                                                controls=[
                                                    ft.Container(
                                                        width=450,
                                                        padding=25,
                                                        border_radius=15,
                                                        border=ft.border.all(2, ft.Colors.GREEN),
                                                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREEN),
                                                        content=ft.Column(
                                                            spacing=15,
                                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                            controls=[
                                                                ft.Icon(
                                                                    name=ft.Icons.PERSON,
                                                                    size=40,
                                                                    color=ft.Colors.GREEN,
                                                                ),
                                                                ft.Text(
                                                                    "DATOS DEL USUARIO",
                                                                    size=16,
                                                                    weight=ft.FontWeight.BOLD,
                                                                    color=ft.Colors.WHITE,
                                                                    text_align=ft.TextAlign.CENTER
                                                                ),
                                                                ft.Divider(height=1),
                                                                ft.Container(
                                                                    content=ft.Column(
                                                                        controls=info_usuario_seleccionado(),
                                                                        spacing=8
                                                                    ),
                                                                    padding=10
                                                                ),
                                                                ft.Divider(height=1),
                                                                ft.ElevatedButton(
                                                                    "Borrar usuario",
                                                                    color = ft.Colors.WHITE,
                                                                    bgcolor = ft.Colors.RED,
                                                                    width=200,
                                                                    on_click = lambda _: page.open(alerta_borrar_usuario)
                                                                ),
                                                            ]
                                                        )
                                                    ),
                                                    ft.Container(
                                                        width=450,
                                                        height=285,
                                                        padding=25,
                                                        border_radius=15,
                                                        border=ft.border.all(2, ft.Colors.BLUE),
                                                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE),
                                                        content=ft.Column(
                                                            spacing=15,
                                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                            controls=[
                                                                ft.Icon(
                                                                    name=ft.Icons.SECURITY,
                                                                    size=40,
                                                                    color=ft.Colors.BLUE,
                                                                ),
                                                                ft.Text(
                                                                    "MODIFICAR ROLES",
                                                                    size=16,
                                                                    weight=ft.FontWeight.BOLD,
                                                                    color=ft.Colors.WHITE,
                                                                    text_align=ft.TextAlign.CENTER
                                                                ),
                                                                ft.Divider(height=1),
                                                                ft.Text(
                                                                    "Selecciona un rol:",
                                                                    size=12,
                                                                    color=ft.Colors.GREY_300
                                                                ),
                                                                selector_rol_editar_usuario,
                                                                ft.Row(
                                                                    alignment=ft.MainAxisAlignment.CENTER,
                                                                    spacing=10,
                                                                    controls=[
                                                                        ft.ElevatedButton(
                                                                            "Eliminar rol",
                                                                            color = ft.Colors.WHITE,
                                                                            bgcolor = ft.Colors.RED,
                                                                            width=180,
                                                                            on_click = lambda _: page.open(alerta_eliminar_rol)
                                                                        ),
                                                                        ft.ElevatedButton(
                                                                            "Añadir rol",
                                                                            color = ft.Colors.WHITE,
                                                                            bgcolor = ft.Colors.BLUE,
                                                                            width=180,
                                                                            on_click = lambda _: page.open(alerta_add_rol)
                                                                        )
                                                                    ]
                                                                )
                                                            ]
                                                        )
                                                    ),
                                                ]
                                            ),
                                            ft.Container(height=15),
                                        ]
                                    )
                                ]
                            ),
                            ft.BottomAppBar(
                                height = 70.0,
                                bgcolor =ft.Colors.GREEN,
                                content = ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls= [
                                        ft.IconButton(
                                            icon=ft.Icons.HOME,
                                            icon_color=ft.Colors.WHITE,
                                            icon_size=30,
                                            tooltip="Volver al inicio",
                                            on_click=lambda _: page.open(alerta_cerrar_sesion)
                                        ),
                                        icono_about,
                                        icono_usuario
                                    ]
                                )
                            )
                        ]
                    )
                )
            
            if page.route == "/main_admin/entrenamientos":
                solicitudes = logica_app.obtener_solicitudes_entrenamiento()
                experimentos = logica_app.obtener_experimentos()
                experimentos_por_nombre = {
                    exp.get("nombre"): exp for exp in experimentos if exp.get("nombre")
                }
                modelo_mapeo = {
                    "MobileNet_V2_Weights.DEFAULT": "MobileNetV2"
                }
                
                # Crear Card para cada solicitud
                tarjetas_solicitudes = []
                for solicitud in solicitudes:
                    nombre_experimento = solicitud.get("nombre", "-")
                    usuario_solicitud = solicitud.get("usuario") or "Desconocido"
                    disponible_prediccion = solicitud.get("disponible_prediccion", False)
                    config = experimentos_por_nombre.get(nombre_experimento, {}).get("config") or {}
                    modelo = modelo_mapeo.get(config.get("weights", "-"), config.get("weights", "-"))
                    formato = config.get("formato", "-")
                    fuentes_list = config.get("fuentes", [])
                    if "all" in fuentes_list:
                        fuentes = "Todas"
                    elif fuentes_list:
                        fuentes = ", ".join(fuentes_list)
                    else:
                        fuentes = "Ninguna"
                    
                    # Checkbox para que el admin decida (decisión final)
                    checkbox_admin_prediccion = ft.Checkbox(
                        label="✓ Hacer disponible para predicción",
                        value=disponible_prediccion,  # Pre-marcado según solicitud del usuario
                        label_style=ft.TextStyle(size=12, color=ft.Colors.GREEN_300),
                    )

                    tarjetas_solicitudes.append(
                        ft.Container(
                            width=450,
                            padding=20,
                            border_radius=12,
                            border=ft.border.all(2, ft.Colors.BLUE),
                            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE),
                            content=ft.Column(
                                spacing=10,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Icon(
                                        name=ft.Icons.SCHOOL,
                                        size=35,
                                        color=ft.Colors.BLUE,
                                    ),
                                    ft.Text(
                                        nombre_experimento,
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.WHITE,
                                        text_align=ft.TextAlign.CENTER
                                    ),
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        spacing=4,
                                        wrap=True,
                                        controls=[
                                            ft.Text("Usuario:", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_300),
                                            ft.Text(f"{usuario_solicitud}", size=12, color=ft.Colors.GREY_300),
                                        ]
                                    ),
                                    # Indicador de solicitud del usuario
                                    ft.Container(
                                        content=ft.Row(
                                            alignment=ft.MainAxisAlignment.CENTER,
                                            spacing=6,
                                            controls=[
                                                ft.Icon(
                                                    name=ft.Icons.REQUEST_PAGE if disponible_prediccion else ft.Icons.NOTE_ALT_OUTLINED,
                                                    size=16,
                                                    color=ft.Colors.ORANGE if disponible_prediccion else ft.Colors.GREY_500,
                                                ),
                                                ft.Text(
                                                    "Usuario solicitó disponibilidad para predicción" if disponible_prediccion else "Usuario no solicitó disponibilidad para predicción",
                                                    size=11,
                                                    color=ft.Colors.ORANGE if disponible_prediccion else ft.Colors.GREY_500,
                                                    italic=True,
                                                ),
                                            ]
                                        ),
                                        padding=ft.padding.only(top=4, bottom=4),
                                    ),
                                    ft.Divider(height=1),
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        spacing=12,
                                        wrap=True,
                                        controls=[
                                            ft.Row(
                                                spacing=4,
                                                controls=[
                                                    ft.Text("Modelo:", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_300),
                                                    ft.Text(f"{modelo}", size=12, color=ft.Colors.GREY_300),
                                                ]
                                            ),
                                            ft.Row(
                                                spacing=4,
                                                controls=[
                                                    ft.Text("Formato:", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_300),
                                                    ft.Text(f"{formato}", size=12, color=ft.Colors.GREY_300),
                                                ]
                                            ),
                                            ft.Row(
                                                spacing=4,
                                                controls=[
                                                    ft.Text("Fuentes:", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_300),
                                                    ft.Text(f"{fuentes}", size=12, color=ft.Colors.GREY_300),
                                                ]
                                            ),
                                        ]
                                    ),
                                    # Checkbox para control del admin sobre disponibilidad
                                    checkbox_admin_prediccion,
                                    ft.ElevatedButton(
                                        text="Entrenar",
                                        color=ft.Colors.WHITE,
                                        bgcolor=ft.Colors.ORANGE,
                                        width=180,
                                        on_click=lambda e, nombre=nombre_experimento, checkbox=checkbox_admin_prediccion: (
                                            page.open(
                                                ft.AlertDialog(
                                                    modal=True,
                                                    title=ft.Text("Entrenamiento en progreso"),
                                                    content=ft.Text("El entrenamiento puede tardar un tiempo. Por favor, espere."),
                                                    actions=[],
                                                )
                                            ),
                                            entrenar_modelo(nombre, checkbox.value)
                                        ),
                                    ),
                                ]
                            )
                        )
                    )
                
                # Mensaje si no hay solicitudes
                if not solicitudes:
                    contenido_vista = [
                        ft.Container(height=50),
                        ft.Icon(name=ft.Icons.INBOX, size=80, color=ft.Colors.GREY_300),
                        ft.Text(
                            "No hay solicitudes de entrenamiento",
                            size=18,
                            color=ft.Colors.GREY_300,
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Text(
                            "Las solicitudes pendientes aparecerán aquí",
                            size=12,
                            color=ft.Colors.GREY_400,
                            text_align=ft.TextAlign.CENTER
                        ),
                    ]
                else:
                    contenido_vista = [
                        ft.Container(height=15),
                        ft.Divider(),
                        ft.Text(
                            "SOLICITUDES DE ENTRENAMIENTO",
                            size=26,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE
                        ),
                        ft.Divider(height=2),
                        ft.Container(
                            content=ft.Row(
                                controls=tarjetas_solicitudes,
                                spacing=15,
                                wrap=True,
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            expand=True,
                        ),
                        ft.Container(height=15),
                    ]

                page.views.append(
                    ft.View(
                        "/main_admin/entrenamientos",
                        [
                            ft.AppBar(
                                title=ft.Text(nombre_app, size=30, text_align="end", weight=ft.FontWeight.BOLD),
                                toolbar_height=50,
                                bgcolor=ft.Colors.GREEN,
                                center_title=True,
                                automatically_imply_leading=False,
                                leading=ft.IconButton(
                                    icon=ft.Icons.ARROW_BACK,
                                    icon_color=ft.Colors.BLACK,
                                    on_click=lambda _: (setattr(page, 'route', '/main_admin'), route_change(page.route))
                                )
                            ),
                            ft.Row(
                                expand=True,
                                alignment=ft.MainAxisAlignment.CENTER,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Column(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        expand=True,
                                        spacing=15,
                                        scroll=ft.ScrollMode.AUTO,
                                        controls=contenido_vista
                                    )
                                ]
                            ),
                            ft.BottomAppBar(
                                height = 70.0,
                                bgcolor = ft.Colors.GREEN,
                                content = ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls= [
                                        ft.IconButton(
                                            icon=ft.Icons.HOME,
                                            icon_color=ft.Colors.WHITE,
                                            icon_size=30,
                                            tooltip="Volver al inicio",
                                            on_click=lambda _: page.open(alerta_cerrar_sesion)
                                        ),
                                        icono_about,
                                        icono_usuario
                                    ]
                                )
                            )
                        ]
                    )
                )
                mostrar_cargando(page, False)

            if page.route == "/main_etiquetador":
                page.views.append(
                    ft.View(
                        "/main_etiquetador",
                        [
                            ft.AppBar(
                                title = ft.Text(nombre_app, size = 30, text_align= "end", weight=ft.FontWeight.BOLD),
                                toolbar_height = 50,
                                bgcolor = ft.Colors.GREEN,
                                center_title = True,
                                automatically_imply_leading = False,
                                leading = ft.IconButton(
                                            icon = ft.Icons.ARROW_BACK,
                                            icon_color = ft.Colors.BLACK,
                                            on_click =lambda _: page.open(alerta_cerrar_sesion)
                                        )
                            ),
                            ft.Row(
                                expand=True,
                                alignment=ft.MainAxisAlignment.CENTER,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Column(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        expand=True,
                                        scroll=ft.ScrollMode.AUTO,
                                        spacing=20,
                                        controls=[
                                            ft.Divider(),
                                            ft.Text(
                                                "ETIQUETADOR - MENÚ",
                                                size=30,
                                                weight=ft.FontWeight.BOLD,
                                                color=ft.Colors.WHITE
                                            ),
                                            ft.Divider(),
                                            ft.Container(height=30),
                                            ft.Row(
                                                alignment=ft.MainAxisAlignment.CENTER,
                                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                                spacing=20,
                                                controls=[
                                                    # Card Etiquetar - GREEN
                                                    ft.Container(
                                                        width=400,
                                                        height=280,
                                                        padding=25,
                                                        border_radius=15,
                                                        border=ft.border.all(2, ft.Colors.GREEN),
                                                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREEN),
                                                        content=ft.Column(
                                                            spacing=12,
                                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                            alignment=ft.MainAxisAlignment.SPACE_AROUND,
                                                            controls=[
                                                                ft.Icon(
                                                                    name=ft.Icons.LOCAL_OFFER,
                                                                    size=40,
                                                                    color=ft.Colors.GREEN,
                                                                ),
                                                                ft.Text(
                                                                    "ETIQUETAR / VALIDAR",
                                                                    size=16,
                                                                    weight=ft.FontWeight.BOLD,
                                                                    color=ft.Colors.WHITE,
                                                                    text_align=ft.TextAlign.CENTER
                                                                ),
                                                                ft.Text(
                                                                    "Etiqueta imágenes nuevas o valida las etiquetadas anteriormente",
                                                                    size=12,
                                                                    color=ft.Colors.GREY_300,
                                                                    text_align=ft.TextAlign.CENTER
                                                                ),
                                                                ft.Divider(height=1),
                                                                ft.ElevatedButton(
                                                                    text="Etiquetar imágenes",
                                                                    color=ft.Colors.WHITE,
                                                                    bgcolor=ft.Colors.GREEN,
                                                                    width=280,
                                                                    on_click=lambda _: (mostrar_cargando(page, True), page.go("/main_etiquetador/filtros"))
                                                                ),
                                                            ]
                                                        )
                                                    ),
                                                    # Card Editar Clases - BLUE
                                                    ft.Container(
                                                        width=400,
                                                        height=280,
                                                        padding=25,
                                                        border_radius=15,
                                                        border=ft.border.all(2, ft.Colors.BLUE),
                                                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE),
                                                        content=ft.Column(
                                                            spacing=12,
                                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                            alignment=ft.MainAxisAlignment.SPACE_AROUND,
                                                            controls=[
                                                                ft.Icon(
                                                                    name=ft.Icons.EDIT,
                                                                    size=40,
                                                                    color=ft.Colors.BLUE,
                                                                ),
                                                                ft.Text(
                                                                    "EDITAR CLASES",
                                                                    size=16,
                                                                    weight=ft.FontWeight.BOLD,
                                                                    color=ft.Colors.WHITE,
                                                                    text_align=ft.TextAlign.CENTER
                                                                ),
                                                                ft.Text(
                                                                    "Visualiza y gestiona las clases de plantas y enfermedades disponibles",
                                                                    size=12,
                                                                    color=ft.Colors.GREY_300,
                                                                    text_align=ft.TextAlign.CENTER
                                                                ),
                                                                ft.Divider(height=1),
                                                                ft.ElevatedButton(
                                                                    text="Gestionar clases",
                                                                    color=ft.Colors.WHITE,
                                                                    bgcolor=ft.Colors.BLUE,
                                                                    width=280,
                                                                    on_click=lambda _: (mostrar_cargando(page, True), page.go("/main_etiquetador/editar_clases"))
                                                                ),
                                                            ]
                                                        )
                                                    ),
                                                ]
                                            ),
                                        ]
                                    )
                                ]
                            ),
                            ft.BottomAppBar(
                                height = 70.0,
                                bgcolor = ft.Colors.GREEN,
                                content = ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls= [
                                        ft.IconButton(
                                            icon=ft.Icons.HOME,
                                            icon_color=ft.Colors.WHITE,
                                            icon_size=30,
                                            tooltip="Volver al inicio",
                                            on_click=lambda _: page.open(alerta_cerrar_sesion)
                                        ),
                                        icono_about,
                                        icono_usuario
                                    ]
                                )
                            )
                        ]
                    )
                )

            if page.route == "/main_etiquetador/filtros":
                plantas = logica_app.obtener_opciones_plantas()
                enfermedades = logica_app.obtener_opciones_enfermedades()
                formatos = logica_app.obtener_opciones_formatos()
                fuentes = logica_app.obtener_opciones_fuentes()

                dropdown_planta = ft.Dropdown(label="Planta", options=[ft.dropdown.Option("Cualquiera")] + [ft.dropdown.Option(p) for p in plantas], value="Cualquiera")
                dropdown_enfermedad = ft.Dropdown(label="Enfermedad", options=[ft.dropdown.Option("Cualquiera")] + [ft.dropdown.Option(e) for e in enfermedades], value="Cualquiera")
                dropdown_formato = ft.Dropdown(label="Formato", options=[ft.dropdown.Option("Cualquiera")] + [ft.dropdown.Option(f) for f in formatos], value="Cualquiera")
                dropdown_fuente = ft.Dropdown(label="Fuente", options=[ft.dropdown.Option("Cualquiera")] + [ft.dropdown.Option(f) for f in fuentes], value="Cualquiera")
                dropdown_num_imagenes = ft.Dropdown(
                    label="Número de imágenes por página",
                    options=[ft.dropdown.Option(str(n)) for n in range(1, 6)],
                    value="5"
                )

                dropdown_planta.width = 450
                dropdown_enfermedad.width = 450
                dropdown_formato.width = 450
                dropdown_fuente.width = 450
                dropdown_num_imagenes.width = 450

                page.views.append(
                    ft.View(
                        "/main_etiquetador/filtros",
                        [
                            ft.AppBar(
                                title = ft.Text(nombre_app, size = 30, text_align= "end", weight=ft.FontWeight.BOLD),
                                toolbar_height = 50,
                                bgcolor = ft.Colors.GREEN,
                                center_title = True,
                                automatically_imply_leading = False,
                                leading = ft.IconButton(
                                            icon = ft.Icons.ARROW_BACK,
                                            icon_color = ft.Colors.BLACK,
                                            on_click = lambda _: page.go("/main_etiquetador")
                                        )
                            ),
                            ft.Row(
                                expand=True,
                                alignment=ft.MainAxisAlignment.CENTER,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Column(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        expand=True,
                                        spacing=10,
                                        controls=[
                                            ft.Divider(),
                                            ft.Text("FILTROS", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                            ft.Divider(),
                                            ft.Container(height=5),
                                            ft.Row(
                                                alignment=ft.MainAxisAlignment.CENTER,
                                                spacing=20,
                                                controls=[
                                                    ft.Container(
                                                        width=200,
                                                        padding=8,
                                                        border_radius=8,
                                                        bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.GREEN),
                                                        border=ft.border.all(1.5, ft.Colors.GREEN_200),
                                                        content=dropdown_planta
                                                    ),
                                                    ft.Container(
                                                        width=200,
                                                        padding=8,
                                                        border_radius=8,
                                                        bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.GREEN),
                                                        border=ft.border.all(1.5, ft.Colors.GREEN_200),
                                                        content=dropdown_enfermedad
                                                    ),
                                                    ft.Container(
                                                        width=200,
                                                        padding=8,
                                                        border_radius=8,
                                                        bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.GREEN),
                                                        border=ft.border.all(1.5, ft.Colors.GREEN_200),
                                                        content=dropdown_formato
                                                    ),
                                                ]
                                            ),
                                            ft.Row(
                                                alignment=ft.MainAxisAlignment.CENTER,
                                                spacing=20,
                                                controls=[
                                                    ft.Container(
                                                        width=200,
                                                        padding=8,
                                                        border_radius=8,
                                                        bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.GREEN),
                                                        border=ft.border.all(1.5, ft.Colors.GREEN_200),
                                                        content=dropdown_fuente
                                                    ),
                                                    ft.Container(
                                                        width=200,
                                                        padding=8,
                                                        border_radius=8,
                                                        bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.GREEN),
                                                        border=ft.border.all(1.5, ft.Colors.GREEN_200),
                                                        content=dropdown_num_imagenes
                                                    ),
                                                ]
                                            ),
                                            ft.Container(height=5),
                                            ft.ElevatedButton(
                                                "CARGAR IMÁGENES",
                                                bgcolor=ft.Colors.GREEN,
                                                color=ft.Colors.WHITE,
                                                on_click=aplicar_filtros_handler(page, dropdown_planta, dropdown_enfermedad, dropdown_formato, dropdown_fuente, dropdown_num_imagenes)
                                            )
                                        ],
                                    )
                                ]
                            ),
                            ft.BottomAppBar(
                                height = 70.0,
                                bgcolor = ft.Colors.GREEN,
                                content = ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls= [
                                        ft.IconButton(
                                            icon=ft.Icons.HOME,
                                            icon_color=ft.Colors.WHITE,
                                            icon_size=30,
                                            tooltip="Volver al inicio",
                                            on_click=lambda _: page.open(alerta_cerrar_sesion)
                                        ),
                                        icono_about,
                                        icono_usuario
                                    ]
                                )
                            )
                        ]
                    )
                )
                mostrar_cargando(page, False)

            if page.route.startswith("/main_etiquetador/seleccion_imagenes"):
                """if hasattr(logica_app, "filtros_actuales") and not getattr(logica_app, "evitar_recarga", False):
                    cargar_datos_no_validados()"""
                logica_app.evitar_recarga = False  # Restablecer la bandera después de cargar los datos
                nonlocal boton_anterior_imagenes, boton_siguiente_imagenes

                boton_anterior_imagenes = ft.ElevatedButton(
                    text="Anterior",
                    on_click=lambda _: (mostrar_cargando(page, True), retroceder_imagenes()),
                    bgcolor=ft.Colors.GREEN,
                    color=ft.Colors.WHITE,
                    disabled=logica_app.puntero_repo <= 0,
                )

                boton_siguiente_imagenes = ft.ElevatedButton(
                    text="Siguiente",
                    on_click=lambda _: (mostrar_cargando(page, True), avanzar_imagenes()),
                    bgcolor=ft.Colors.GREEN,
                    color=ft.Colors.WHITE,
                    disabled=len(logica_app.batch_archivos) < logica_app.max_archivos,
                )

                page.views.append(
                    ft.View(
                    "/main_etiquetador/seleccion_imagenes",
                    [
                        ft.AppBar(
                            title = ft.Text(nombre_app, size = 30, text_align= "end", weight=ft.FontWeight.BOLD),
                            toolbar_height = 50,
                            bgcolor = ft.Colors.GREEN,
                            center_title = True,
                            automatically_imply_leading = False,
                            leading = ft.IconButton(
                                        icon = ft.Icons.ARROW_BACK,
                                        icon_color = ft.Colors.BLACK,
                                        on_click = lambda _: page.go("/main_etiquetador")
                                    )
                        ),
                        ft.Row(
                            expand = True,
                            alignment = ft.MainAxisAlignment.CENTER,
                            vertical_alignment = ft.CrossAxisAlignment.CENTER,
                            controls = [
                                ft.Column(
                                    expand = True,
                                    alignment = ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                                    scroll = ft.ScrollMode.AUTO,
                                    spacing = 5,
                                    controls = [
                                        ft.Divider(),
                                        ft.Text(
                                            "SELECCIÓN DE IMÁGENES",
                                            size = 24,
                                            weight = ft.FontWeight.BOLD,
                                            color = ft.Colors.WHITE
                                        ),
                                        ft.Divider(),
                                        ft.Container(
                                            content=ft.Column(
                                                alignment = ft.MainAxisAlignment.START,
                                                horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                                                scroll = ft.ScrollMode.AUTO,
                                                controls = [tabla_docs_no_validados,]
                                            ),
                                            height=400,
                                        ),
                                        ft.Container(height = 10),
                                        ft.Row(
                                            alignment = ft.MainAxisAlignment.CENTER,
                                            vertical_alignment = ft.CrossAxisAlignment.CENTER,
                                            spacing = 20,
                                            controls = [
                                                boton_anterior_imagenes,
                                                boton_siguiente_imagenes,
                                                ft.OutlinedButton(
                                                    text="Volver a filtros",
                                                    style=ft.ButtonStyle(
                                                        color=ft.Colors.BLUE,
                                                        overlay_color=ft.Colors.BLUE_50,
                                                        side=ft.BorderSide(1, ft.Colors.BLUE),
                                                    ),
                                                    on_click=lambda _: (mostrar_cargando(page, True), page.go("/main_etiquetador/filtros"))
                                                ),
                                            ]
                                        ),
                                        ft.Container(height = 10),
                                        ]
                                    )
                                ]
                            ),
                            ft.BottomAppBar(
                                height = 70.0,
                                bgcolor = ft.Colors.GREEN,
                                content = ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls= [
                                        ft.IconButton(
                                            icon=ft.Icons.HOME,
                                            icon_color=ft.Colors.WHITE,
                                            icon_size=30,
                                            tooltip="Volver al inicio",
                                            on_click=lambda _: page.open(alerta_cerrar_sesion)
                                        ),
                                        icono_about,
                                        icono_usuario
                                    ]
                                )
                            )
                        ]
                    )
                )
                actualizar_estado_paginacion_imagenes()

            if page.route.startswith("/main_etiquetador/seleccion_imagenes/etiquetar"):
                # Setup para imagen ampliada
                imagen_ampliada = ft.Image(width=700, height=500, fit=ft.ImageFit.CONTAIN)
                imagen_ampliada_src_base64 = None
                
                def mostrar_imagen_ampliada(img_b64):
                    nonlocal imagen_ampliada_src_base64
                    imagen_ampliada.src = None
                    imagen_ampliada.src_base64 = img_b64
                    imagen_ampliada_src_base64 = img_b64
                    page.dialog = imagen_ampliada_dialog
                    imagen_ampliada_dialog.open = True
                    page.update()

                def cerrar_imagen_ampliada():
                    imagen_ampliada_dialog.open = False
                    page.update()

                imagen_ampliada_dialog = ft.AlertDialog(
                    modal=True,
                    content=ft.Container(
                        content=ft.Column([
                            ft.Container(
                                content=imagen_ampliada,
                                expand=True,
                                margin=ft.margin.only(bottom=10),
                                alignment=ft.alignment.center,
                            ),
                            ft.Row([
                                ft.ElevatedButton(
                                    text="Cerrar",
                                    on_click=lambda _: cerrar_imagen_ampliada(),
                                    bgcolor=ft.Colors.RED,
                                    color=ft.Colors.WHITE,
                                ),
                            ], alignment=ft.MainAxisAlignment.CENTER),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        width=min(page.width * 0.9, 800),
                        height=min(page.height * 0.85, 700),
                        padding=10,
                        alignment=ft.alignment.center,
                    ),
                )
                
                page.views.append(
                    ft.View(
                        "/main_etiquetador/seleccion_imagenes/etiquetar",
                        [
                            ft.AppBar(
                                title = ft.Text(nombre_app, size = 30, text_align= "end", weight=ft.FontWeight.BOLD),
                                toolbar_height = 50,
                                bgcolor = ft.Colors.GREEN,
                                center_title = True,
                                automatically_imply_leading = False,
                                leading = ft.IconButton(
                                        icon = ft.Icons.ARROW_BACK,
                                        icon_color = ft.Colors.BLACK,
                                        on_click = lambda e: (mostrar_cargando(page, True), cargar_datos_no_validados(), page.update(), page.go("/main_etiquetador/seleccion_imagenes"))
                                     )
                            ),
                            ft.Row(
                                expand = True,
                                alignment = ft.MainAxisAlignment.CENTER,
                                vertical_alignment = ft.CrossAxisAlignment.CENTER,
                                controls = [
                                    ft.Column(
                                        expand = True,
                                        alignment = ft.MainAxisAlignment.CENTER,
                                        horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                                        scroll=ft.ScrollMode.AUTO,
                                        spacing = 10,
                                        controls = [
                                           ft.Divider(),
                                           ft.Text(
                                               "ETIQUETAR IMAGEN",
                                               size = 24,
                                               weight = ft.FontWeight.BOLD,
                                               color = ft.Colors.WHITE
                                           ),
                                           ft.Divider(),
                                           ft.Container(
                                               content=ft.Stack(
                                                   controls=[
                                                       ft.Container(
                                                           content=ft.Image(
                                                               src_base64=logica_app.recuperar_imagen_base64(logica_app.archivo_seleccionado["imagen_rgb"]),
                                                               fit=ft.ImageFit.CONTAIN
                                                           ),
                                                           width=400,
                                                           height=300,
                                                           alignment=ft.alignment.center
                                                       ),
                                                       ft.Container(
                                                           content=ft.Icon(
                                                               name=ft.Icons.ZOOM_IN,
                                                               color=ft.Colors.WHITE,
                                                               size=28,
                                                           ),
                                                           alignment=ft.alignment.bottom_right,
                                                           padding=8,
                                                       ),
                                                   ],
                                                   alignment=ft.alignment.center,
                                               ),
                                               alignment=ft.alignment.center,
                                               ink=True,
                                               on_click=lambda _: mostrar_imagen_ampliada(logica_app.recuperar_imagen_base64(logica_app.archivo_seleccionado["imagen_rgb"])),
                                           ),
                                           ft.Divider(),
                                           dropdown_etiquetar,
                                           ft.Row(
                                               alignment = ft.MainAxisAlignment.CENTER,
                                               spacing = 15,
                                               controls = [
                                                   ft.ElevatedButton(
                                                       "Etiquetar",
                                                       on_click=lambda _: etiquetar_imagen(),
                                                       bgcolor = ft.Colors.GREEN,
                                                       color = ft.Colors.WHITE
                                                   ),
                                                   ft.ElevatedButton(
                                                       "Validar",
                                                       bgcolor=ft.Colors.BLUE,
                                                       color=ft.Colors.WHITE,
                                                       on_click=lambda _: validar_imagen_actual()
                                                   ),
                                               ]
                                           ),
                                        ]
                                    )
                                ]
                            ),
                            imagen_ampliada_dialog,
                            ft.BottomAppBar(
                                height = 70.0,
                                bgcolor = ft.Colors.GREEN,
                                content = ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls= [
                                        ft.IconButton(
                                            icon=ft.Icons.HOME,
                                            icon_color=ft.Colors.WHITE,
                                            icon_size=30,
                                            tooltip="Volver al inicio",
                                            on_click=lambda _: page.open(alerta_cerrar_sesion)
                                        ),
                                        icono_about,
                                        icono_usuario
                                    ]
                                )
                            )
                        ]
                    )
                )
                page.update()
                dropdown_etiquetar_options(logica_app.archivo_seleccionado["clase"])
                mostrar_cargando(page, False)

            if page.route.startswith("/main_etiquetador/editar_clases"):
                res = logica_app.obtener_clases()
                if not res.get("success"):
                    page.open(ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Error"),
                        content=ft.Text("No se pudieron cargar las clases desde el servidor."),
                        actions=[ft.TextButton("Aceptar", on_click=lambda e: page.go("/main_etiquetador"))]
                    ))
                    return

                clases = res["clases"]  # Todas las clases
                clases_modificadas = []  # Lista para almacenar los cambios realizados
                clases_por_pagina = 5  # Número de clases por página (valor por defecto)
                pagina_actual = 0  # Índice de la página actual
                clases_filtradas = clases  # Clases después de aplicar el filtro

                # Indicador de página
                indicador_pagina = ft.Text(
                    "Página 1 de 1",
                    size=12,
                    color=ft.Colors.GREY_700,
                    text_align=ft.TextAlign.CENTER
                )

                # Dropdown para los filtros
                dropdown_filtro = ft.Dropdown(
                    label="Mostrar:",
                    options=[
                        ft.dropdown.Option("Todas"),
                        ft.dropdown.Option("Incompletas"),
                        ft.dropdown.Option("Completas")
                    ],
                    value="Todas",
                    on_change=lambda e: aplicar_filtro()
                )

                # Dropdown para elegir filas por página
                dropdown_filas_por_pagina = ft.Dropdown(
                    label="Filas por página:",
                    options=[
                        ft.dropdown.Option("5"),
                        ft.dropdown.Option("7"),
                        ft.dropdown.Option("10"),
                        ft.dropdown.Option("15"),
                        ft.dropdown.Option("20")
                    ],
                    value="5",
                    width=150,
                    on_change=lambda e: cambiar_filas_por_pagina(e)
                )

                tabla_clases = ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("ID")),
                        ft.DataColumn(ft.Text("Planta")),
                        ft.DataColumn(ft.Text("Nombre común")),
                        ft.DataColumn(ft.Text("Clasificación")),
                        ft.DataColumn(ft.Text("Nombre científico")),
                    ],
                    rows=[]
                )

                # Función para aplicar filtros
                def aplicar_filtro():
                    nonlocal clases_filtradas, pagina_actual
                    filtro = dropdown_filtro.value
                    if filtro == "Incompletas":
                        clases_filtradas = [c for c in clases if not c.get("clasificacion") or not c.get("nombre_cientifico")]
                    elif filtro == "Completas":
                        clases_filtradas = [c for c in clases if c.get("clasificacion") and c.get("nombre_cientifico")]
                    else:
                        clases_filtradas = clases

                    pagina_actual = 0  # Reiniciar a la primera página
                    cargar_pagina()

                # Función para cambiar el número de filas por página
                def cambiar_filas_por_pagina(e):
                    nonlocal clases_por_pagina, pagina_actual
                    clases_por_pagina = int(dropdown_filas_por_pagina.value)
                    pagina_actual = 0  # Reiniciar a la primera página
                    cargar_pagina()

                # Función para cargar las clases de la página actual
                def cargar_pagina():
                    nonlocal pagina_actual
                    inicio = pagina_actual * clases_por_pagina
                    fin = inicio + clases_por_pagina
                    clases_pagina = clases_filtradas[inicio:fin]

                    # Calcular número total de páginas
                    total_paginas = (len(clases_filtradas) + clases_por_pagina - 1) // clases_por_pagina
                    pagina_mostrada = pagina_actual + 1 if clases_filtradas else 1
                    indicador_pagina.value = f"Página {pagina_mostrada} de {total_paginas}"

                    # Actualizar las filas de la tabla
                    tabla_clases.rows.clear()
                    for c in clases_pagina:
                        clasif_input = ft.TextField(value=c.get("clasificacion", ""), expand=True)
                        cient_input = ft.TextField(value=c.get("nombre_cientifico", ""), expand=True)

                        # Usar un contenedor para fijar el ancho de las cajas de texto
                        clasif_cell = ft.Container(
                            content=clasif_input,
                            width=150,
                            border=ft.border.all(1, ft.Colors.GREY),  # Borde alrededor de la celda
                        )
                        cient_cell = ft.Container(
                            content=cient_input,
                            width=300,
                            border=ft.border.all(1, ft.Colors.GREY),  # Borde alrededor de la celda
                        )  

                        # Guardar los cambios en la lista temporal
                        clasif_input.on_change = lambda e, cid=c.get("_id"): actualizar_clase(e, "clasificacion", cid)
                        cient_input.on_change = lambda e, cid=c.get("_id"): actualizar_clase(e, "nombre_cientifico", cid)

                        fila = ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Container(content=ft.Text(str(c.get("_id"))))),
                                ft.DataCell(ft.Container(content=ft.Text(c.get("planta", "")))),
                                ft.DataCell(ft.Container(content=ft.Text(c.get("nombre_comun", "")))),
                                ft.DataCell(clasif_cell),
                                ft.DataCell(cient_cell),
                            ]
                        )
                        tabla_clases.rows.append(fila)

                    # Actualizar los botones de navegación
                    boton_anterior.disabled = pagina_actual == 0
                    boton_siguiente.disabled = fin >= len(clases_filtradas)
                    page.update()

                # Función para manejar los cambios en las clases
                def actualizar_clase(e, campo, cid):
                    for c in clases:
                        if c["_id"] == cid:
                            c[campo] = e.control.value
                            if c not in clases_modificadas:
                                clases_modificadas.append(c)
                            break

                # Botones de navegación mejorados
                boton_anterior = ft.ElevatedButton(
                    text="⬆ Filas anteriores",
                    on_click=lambda _: cambiar_pagina(-1),
                    disabled=True,
                    width=150
                )
                boton_siguiente = ft.ElevatedButton(
                    text="Filas siguientes ⬇",
                    on_click=lambda _: cambiar_pagina(1),
                    disabled=len(clases_filtradas) <= clases_por_pagina,
                    width=150
                )

                # Función para cambiar de página
                def cambiar_pagina(direccion):
                    nonlocal pagina_actual
                    pagina_actual += direccion
                    cargar_pagina()

                # Función para guardar los cambios
                def guardar_cambios(e):
                    if not clases_modificadas:
                        page.open(ft.AlertDialog(
                            modal=True,
                            title=ft.Text("Sin cambios"),
                            content=ft.Text("No se ha modificado ninguna clase."),
                            actions=[ft.TextButton("Aceptar", on_click=lambda ev: page.close(ev.control.parent))]
                        ))
                        return

                    res = logica_app.reemplazar_clases(clases)
                    if res.get("success"):
                        page.open(ft.AlertDialog(
                            modal=True,
                            title=ft.Text("Cambios guardados"),
                            content=ft.Text(res.get("message", "Actualización completada.")),
                            actions=[ft.TextButton("Aceptar", on_click=lambda ev: page.go("/main_etiquetador"))]
                        ))
                    else:
                        page.open(ft.AlertDialog(
                            modal=True,
                            title=ft.Text("Error al guardar"),
                            content=ft.Text(res.get("error", "Error desconocido")),
                            actions=[ft.TextButton("Aceptar", on_click=lambda ev: page.close(ev.control.parent))]
                        ))

                # Parte superior: Botones de navegación, filtro y selector de filas
                fila_superior = ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        boton_anterior,
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=20,
                            expand=True,
                            controls=[
                                dropdown_filtro,
                                dropdown_filas_por_pagina,
                            ]
                        ),
                        boton_siguiente,
                    ],
                )

                # Fila de indicador de página
                fila_indicador = ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[indicador_pagina]
                )

                # Parte inferior: Botones "Añadir clase", "Guardar cambios" y "Cancelar"
                fila_inferior = ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.ElevatedButton(
                            text="Cancelar",
                            bgcolor=ft.Colors.RED,
                            color=ft.Colors.WHITE,
                            on_click=lambda _: page.go("/main_etiquetador"),
                        ),
                        ft.ElevatedButton(
                            text="Añadir clase",
                            bgcolor=ft.Colors.BLUE,
                            color=ft.Colors.WHITE,
                            on_click=abrir_dialogo_add_class,
                        ),
                        ft.ElevatedButton(
                            text="Guardar cambios",
                            bgcolor=ft.Colors.GREEN,
                            color=ft.Colors.WHITE,
                            on_click=guardar_cambios,
                        ),
                    ],
                )

                # Cargar la primera página al abrir la vista
                aplicar_filtro()

                # Vista de edición de clases
                page.views.append(
                    ft.View(
                        "/main_etiquetador/editar_clases",
                        [
                            ft.AppBar(
                                title=ft.Text("EDITAR CLASES", size=25, text_align="end", weight=ft.FontWeight.BOLD),
                                bgcolor=ft.Colors.GREEN,
                                center_title=True,
                                leading=ft.IconButton(
                                    icon=ft.Icons.ARROW_BACK,
                                    icon_color=ft.Colors.BLACK,
                                    on_click=lambda _: page.go("/main_etiquetador")
                                )
                            ),
                            ft.Row(
                                expand=True,
                                alignment=ft.MainAxisAlignment.CENTER,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Column(
                                        alignment=ft.MainAxisAlignment.SPACE_AROUND,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        expand=True,
                                        scroll=ft.ScrollMode.AUTO,
                                        controls=[
                                            ft.Container(height=8),
                                            fila_superior,
                                            fila_indicador,
                                            ft.Container(
                                                content=ft.Column(
                                                    controls=[tabla_clases],
                                                    scroll=ft.ScrollMode.AUTO,
                                                    expand=True,
                                                ),
                                            ),
                                            ft.Divider(),
                                            fila_inferior,
                                        ]
                                    )
                                ]
                            ),
                            ft.BottomAppBar(
                                height = 70.0,
                                bgcolor = ft.Colors.GREEN,
                                content = ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls= [
                                        ft.IconButton(
                                            icon=ft.Icons.HOME,
                                            icon_color=ft.Colors.WHITE,
                                            icon_size=30,
                                            tooltip="Volver al inicio",
                                            on_click=lambda _: page.open(alerta_cerrar_sesion)
                                        ),
                                        icono_about,
                                        icono_usuario
                                    ]
                                )
                            )
                        ]
                    )
                )
                mostrar_cargando(page, False)

            if page.route == ("/main_usuario"):
                file_picker = ft.FilePicker(on_result=on_image_selected)
                page.overlay.append(file_picker)

                def open_file_picker(_=None):
                    # Ensure the FilePicker control is attached to the page before invoking pick_files()
                    if file_picker.page is None:
                        page.overlay.append(file_picker)
                        page.update()
                    try:
                        file_picker.pick_files(allow_multiple=False)
                    except AssertionError:
                        # Retry once after ensuring attachment
                        if file_picker.page is None:
                            page.overlay.append(file_picker)
                            page.update()
                        file_picker.pick_files(allow_multiple=False)

                page.views.append(
                    ft.View(
                        "/main_usuario",
                        [
                            ft.AppBar(
                                title=ft.Text(nombre_app, size=30, text_align="end", weight=ft.FontWeight.BOLD),
                                toolbar_height=50,
                                bgcolor=ft.Colors.GREEN,
                                center_title=True,
                                automatically_imply_leading=False,
                                leading=ft.IconButton(
                                    icon=ft.Icons.ARROW_BACK,
                                    icon_color=ft.Colors.BLACK,
                                    on_click=lambda _: page.open(alerta_cerrar_sesion)
                                ),
                            ),
                            ft.Row(
                                expand=True,
                                alignment=ft.MainAxisAlignment.CENTER,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Column(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        expand=True,
                                        spacing=20,
                                        scroll=ft.ScrollMode.AUTO,
                                        controls=[
                                            ft.Divider(),
                                            ft.Text(
                                                "USUARIO - MENÚ",
                                                size=30,
                                                weight=ft.FontWeight.BOLD,
                                                color=ft.Colors.WHITE
                                            ),
                                            ft.Divider(),
                                            ft.Row(
                                                alignment=ft.MainAxisAlignment.CENTER,
                                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                                spacing=30,
                                                controls=[
                                                    # Card Subir Foto - GREEN
                                                    ft.Container(
                                                        width=350,
                                                        height=280,
                                                        padding=25,
                                                        border_radius=15,
                                                        border=ft.border.all(2, ft.Colors.GREEN),
                                                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREEN),
                                                        content=ft.Column(
                                                            spacing=12,
                                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                            alignment=ft.MainAxisAlignment.SPACE_AROUND,
                                                            controls=[
                                                                ft.Icon(
                                                                    name=ft.Icons.PHOTO_CAMERA,
                                                                    size=40,
                                                                    color=ft.Colors.GREEN,
                                                                ),
                                                                ft.Text(
                                                                    "SUBIR FOTO",
                                                                    size=16,
                                                                    weight=ft.FontWeight.BOLD,
                                                                    color=ft.Colors.WHITE,
                                                                    text_align=ft.TextAlign.CENTER
                                                                ),
                                                                ft.Text(
                                                                    "Sube una imagen a la base de datos o predice su clase",
                                                                    size=12,
                                                                    color=ft.Colors.GREY_300,
                                                                    text_align=ft.TextAlign.CENTER
                                                                ),
                                                                ft.Divider(height=1),
                                                                ft.ElevatedButton(
                                                                    text="Seleccionar foto",
                                                                    color=ft.Colors.WHITE,
                                                                    bgcolor=ft.Colors.GREEN,
                                                                    width=280,
                                                                    on_click=open_file_picker
                                                                ),
                                                            ]
                                                        )
                                                    ),
                                                    # Card Experimentos - BLUE
                                                    ft.Container(
                                                        width=350,
                                                        height=280,
                                                        padding=25,
                                                        border_radius=15,
                                                        border=ft.border.all(2, ft.Colors.BLUE),
                                                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE),
                                                        content=ft.Column(
                                                            spacing=12,
                                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                            alignment=ft.MainAxisAlignment.SPACE_AROUND,
                                                            controls=[
                                                                ft.Icon(
                                                                    name=ft.Icons.SCIENCE,
                                                                    size=40,
                                                                    color=ft.Colors.BLUE,
                                                                ),
                                                                ft.Text(
                                                                    "EXPERIMENTOS",
                                                                    size=16,
                                                                    weight=ft.FontWeight.BOLD,
                                                                    color=ft.Colors.WHITE,
                                                                    text_align=ft.TextAlign.CENTER
                                                                ),
                                                                ft.Text(
                                                                    "Explora resultados de experimentos o crea el tuyo propio",
                                                                    size=12,
                                                                    color=ft.Colors.GREY_300,
                                                                    text_align=ft.TextAlign.CENTER
                                                                ),
                                                                ft.Divider(height=1),
                                                                ft.ElevatedButton(
                                                                    text="Ver experimentos",
                                                                    color=ft.Colors.WHITE,
                                                                    bgcolor=ft.Colors.BLUE,
                                                                    width=280,
                                                                    on_click=lambda _: (mostrar_cargando(page, True), page.go("/main_usuario/experimentos"))
                                                                ),
                                                            ]
                                                        )
                                                    ),
                                                    # Card Subida Masiva - ORANGE
                                                    ft.Container(
                                                        width=350,
                                                        height=280,
                                                        padding=25,
                                                        border_radius=15,
                                                        border=ft.border.all(2, ft.Colors.ORANGE),
                                                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.ORANGE),
                                                        content=ft.Column(
                                                            spacing=12,
                                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                            alignment=ft.MainAxisAlignment.SPACE_AROUND,
                                                            controls=[
                                                                ft.Icon(
                                                                    name=ft.Icons.CLOUD_UPLOAD,
                                                                    size=40,
                                                                    color=ft.Colors.ORANGE,
                                                                ),
                                                                ft.Text(
                                                                    "SUBIDA MASIVA",
                                                                    size=16,
                                                                    weight=ft.FontWeight.BOLD,
                                                                    color=ft.Colors.WHITE,
                                                                    text_align=ft.TextAlign.CENTER
                                                                ),
                                                                ft.Text(
                                                                    "Ejecuta la subida masiva de imágenes desde una carpeta específica (solo para Usuarios+)",
                                                                    size=12,
                                                                    color=ft.Colors.GREY_300,
                                                                    text_align=ft.TextAlign.CENTER
                                                                ),
                                                                ft.Divider(height=1),
                                                                ft.ElevatedButton(
                                                                    text="Subir imágenes",
                                                                    color=ft.Colors.WHITE,
                                                                    bgcolor=ft.Colors.ORANGE,
                                                                    width=280,
                                                                    on_click=lambda _: (mostrar_cargando(page, True), page.go("/main_usuario/subida_masiva"))
                                                                ),
                                                            ]
                                                        )
                                                    ),
                                                ]
                                            ),
                                        ]
                                    )
                                ]
                            ),
                            ft.BottomAppBar(
                                height = 70.0,
                                bgcolor = ft.Colors.GREEN,
                                content = ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls= [
                                        ft.IconButton(
                                            icon=ft.Icons.HOME,
                                            icon_color=ft.Colors.WHITE,
                                            icon_size=30,
                                            tooltip="Volver al inicio",
                                            on_click=lambda _: page.open(alerta_cerrar_sesion)
                                        ),
                                        icono_about,
                                        icono_usuario
                                    ]
                                )
                            )
                        ]
                    )
                )
                page.update()

            if page.route == "/main_usuario/foto":
                    imagen_ampliada = ft.Image(width=700, height=500, fit=ft.ImageFit.CONTAIN)

                    def mostrar_imagen_ampliada(img_b64):
                        imagen_ampliada.src_base64 = img_b64
                        page.open(imagen_ampliada_dialog)

                    def cerrar_imagen_ampliada():
                        page.close(imagen_ampliada_dialog)

                    imagen_ampliada_dialog = ft.AlertDialog(
                        modal=True,
                        content=ft.Container(
                            content=ft.Column([
                                ft.Container(
                                    content=imagen_ampliada,
                                    expand=True,
                                    margin=ft.margin.only(bottom=10),
                                    alignment=ft.alignment.center,
                                ),
                                ft.Row([
                                    ft.ElevatedButton(
                                        text="Cerrar",
                                        on_click=lambda _: cerrar_imagen_ampliada(),
                                        bgcolor=ft.Colors.RED,
                                        color=ft.Colors.WHITE,
                                    ),
                                ], alignment=ft.MainAxisAlignment.CENTER),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            width=min(page.width * 0.9, 800),
                            height=min(page.height * 0.85, 700),
                            padding=10,
                            alignment=ft.alignment.center,
                        ),
                    )

                    page.views.append(
                        ft.View(
                            "/main_usuario/foto",
                            [
                                ft.AppBar(
                                    title = ft.Text(nombre_app, size = 30, text_align= "end", weight=ft.FontWeight.BOLD),
                                    toolbar_height = 50,
                                    bgcolor = ft.Colors.GREEN,
                                    center_title = True,
                                    automatically_imply_leading = False,
                                    leading = ft.IconButton(
                                            icon = ft.Icons.ARROW_BACK,
                                            icon_color = ft.Colors.BLACK,
                                            on_click = lambda _: page.go("/main_usuario")
                                        )
                                ),
                                ft.Row(
                                    expand = True,
                                    alignment = ft.MainAxisAlignment.CENTER,
                                    vertical_alignment = ft.CrossAxisAlignment.CENTER,
                                    controls = [
                                            ft.Column(
                                                alignment = ft.MainAxisAlignment.CENTER,
                                                horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                                                expand = True,
                                                spacing = 15,
                                                scroll = ft.ScrollMode.AUTO,
                                                controls = [
                                                    ft.Container(height=10),
                                                    ft.Divider(),
                                                    ft.Text(
                                                        "SUBIR FOTO",
                                                        size=26,
                                                        weight=ft.FontWeight.BOLD,
                                                        color=ft.Colors.WHITE
                                                    ),
                                                    ft.Divider(height=2),
                                                    ft.Row(
                                                        spacing=20,
                                                        wrap=True,
                                                        alignment=ft.MainAxisAlignment.CENTER,
                                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                                        controls=[
                                                            ft.Container(
                                                                width=360,
                                                                padding=20,
                                                                border_radius=15,
                                                                border=ft.border.all(2, ft.Colors.GREEN),
                                                                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREEN),
                                                                content=ft.Stack(
                                                                    controls=[
                                                                        ft.Image(
                                                                            src_base64=logica_app.foto_b64,
                                                                            width=300,
                                                                            height=278,
                                                                            fit=ft.ImageFit.CONTAIN,
                                                                        ),
                                                                        ft.Container(
                                                                            content=ft.Icon(
                                                                                name=ft.Icons.ZOOM_IN,
                                                                                color=ft.Colors.WHITE,
                                                                                size=28,
                                                                            ),
                                                                            alignment=ft.alignment.top_right,
                                                                            padding=8,
                                                                        ),
                                                                    ],
                                                                    alignment=ft.alignment.center,
                                                                ),
                                                                alignment=ft.alignment.center,
                                                                ink=True,
                                                                on_click=lambda _: mostrar_imagen_ampliada(logica_app.foto_b64),
                                                            ),
                                                            ft.Container(
                                                                width=420,
                                                                padding=20,
                                                                border_radius=15,
                                                                border=ft.border.all(2, ft.Colors.BLUE),
                                                                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE),
                                                                content=ft.Column(
                                                                    spacing=16,
                                                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                                    controls=[
                                                                        dropdown_etiquetar,
                                                                        dropdown_formato,
                                                                        ft.Container(height=4),
                                                                        ft.Column(
                                                                            spacing=6,
                                                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                                            controls=[
                                                                                ft.ElevatedButton(
                                                                                    adaptive=True,
                                                                                    bgcolor=ft.Colors.GREEN,
                                                                                    color=ft.Colors.WHITE,
                                                                                    text="SUBIR FOTO",
                                                                                    width=200,
                                                                                    on_click=lambda _: subir_foto()
                                                                                ),
                                                                                ft.Text(
                                                                                    "Guarda la imagen en la base de datos con la etiqueta seleccionada",
                                                                                    size=15,
                                                                                    color=ft.Colors.GREY_300,
                                                                                    text_align=ft.TextAlign.CENTER
                                                                                ),
                                                                            ]
                                                                        ),
                                                                        ft.Divider(height=1),
                                                                        ft.Column(
                                                                            spacing=6,
                                                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                                            controls=[
                                                                                ft.ElevatedButton(
                                                                                    adaptive=True,
                                                                                    bgcolor=ft.Colors.BLUE,
                                                                                    color=ft.Colors.WHITE,
                                                                                    text="PREDECIR CLASE",
                                                                                    width=200,
                                                                                    on_click=lambda _: (mostrar_cargando(page, True), page.go("/main_usuario/prediccion"))
                                                                                ),
                                                                                ft.Text(
                                                                                    "Obtén una predicción sin guardar la imagen en la base de datos",
                                                                                    size=15,
                                                                                    color=ft.Colors.GREY_300,
                                                                                    text_align=ft.TextAlign.CENTER
                                                                                ),
                                                                            ]
                                                                        ),
                                                                    ]
                                                                )
                                                            ),
                                                        ]
                                                    ),
                                                    ft.Container(height=10),
                                                ]
                                        )
                                    ]
                                ),
                                imagen_ampliada_dialog,
                                ft.BottomAppBar(
                                height = 70.0,
                                bgcolor = ft.Colors.GREEN,
                                content = ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls= [
                                        ft.IconButton(
                                            icon=ft.Icons.HOME,
                                            icon_color=ft.Colors.WHITE,
                                            icon_size=30,
                                            tooltip="Volver al inicio",
                                            on_click=lambda _: page.open(alerta_cerrar_sesion)
                                        ),
                                        icono_about,
                                        icono_usuario
                                        ]
                                    )
                                )
                            ]
                        )
                    )
                    page.update()
                    dropdown_etiquetar_options(getattr(logica_app, 'archivo_seleccionado', {}).get('clase') if getattr(logica_app, 'archivo_seleccionado', None) else None)
                    cargar_formatos_dropdown(dropdown_formato)

            if page.route == "/main_usuario/prediccion":
                modelos = logica_app.obtener_modelos()
                experimentos = logica_app.obtener_experimentos()
                plantas = logica_app.obtener_opciones_plantas()

                # Crear un diccionario para búsqueda rápida de experimentos por nombre
                experimentos_dict = {exp["nombre"]: exp for exp in experimentos}

                # Container para mostrar información del experimento
                info_experimento_container = ft.Container(
                    visible=False,
                    padding=15,
                    border=ft.border.all(1, ft.Colors.GREY_400),
                    border_radius=5,
                    width=500,
                    content=ft.Column(
                        spacing=8,
                        controls=[]
                    )
                )

                def actualizar_info_experimento(nombre_modelo):
                    if not nombre_modelo:
                        info_experimento_container.visible = False
                        page.update()
                        return
                    
                    # Extraer nombre del experimento (quitar .pth)
                    nombre_experimento = nombre_modelo.replace(".pth", "")
                    
                    # Buscar el experimento
                    exp = experimentos_dict.get(nombre_experimento)
                    
                    if not exp or not exp.get("config"):
                        info_experimento_container.visible = False
                        page.update()
                        return
                    
                    config = exp["config"]
                    metrics = exp.get("metrics")
                    
                    # Mapeo de modelos
                    modelo_mapeo = {
                        "MobileNet_V2_Weights.DEFAULT": "MobileNetV2"
                    }
                    modelo = modelo_mapeo.get(config.get("weights", ""), config.get("weights", "N/A"))
                    
                    # Procesar información
                    fuentes = config.get("fuentes", [])
                    fuentes_texto = "Todas" if "all" in fuentes else ", ".join(fuentes)
                    
                    plantas_config = config.get("plantas", [])
                    plantas_texto = "Todas" if "all" in plantas_config else ", ".join(plantas_config)
                    
                    enfermedades_config = config.get("enfermedades", [])
                    enfermedades_texto = "Todas" if "all" in enfermedades_config else ", ".join(enfermedades_config)
                    
                    formato = config.get("formato", "N/A")
                    imagenes_por_clase = "Todas" if config.get("imagenes_por_clase") == "all" else str(config.get("imagenes_por_clase", "N/A"))
                    
                    precision_media = "-"
                    if metrics and "test" in metrics and "accuracy_combinada" in metrics["test"]:
                        precision_media = f"{round(metrics['test']['accuracy_combinada'], 4)}"
                    
                    # Actualizar contenido
                    info_experimento_container.content.controls = [
                        ft.Text(f"Información de {nombre_experimento}:", weight=ft.FontWeight.BOLD, size=18),
                        ft.Divider(height=1),
                        ft.Row(wrap=True, controls=[ft.Text("Modelo:", size=16, weight=ft.FontWeight.BOLD), ft.Text(modelo, size=14)]),
                        ft.Row(wrap=True, controls=[ft.Text("Plantas:", size=16, weight=ft.FontWeight.BOLD), ft.Text(plantas_texto, size=14, selectable=True)]),
                        ft.Row(wrap=True, controls=[ft.Text("Enfermedades:", size=16, weight=ft.FontWeight.BOLD), ft.Text(enfermedades_texto, size=14, selectable=True)]),
                        ft.Row(wrap=True, controls=[ft.Text("Fuentes:", size=16, weight=ft.FontWeight.BOLD), ft.Text(fuentes_texto, size=14)]),
                        ft.Row(wrap=True, controls=[ft.Text("Formato:", size=16, weight=ft.FontWeight.BOLD), ft.Text(formato, size=14)]),
                        ft.Row(wrap=True, controls=[ft.Text("Imágenes por clase:", size=16, weight=ft.FontWeight.BOLD), ft.Text(imagenes_por_clase, size=14)]),
                        ft.Row(wrap=True, controls=[ft.Text("Precisión media:", size=16, weight=ft.FontWeight.BOLD), ft.Text(precision_media, size=14)]),
                    ]
                    info_experimento_container.visible = True
                    page.update()

                dropdown_modelo = ft.Dropdown(
                    label="Selecciona el modelo que quieres usar",
                    options=[ft.dropdown.Option(m) for m in modelos],
                    value=modelos[0] if modelos else None,
                    width=500,
                    on_change=lambda e: actualizar_info_experimento(e.control.value),
                    border_color=ft.Colors.WHITE,
                    focused_border_color=ft.Colors.GREEN,
                    label_style=ft.TextStyle(color=ft.Colors.WHITE),
                )

                dropdown_planta = ft.Dropdown(
                    label="Seleccionar planta (si la conoces)",
                    options=[
                        ft.DropdownOption(key=None, text="Ninguna")
                    ] + [
                        ft.DropdownOption(key=planta, text=planta) for planta in logica_app.obtener_opciones_plantas()
                    ],
                    value=None,
                    width=400,
                    border_color=ft.Colors.WHITE,
                    focused_border_color=ft.Colors.GREEN,
                    label_style=ft.TextStyle(color=ft.Colors.WHITE),
                )

                page.views.append(
                    ft.View(
                        "/main_usuario/prediccion",
                        [
                            ft.AppBar(
                                    title = ft.Text(nombre_app, size = 30, text_align= "end", weight=ft.FontWeight.BOLD),
                                    toolbar_height = 50,
                                    bgcolor = ft.Colors.GREEN,
                                    center_title = True,
                                    automatically_imply_leading = False,
                                    leading = ft.IconButton(
                                            icon = ft.Icons.ARROW_BACK,
                                            icon_color = ft.Colors.BLACK,
                                            on_click = lambda _: page.go("/main_usuario/foto")
                                        )
                            ),
                            ft.Row(
                                expand=True,
                                alignment=ft.MainAxisAlignment.CENTER,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Column(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        spacing=10,
                                        scroll=ft.ScrollMode.AUTO,
                                        controls=[
                                            ft.Container(
                                                content=ft.Divider(),
                                                width=400
                                            ),
                                            ft.Text(
                                                "PREDICCIÓN DE IMAGEN",
                                                size=26,
                                                weight=ft.FontWeight.BOLD,
                                                color=ft.Colors.WHITE
                                            ),
                                            ft.Container(
                                                content=ft.Divider(),
                                                width=400
                                            ),
                                            ft.Container(height=12),
                                            ft.Row(
                                                alignment=ft.MainAxisAlignment.CENTER,
                                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                                spacing=20,
                                                controls=[
                                            ft.Container(
                                                width=400,
                                                padding=15,
                                                border_radius=12,
                                                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE),
                                                border=ft.border.all(2, ft.Colors.BLUE),
                                                content=ft.Column(
                                                    alignment=ft.MainAxisAlignment.START,
                                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                    spacing=10,
                                                    controls=[
                                                        dropdown_modelo,
                                                        info_experimento_container,
                                                    ],
                                                ),
                                            ),
                                            ft.Container(
                                                width=400,
                                                padding=15,
                                                border_radius=12,
                                                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREEN),
                                                border=ft.border.all(2, ft.Colors.GREEN),
                                                content=ft.Column(
                                                    alignment=ft.MainAxisAlignment.START,
                                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                    spacing=10,
                                                    controls=[
                                                        ft.Image(
                                                            src_base64=logica_app.foto_b64,
                                                            width=300,
                                                            height=300,
                                                            fit=ft.ImageFit.CONTAIN,
                                                        ),
                                                        dropdown_planta,
                                                    ],
                                                ),
                                            ),
                                            ft.ElevatedButton(
                                                text="REALIZAR PREDICCION",
                                                bgcolor=ft.Colors.GREEN,
                                                color=ft.Colors.WHITE,
                                                width=175,
                                                height=100,
                                                style=ft.ButtonStyle(
                                                    shape=ft.RoundedRectangleBorder(radius=12),
                                                    text_style=ft.TextStyle(size=14, weight=ft.FontWeight.BOLD),
                                                ),
                                                on_click=lambda e: predecir_foto(dropdown_modelo.value, dropdown_planta.value),
                                            ),
                                        ],
                                    ),
                                        ],
                                    ),
                                ],
                            ),
                            ft.BottomAppBar(
                                height = 70.0,
                                bgcolor = ft.Colors.GREEN,
                                content = ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls= [
                                        ft.IconButton(
                                            icon=ft.Icons.HOME,
                                            icon_color=ft.Colors.WHITE,
                                            icon_size=30,
                                            tooltip="Volver al inicio",
                                            on_click=lambda _: page.open(alerta_cerrar_sesion)
                                        ),
                                        icono_about,
                                        icono_usuario
                                    ]
                                )
                            )
                        ],
                    )
                )
                
                # Mostrar info del modelo inicial si hay uno seleccionado
                if modelos:
                    actualizar_info_experimento(modelos[0])
                
                mostrar_cargando(page, False)
                    
            if page.route == "/main_usuario/subida_masiva":
                    if not logica_app.verificar_rol("usuario+"):
                        mostrar_cargando(page, False)
                        page.open(ft.AlertDialog(
                            modal=True,
                            title=ft.Text("Acceso denegado"),
                            content=ft.Text("La subida masiva solo está disponible para usuarios con el rol 'Usuario+'."),
                            actions=[ft.TextButton("Aceptar", on_click=lambda _: page.go("/main_usuario"))]
                        ))
                        return

                    # Texto para mostrar el archivo seleccionado
                    archivo_seleccionado_text = ft.Text(
                        "Sin archivo seleccionado",
                        size=11,
                        color=ft.Colors.GREY_400,
                        italic=True
                    )
                    
                    # Callback para cuando se selecciona un archivo
                    def on_zip_selected(e: ft.FilePickerResultEvent):
                        if e.files:
                            archivo_seleccionado_text.value = f"✓ {e.files[0].name}"
                            archivo_seleccionado_text.color = ft.Colors.GREEN
                            archivo_seleccionado_text.italic = False
                            archivo_seleccionado_text.weight = ft.FontWeight.BOLD
                        else:
                            archivo_seleccionado_text.value = "Sin archivo seleccionado"
                            archivo_seleccionado_text.color = ft.Colors.GREY_400
                            archivo_seleccionado_text.italic = True
                            archivo_seleccionado_text.weight = None
                        page.update()

                    # Controles para PASO 1: Subir ZIP
                    zip_picker = ft.FilePicker(on_result=on_zip_selected)
                    page.overlay.append(zip_picker)

                    def open_zip_picker(_=None):
                        # Ensure the FilePicker control is attached to the page before invoking pick_files()
                        if zip_picker.page is None:
                            page.overlay.append(zip_picker)
                            page.update()
                        try:
                            zip_picker.pick_files(allowed_extensions=["zip"], dialog_title="Selecciona ZIP")
                        except AssertionError:
                            # Retry once after ensuring attachment
                            if zip_picker.page is None:
                                page.overlay.append(zip_picker)
                                page.update()
                            zip_picker.pick_files(allowed_extensions=["zip"], dialog_title="Selecciona ZIP")
                    
                    nombre_fuente_input = ft.TextField(
                        label="Nombre de la fuente",
                        hint_text="Ej: Invernadero2024",
                        width=350
                    )
                    
                    # Controles para PASO 2: Ejecutar subida
                    fuente_dropdown = ft.Dropdown(
                        label="Selecciona una fuente",
                        width=350,
                        options=[]
                    )
                    
                    procesar_switch = ft.Switch(
                        label="Procesar imágenes",
                        value=False
                    )

                    validada_switch = ft.Switch(
                        label="Validar imágenes",
                        value=False
                    )

                    page.views.append(
                        ft.View(
                            "/main_usuario/subida_masiva",
                            [
                                ft.AppBar(
                                    title = ft.Text(nombre_app, size = 30, text_align= "end", weight=ft.FontWeight.BOLD),
                                    toolbar_height = 50,
                                    bgcolor = ft.Colors.GREEN,
                                    center_title = True,
                                    automatically_imply_leading = False,
                                    leading = ft.IconButton(
                                            icon = ft.Icons.ARROW_BACK,
                                            icon_color = ft.Colors.BLACK,
                                            on_click = lambda _: page.go("/main_usuario")
                                    )
                                ),
                                ft.Column(
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    expand=True,
                                    scroll=ft.ScrollMode.AUTO,
                                    spacing=15,
                                    controls=[
                                        ft.Divider(),
                                        ft.Text("SUBIDA MASIVA DE IMÁGENES", size=26, weight=ft.FontWeight.BOLD),
                                        ft.Divider(),
                                        
                                        # Contenedor Row para los dos pasos lado a lado
                                        ft.Row(
                                            alignment=ft.MainAxisAlignment.CENTER,
                                            vertical_alignment=ft.CrossAxisAlignment.START,
                                            spacing=30,
                                            wrap=False,
                                            controls=[
                                                # PASO 1: Subir ZIP
                                                ft.Container(
                                                    width=500,
                                                    height=320,
                                                    padding=20,
                                                    border_radius=10,
                                                    bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.GREEN),
                                                    border=ft.border.all(2, ft.Colors.GREEN),
                                                    content=ft.Column(
                                                        spacing=15,
                                                        controls=[
                                                            ft.Text("PASO 1: Subir ZIP desde tu dispositivo", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
                                                            ft.Text(
                                                                "El ZIP debe contener una carpeta 'color/' con subcarpetas en formato 'Planta___Enfermedad' (ej: Vid___Clorosis)",
                                                                size=11,
                                                                color=ft.Colors.GREY_400
                                                            ),
                                                            ft.Container(
                                                                height=185,
                                                                padding=15,
                                                                border_radius=8,
                                                                border=ft.border.all(1, ft.Colors.WHITE),
                                                                content=ft.Column(
                                                                    spacing=12,
                                                                    controls=[
                                                                        ft.Column(
                                                                            spacing=8,
                                                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                                            controls=[
                                                                                ft.ElevatedButton(
                                                                                    text="Seleccionar ZIP",
                                                                                    icon=ft.Icons.FOLDER_OPEN,
                                                                                    on_click=open_zip_picker
                                                                                ),
                                                                                archivo_seleccionado_text,
                                                                            ]
                                                                        ),
                                                                        nombre_fuente_input,
                                                                        ft.ElevatedButton(
                                                                            text="Subir ZIP",
                                                                            bgcolor=ft.Colors.GREEN,
                                                                            color=ft.Colors.WHITE,
                                                                            width=400,
                                                                            on_click=lambda _: subir_zip(page, logica_app, zip_picker, nombre_fuente_input, fuente_dropdown)
                                                                        )
                                                                    ]
                                                                )
                                                            ),
                                                        ]
                                                    )
                                                ),
                                                
                                                # PASO 2: Configurar subida
                                                ft.Container(
                                                    width=620,
                                                    height=320,
                                                    padding=20,
                                                    border_radius=10,
                                                    bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLUE),
                                                    border=ft.border.all(2, ft.Colors.BLUE),
                                                    content=ft.Column(
                                                        spacing=15,
                                                        controls=[
                                                            ft.Text("PASO 2: Configurar subida a la base de datos", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE),
                                                            ft.Text(
                                                                "Selecciona la fuente y decide cómo guardar la subida.",
                                                                size=11,
                                                                color=ft.Colors.GREY_400
                                                            ),
                                                            ft.Container(
                                                                padding=15,
                                                                border_radius=8,
                                                                border=ft.border.all(1, ft.Colors.WHITE),
                                                                content=ft.Column(
                                                                    spacing=12,
                                                                    controls=[
                                                                        ft.Column(
                                                                            spacing=8,
                                                                            controls=[
                                                                                ft.Text("Selecciona la fuente a subir", size=10, color=ft.Colors.GREY_500),
                                                                                fuente_dropdown
                                                                            ]
                                                                        ),
                                                                        ft.Divider(),
                                                                        ft.Row(
                                                                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                                                            vertical_alignment=ft.CrossAxisAlignment.START,
                                                                            controls=[
                                                                                ft.Container(
                                                                                    width=255,
                                                                                    content=ft.Column(
                                                                                        spacing=6,
                                                                                        controls=[
                                                                                            procesar_switch,
                                                                                            ft.Text(
                                                                                                "Genera imágenes en formato grises y segmentadas.",
                                                                                                size=10,
                                                                                                color=ft.Colors.GREY_500,
                                                                                                italic=True
                                                                                            ),
                                                                                        ]
                                                                                    )
                                                                                ),
                                                                                ft.Container(
                                                                                    width=255,
                                                                                    content=ft.Column(
                                                                                        spacing=6,
                                                                                        controls=[
                                                                                            validada_switch,
                                                                                            ft.Text(
                                                                                                "Activar si estás seguro de que las clases son correctas.",
                                                                                                size=10,
                                                                                                color=ft.Colors.GREY_500,
                                                                                                italic=True
                                                                                            ),
                                                                                        ]
                                                                                    )
                                                                                ),
                                                                            ]
                                                                        ),
                                                                    ]
                                                                )
                                                            ),
                                                        ]
                                                    )
                                                ),
                                            ]
                                        ),
                                        
                                        # Botón Ejecutar Subida centrado y más grande
                                        ft.Container(
                                            padding=10,
                                            content=ft.ElevatedButton(
                                                text="EJECUTAR SUBIDA MASIVA",
                                                icon=ft.Icons.CLOUD_UPLOAD,
                                                bgcolor=ft.Colors.BLUE,
                                                color=ft.Colors.WHITE,
                                                width=350,
                                                height=60,
                                                style=ft.ButtonStyle(
                                                    shape=ft.RoundedRectangleBorder(radius=10),
                                                    text_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD),
                                                ),
                                                on_click=lambda _: ejecutar_subida_masiva(page, logica_app, fuente_dropdown, procesar_switch, validada_switch)
                                            )
                                        ),
                                    ]
                                ),
                                ft.BottomAppBar(
                                    height=70.0,
                                    bgcolor=ft.Colors.GREEN,
                                    content=ft.Row(
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        controls=[
                                            ft.IconButton(
                                                icon=ft.Icons.HOME,
                                                icon_color=ft.Colors.WHITE,
                                                icon_size=30,
                                                tooltip="Volver al inicio",
                                                on_click=lambda _: page.open(alerta_cerrar_sesion)
                                            ),
                                            icono_about,
                                            icono_usuario,
                                        ]
                                    )
                                )
                            ]
                        )
                    )

                    mostrar_cargando(page, False)
                    page.update()

                    # Cargar dropdown de fuentes al abrir la vista
                    cargar_fuentes_dropdown(fuente_dropdown)

            if page.route == "/main_usuario/experimentos":
                    tabla_experimentos = ft.DataTable(
                        columns=[
                            ft.DataColumn(ft.Text("Nombre")),
                            ft.DataColumn(ft.Text("Modelo")),
                            ft.DataColumn(ft.Text("Plantas")),
                            ft.DataColumn(ft.Text("Enfermedades")),
                            ft.DataColumn(ft.Text("Fuentes")),
                            ft.DataColumn(ft.Text("Formato")),
                            ft.DataColumn(ft.Text("Imágenes por clase")),
                            ft.DataColumn(ft.Text("Precisión media")),
                            ft.DataColumn(ft.Text("Acciones")),
                        ],
                        rows=[]
                    )

                    experimentos = logica_app.obtener_experimentos()

                    modelo_mapeo = {
                        "MobileNet_V2_Weights.DEFAULT": "MobileNetV2"
                    }

                    experimentos_por_pagina = 5
                    pagina_actual = 0

                    # Indicador de página
                    indicador_pagina = ft.Text(
                        "Página 1 de 1",
                        size=12,
                        color=ft.Colors.GREY_700,
                        text_align=ft.TextAlign.CENTER
                    )

                    # Dropdown para elegir filas por página
                    dropdown_filas_por_pagina = ft.Dropdown(
                        label="Filas por página:",
                        options=[
                            ft.dropdown.Option("5"),
                            ft.dropdown.Option("7"),
                            ft.dropdown.Option("10"),
                            ft.dropdown.Option("15"),
                            ft.dropdown.Option("20")
                        ],
                        value="5",
                        width=150,
                        on_change=lambda e: cambiar_filas_por_pagina(e)
                    )

                    def mostrar_lista_dialogo(lista, titulo):
                        min_height = 80
                        max_height = 400
                        item_height = 12
                        height = min(max_height, max(min_height, len(lista) * item_height + 40))
                        dialogo = ft.AlertDialog(
                            modal=True,
                            title=ft.Text(titulo),
                            content=ft.Column([
                                ft.Text("\n".join(lista) if lista else "(Vacío)")
                            ], scroll=ft.ScrollMode.AUTO, width=350, height=height),
                            actions=[ft.TextButton("Cerrar", on_click=lambda e: page.close(dialogo))]
                        )
                        page.open(dialogo)

                    def cargar_pagina():
                        nonlocal pagina_actual
                        inicio = pagina_actual * experimentos_por_pagina
                        fin = inicio + experimentos_por_pagina
                        experimentos_pagina = experimentos[inicio:fin]

                        # Calcular número total de páginas
                        total_paginas = (len(experimentos) + experimentos_por_pagina - 1) // experimentos_por_pagina
                        pagina_mostrada = pagina_actual + 1 if experimentos else 1
                        indicador_pagina.value = f"Página {pagina_mostrada} de {total_paginas}"

                        # Actualizar las filas de la tabla
                        tabla_experimentos.rows.clear()
                        for exp in experimentos_pagina:
                            nombre = exp["nombre"]
                            config = exp.get("config") or {}
                            metrics = exp.get("metrics")

                            if nombre == "BASE" or not config:
                                fila = ft.DataRow(
                                    cells=[
                                        ft.DataCell(ft.Text("BASE (Plantilla)")),
                                        ft.DataCell(ft.Text("-")),
                                        ft.DataCell(ft.Text("-")),
                                        ft.DataCell(ft.Text("-")),
                                        ft.DataCell(ft.Text("-")),
                                        ft.DataCell(ft.Text("-")),
                                        ft.DataCell(ft.Text("-")),
                                        ft.DataCell(ft.Text("-")),
                                        ft.DataCell(ft.Text("-")),
                                    ]
                                )
                                tabla_experimentos.rows.append(fila)
                                continue

                            modelo = modelo_mapeo.get(config.get("weights", ""), config.get("weights", "-"))
                            fuentes = ", ".join(config.get("fuentes", []))
                            if "all" in config.get("fuentes", []):
                                fuentes = "Todas"
                            imagenes_por_clase = "Todas" if config.get("imagenes_por_clase") == "all" else config.get("imagenes_por_clase", "-")
                            formato = config.get("formato", "-")

                            # Plantas
                            if "all" in config.get("plantas", []):
                                celda_plantas = ft.DataCell(ft.Text("Todas"))
                            else:
                                lista_plantas = config.get("plantas", [])
                                celda_plantas = ft.DataCell(
                                    ft.TextButton(
                                        text="Específicas",
                                        style=ft.ButtonStyle(color=ft.Colors.BLUE),
                                        on_click=lambda e, lp=lista_plantas: mostrar_lista_dialogo(lp, "Plantas específicas")
                                    )
                                )

                            # Enfermedades
                            if "all" in config.get("enfermedades", []):
                                celda_enfermedades = ft.DataCell(ft.Text("Todas"))
                            else:
                                lista_enfermedades = config.get("enfermedades", [])
                                celda_enfermedades = ft.DataCell(
                                    ft.TextButton(
                                        text="Específicas",
                                        style=ft.ButtonStyle(color=ft.Colors.BLUE),
                                        on_click=lambda e, le=lista_enfermedades: mostrar_lista_dialogo(le, "Enfermedades específicas")
                                    )
                                )

                            if metrics and "test" in metrics and "accuracy_combinada" in metrics["test"]:
                                precision_media = round(metrics["test"]["accuracy_combinada"], 4)
                            else:
                                precision_media = "-"

                            fila = ft.DataRow(
                                cells=[
                                    ft.DataCell(ft.Text(nombre)),
                                    ft.DataCell(ft.Text(modelo)),
                                    celda_plantas,
                                    celda_enfermedades,
                                    ft.DataCell(ft.Text(fuentes)),
                                    ft.DataCell(ft.Text(formato)),
                                    ft.DataCell(ft.Text(str(imagenes_por_clase))),
                                    ft.DataCell(ft.Text(str(precision_media))),
                                    ft.DataCell(
                                        ft.ElevatedButton(
                                            text="Ver resultados",
                                            on_click=lambda e, nombre=nombre: (mostrar_cargando(page, True), page.go(f"/main_usuario/experimentos/{nombre}"))
                                        )
                                    ),
                                ]
                            )
                            tabla_experimentos.rows.append(fila)

                        # Actualizar los botones de navegación
                        boton_anterior.disabled = pagina_actual == 0
                        boton_siguiente.disabled = fin >= len(experimentos)
                        page.update()

                    # Función para cambiar el número de filas por página
                    def cambiar_filas_por_pagina(e):
                        nonlocal pagina_actual, experimentos_por_pagina
                        experimentos_por_pagina = int(dropdown_filas_por_pagina.value)
                        pagina_actual = 0  # Reiniciar a la primera página
                        cargar_pagina()

                    # Botones de navegación mejorados
                    boton_anterior = ft.ElevatedButton(
                        text="⬆ Filas anteriores",
                        on_click=lambda _: cambiar_pagina(-1),
                        disabled=True,
                        width=150
                    )
                    boton_siguiente = ft.ElevatedButton(
                        text="Filas siguientes ⬇",
                        on_click=lambda _: cambiar_pagina(1),
                        disabled=len(experimentos) <= experimentos_por_pagina,
                        width=150
                    )

                    # Función para cambiar de página
                    def cambiar_pagina(direccion):
                        nonlocal pagina_actual
                        pagina_actual += direccion
                        cargar_pagina()

                    # Parte superior: Botones de navegación y dropdown
                    fila_superior = ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            boton_anterior,
                            dropdown_filas_por_pagina,
                            boton_siguiente,
                        ],
                    )

                    # Indicador de página centrado
                    fila_opciones = ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[indicador_pagina]
                    )

                    # Cargar la primera página
                    cargar_pagina()

                    page.views.append(
                        ft.View(
                            "/main_usuario/experimentos",
                            [
                                ft.AppBar(
                                    title = ft.Text("EXPERIMENTOS", size = 30, text_align= "center", weight=ft.FontWeight.BOLD),
                                    toolbar_height = 50,
                                    bgcolor = ft.Colors.GREEN,
                                    center_title = True,
                                    automatically_imply_leading = False,
                                    leading = ft.IconButton(
                                            icon = ft.Icons.ARROW_BACK,
                                            icon_color = ft.Colors.BLACK,
                                            on_click = lambda _: page.go("/main_usuario")
                                    )
                                ),
                                ft.Column(
                                    alignment=ft.MainAxisAlignment.START,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    expand=True,
                                    controls=[
                                        ft.Container(height=10),
                                        fila_superior,
                                        fila_opciones,
                                        ft.Divider(),
                                        ft.Container(
                                            content=ft.Column(
                                                controls=[
                                                    ft.Container(
                                                        content=tabla_experimentos,
                                                        expand=True,
                                                    ),
                                                ],
                                                scroll=ft.ScrollMode.AUTO,
                                                expand=True,
                                            ),
                                            expand=True,
                                            height=600,
                                        ),
                                        ft.Divider(),
                                        ft.Row(
                                            alignment=ft.MainAxisAlignment.CENTER,
                                            spacing=10,
                                            controls=[
                                                ft.ElevatedButton(
                                                    text="Crear Nuevo Experimento",
                                                    on_click=lambda _: (mostrar_cargando(page, True), page.go("/main_usuario/experimentos/crear")),
                                                    bgcolor=ft.Colors.GREEN,
                                                    color=ft.Colors.WHITE,
                                                ),
                                                ft.ElevatedButton(
                                                    text="Comparar Experimentos",
                                                    on_click=lambda _: (mostrar_cargando(page, True), page.go("/main_usuario/experimentos/comparar")),
                                                    bgcolor=ft.Colors.BLUE,
                                                    color=ft.Colors.WHITE,
                                                ),
                                            ],
                                        ),
                                        ft.Container(height=10),
                                    ],
                                ),
                                ft.BottomAppBar(
                                height = 70.0,
                                bgcolor = ft.Colors.GREEN,
                                content = ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls= [
                                        ft.IconButton(
                                            icon=ft.Icons.HOME,
                                            icon_color=ft.Colors.WHITE,
                                            icon_size=30,
                                            tooltip="Volver al inicio",
                                            on_click=lambda _: page.open(alerta_cerrar_sesion)
                                        ),
                                        icono_about,
                                        icono_usuario
                                        ]
                                    )
                                )
                            ],
                        )
                    )
                    mostrar_cargando(page, False)

            if page.route == "/main_usuario/experimentos/crear":
                respuesta_filtros_docs = logica_app.obtener_opciones_filtros_docs()
                filtros_multiseleccion = {}
                formato_opciones = []
                mapeos_ids = {}

                if isinstance(respuesta_filtros_docs, dict) and respuesta_filtros_docs.get("success"):
                    filtros_multiseleccion = respuesta_filtros_docs.get("filtros_multiseleccion", {})
                    formato_opciones = respuesta_filtros_docs.get("formato_opciones", [])
                    mapeos_ids = respuesta_filtros_docs.get("mapeos_ids", {})

                # Fallback por compatibilidad si el endpoint nuevo no devuelve datos.
                if not isinstance(filtros_multiseleccion, dict) or not filtros_multiseleccion:
                    filtros_multiseleccion = {
                        "planta": logica_app.obtener_opciones_plantas(),
                        "nombre_comun": [e for e in logica_app.obtener_opciones_enfermedades() if e != "Sin_clasificar"],
                        "fuente": logica_app.obtener_opciones_fuentes(),
                    }

                if not formato_opciones:
                    formato_opciones = logica_app.obtener_opciones_formatos()

                modelos = logica_app.obtener_opciones_modelos()

                # Estado de seleccion dinamica por campo de Docs.
                selecciones_filtros = {}
                for campo, valores in filtros_multiseleccion.items():
                    valores_limpios = [v for v in valores if v is not None and str(v).strip() != ""]
                    if campo == "nombre_comun":
                        valores_limpios = [v for v in valores_limpios if str(v) != "Sin_clasificar"]
                    filtros_multiseleccion[campo] = ["all"] + valores_limpios
                    selecciones_filtros[campo] = ["all"]

                def nombre_campo_ui(campo):
                    if campo == "nombre_comun":
                        return "Enfermedad"
                    return str(campo).replace("_", " ").title()

                def abrir_modal_seleccion(campo):
                    opciones = filtros_multiseleccion.get(campo, ["all"])
                    titulo = f"Seleccionar {nombre_campo_ui(campo)}"
                    seleccion_actual = selecciones_filtros.get(campo, ["all"])

                    # Crear checkboxes con "Todas" en lugar de "all"
                    checkboxes = []
                    
                    def on_checkbox_change(e, cb_actual):
                        # Si se marca "Todas", desmarcar todas las demás
                        if cb_actual.data == "all" and cb_actual.value:
                            for cb in checkboxes:
                                if cb.data != "all":
                                    cb.value = False
                        # Si se marca cualquier otra opción, desmarcar "Todas"
                        elif cb_actual.data != "all" and cb_actual.value:
                            for cb in checkboxes:
                                if cb.data == "all":
                                    cb.value = False
                        page.update()
                    
                    for opcion in opciones:
                        label_mostrar = "Todas" if opcion == "all" else opcion
                        cb = ft.Checkbox(
                            label=str(label_mostrar),
                            value=(opcion in seleccion_actual),
                            data=opcion  # Guardar el valor real en data
                        )
                        cb.on_change = lambda e, checkbox=cb: on_checkbox_change(e, checkbox)
                        checkboxes.append(cb)

                    def confirmar_seleccion(e):
                        # Usar el valor real (data) en lugar del label
                        seleccionadas = [cb.data for cb in checkboxes if cb.value]
                        if not seleccionadas:
                            seleccionadas = ["all"]
                        selecciones_filtros[campo] = seleccionadas
                        actualizar_textos_seleccion()
                        page.close(modal_seleccion)

                    modal_seleccion = ft.AlertDialog(
                        modal=True,
                        title=ft.Text(titulo),
                        content=ft.Column(controls=checkboxes, scroll=ft.ScrollMode.AUTO),
                        actions=[
                            ft.TextButton("Cancelar", on_click=lambda _: page.close(modal_seleccion)),
                            ft.TextButton("Confirmar", on_click=confirmar_seleccion),
                        ],
                    )
                    page.open(modal_seleccion)

                textos_filtros_seleccionados = {
                    campo: ft.Text(f"{nombre_campo_ui(campo)} seleccionadas: Todas")
                    for campo in sorted(filtros_multiseleccion.keys())
                }

                def actualizar_textos_seleccion():
                    for campo, texto in textos_filtros_seleccionados.items():
                        seleccion = selecciones_filtros.get(campo, ["all"])
                        valores_mostrar = ["Todas" if v == "all" else str(v) for v in seleccion]
                        texto.value = f"{nombre_campo_ui(campo)} seleccionadas: {', '.join(valores_mostrar) or 'Ninguna'}"
                    page.update()

                botones_filtros = {
                    campo: ft.ElevatedButton(
                        text=f"Seleccionar {nombre_campo_ui(campo)}",
                        on_click=lambda _, c=campo: abrir_modal_seleccion(c),
                    )
                    for campo in sorted(filtros_multiseleccion.keys())
                }

                controles_filtros_dinamicos = []
                for campo in sorted(filtros_multiseleccion.keys()):
                    controles_filtros_dinamicos.append(botones_filtros[campo])
                    controles_filtros_dinamicos.append(textos_filtros_seleccionados[campo])
                    controles_filtros_dinamicos.append(ft.Divider(height=1))

                if not controles_filtros_dinamicos:
                    controles_filtros_dinamicos = [
                        ft.Text("No hay filtros de Docs disponibles en este momento.", color=ft.Colors.YELLOW_200)
                    ]

                input_nombre_experimento = ft.TextField(
                    label="Nombre del experimento",
                    hint_text="Introduce un nombre único para el experimento",
                    border=ft.InputBorder.OUTLINE,
                    border_color=ft.Colors.WHITE,
                )
                dropdown_formato = ft.Dropdown(
                    label="Formato",
                    options=[ft.dropdown.Option(fmt) for fmt in formato_opciones],
                    value=formato_opciones[0] if formato_opciones else None,
                    border_color=ft.Colors.WHITE,
                )
                dropdown_modelo = ft.Dropdown(
                    label="Modelo",
                    options=[ft.dropdown.Option(m) for m in modelos],
                    value=modelos[0] if modelos else None,
                    border_color=ft.Colors.WHITE,
                )
                dropdown_num_imagenes = ft.Dropdown(
                    label="Nº de imágenes por clase",
                    options=[
                        ft.dropdown.Option("50", text="50"),
                        ft.dropdown.Option("100", text="100"),
                        ft.dropdown.Option("500", text="500"),
                        ft.dropdown.Option("Todas", text="Todas"),
                    ],
                    value="50",
                    border_color=ft.Colors.WHITE,
                )
                
                checkbox_disponible_prediccion = ft.Checkbox(
                    label="Quiero que este modelo esté disponible para predecir",
                    value=False,
                    disabled=True,  # Deshabilitado por defecto
                )

                checkbox_solo_validadas = ft.Checkbox(
                    label="Usar solo imágenes validadas",
                    value=False,
                    disabled=True,
                )
                
                def on_entrenar_change(e):
                    """Habilita/deshabilita los checkboxes dependientes según el estado de entrenar"""
                    checkbox_disponible_prediccion.disabled = not e.control.value
                    checkbox_solo_validadas.disabled = not e.control.value
                    if not e.control.value:
                        checkbox_disponible_prediccion.value = False
                        checkbox_solo_validadas.value = False
                    page.update()
                
                checkbox_entrenar_modelo = ft.Checkbox(
                    label="Quiero entrenar este modelo",
                    value=False,
                    on_change=on_entrenar_change,
                )

                def construir_config_experimento():
                    """Construye config con valores legibles (nombres) incluyendo todos los campos dinámicos."""
                    config = {
                        "formato": dropdown_formato.value,
                        "imagenes_por_clase": int(dropdown_num_imagenes.value) if dropdown_num_imagenes.value != "Todas" else dropdown_num_imagenes.value,
                        "modelo": dropdown_modelo.value,
                        "solo_validadas": checkbox_solo_validadas.value,
                    }
                    
                    # Añadir todos los campos dinámicos seleccionados.
                    for campo, seleccion in selecciones_filtros.items():
                        # Mapeo de nombres internos a nombres de config (compatibilidad).
                        nombre_config = campo
                        if campo == "nombre_comun":
                            nombre_config = "enfermedades"
                        elif campo == "planta":
                            nombre_config = "plantas"
                        elif campo == "fuente":
                            nombre_config = "fuentes"
                        
                        config[nombre_config] = seleccion
                    
                    return config

                boton_crear_experimento = ft.ElevatedButton(
                    text="Crear Experimento",
                    on_click=lambda _: crear_experimento(
                        input_nombre_experimento.value,
                        construir_config_experimento(),
                        checkbox_entrenar_modelo.value,
                        checkbox_disponible_prediccion.value,
                        page,
                    ),
                    bgcolor=ft.Colors.BLUE,
                    color=ft.Colors.WHITE,
                )
                page.views.append(
                    ft.View(
                        "/main_usuario/experimentos/crear",
                        [
                            ft.AppBar(
                            title = ft.Text(nombre_app, size = 30, text_align= "end", weight=ft.FontWeight.BOLD),
                                toolbar_height = 50,
                                bgcolor = ft.Colors.GREEN,
                                center_title = True,
                                automatically_imply_leading = False,
                                leading = ft.IconButton(
                                        icon = ft.Icons.ARROW_BACK,
                                        icon_color = ft.Colors.BLACK,
                                        on_click = lambda _: page.go("/main_usuario/experimentos")
                                )
                            ),
                            ft.Row(
                                expand=True,
                                alignment=ft.MainAxisAlignment.CENTER,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Column(
                                        expand=True,
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        spacing=15,
                                        scroll=ft.ScrollMode.AUTO,
                                        controls=[
                                    ft.Column(
                                        spacing=8,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        controls=[
                                            ft.Text("NOMBRE DEL NUEVO EXPERIMENTO", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                            ft.Container(
                                                width=550,
                                                content=input_nombre_experimento,
                                            ),
                                            ft.Text(
                                                "Asigna un nombre único para identificar tu experimento. Evita usar caracteres especiales y espacios al inicio o final.",
                                                size=10,
                                                color=ft.Colors.YELLOW_200,
                                                italic=True
                                            ),
                                        ]
                                    ),
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        vertical_alignment=ft.CrossAxisAlignment.START,
                                        spacing=30,
                                        controls=[
                                            # Columna Izquierda - Datasets
                                            ft.Container(
                                                width=350,
                                                padding=20,
                                                height=420,
                                                border_radius=15,
                                                border=ft.border.all(2, ft.Colors.GREEN),
                                                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREEN),
                                                content=ft.Column(
                                                    spacing=12,
                                                    controls=[
                                                        ft.Text("📊 SELECCIÓN DE DATOS", size=15, weight=ft.FontWeight.BOLD),
                                                        ft.Divider(height=1),
                                                        ft.Text(
                                                            "Desplaza hacia abajo para ver más filtros",
                                                            size=10,
                                                            color=ft.Colors.GREEN_200,
                                                            italic=True,
                                                        ),
                                                        ft.Container(
                                                            height=290,
                                                            content=ft.Column(
                                                                spacing=12,
                                                                scroll=ft.ScrollMode.ALWAYS,
                                                                controls=controles_filtros_dinamicos,
                                                            ),
                                                        ),
                                                    ]
                                                )
                                            ),
                                            # Columna Derecha - Configuración
                                            ft.Container(
                                                width=420,
                                                padding=20,
                                                height=420,
                                                border_radius=15,
                                                border=ft.border.all(2, ft.Colors.BLUE),
                                                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE),
                                                content=ft.Column(
                                                    spacing=12,
                                                    controls=[
                                                        ft.Text("⚙️ CONFIGURACIÓN", size=15, weight=ft.FontWeight.BOLD),
                                                        ft.Divider(height=1),
                                                        ft.Row(controls=[dropdown_formato, dropdown_num_imagenes], spacing=20),
                                                        dropdown_modelo,
                                                        ft.Divider(height=1),
                                                        checkbox_entrenar_modelo,
                                                        checkbox_disponible_prediccion,
                                                        checkbox_solo_validadas,
                                                        ft.Container(height=5),
                                                        boton_crear_experimento,
                                                    ]
                                                )
                                            ),
                                        ]
                                    ),
                                ],
                                    ),
                                ]
                            ),
                            ft.BottomAppBar(
                                height = 70.0,
                                bgcolor = ft.Colors.GREEN,
                                content = ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls= [
                                        ft.IconButton(
                                            icon=ft.Icons.HOME,
                                            icon_color=ft.Colors.WHITE,
                                            icon_size=30,
                                            tooltip="Volver al inicio",
                                            on_click=lambda _: page.open(alerta_cerrar_sesion)
                                        ),
                                        icono_about,
                                        icono_usuario
                                    ]
                                )
                            )
                        ],
                    )
                )
                mostrar_cargando(page, False)
            
            if page.route == "/main_usuario/experimentos/comparar":
                experimentos = logica_app.obtener_experimentos()

                seleccionados = []
                cards_experimentos = []
                
                # Texto contador de seleccionados
                texto_contador = ft.Text(
                    "0 experimentos seleccionados",
                    size=16,
                    color=ft.Colors.WHITE,
                    weight=ft.FontWeight.BOLD
                )

                def actualizar_contador():
                    num = len(seleccionados)
                    texto_contador.value = f"{num} experimento{'s' if num != 1 else ''} seleccionado{'s' if num != 1 else ''}"
                    if num >= 2:
                        texto_contador.color = ft.Colors.GREEN_300
                    elif num == 1:
                        texto_contador.color = ft.Colors.YELLOW_300
                    else:
                        texto_contador.color = ft.Colors.WHITE
                    page.update()

                def toggle_experimento(e, exp_nombre, checkbox):
                    if exp_nombre in seleccionados:
                        seleccionados.remove(exp_nombre)
                    else:
                        seleccionados.append(exp_nombre)
                    actualizar_contador()

                def limpiar_seleccion(e):
                    seleccionados.clear()
                    for card in cards_experimentos:
                        # Buscar el checkbox dentro del card y desmarcarlo
                        checkbox = card.content.controls[0]  # El checkbox es el primer control
                        checkbox.value = False
                    actualizar_contador()

                # Crear cards para cada experimento
                for exp in experimentos:
                    if exp["nombre"] != "BASE":
                        checkbox = ft.Checkbox(
                            label=exp["nombre"],
                            value=False,
                        )
                        checkbox.on_change = lambda e, nombre=exp["nombre"], cb=checkbox: toggle_experimento(e, nombre, cb)
                        
                        card = ft.Container(
                            width=200,
                            padding=15,
                            margin=8,
                            border_radius=10,
                            border=ft.border.all(2, ft.Colors.WHITE),
                            content=ft.Column(
                                spacing=5,
                                horizontal_alignment=ft.CrossAxisAlignment.START,
                                controls=[
                                    checkbox,
                                ]
                            )
                        )
                        cards_experimentos.append(card)

                def comparar(e):
                    if len(seleccionados) < 2:
                        alerta_seleccion_insuficiente = ft.AlertDialog(
                            modal=True,
                            title=ft.Text("Error"),
                            content=ft.Text("Selecciona al menos dos experimentos para comparar."),
                            actions=[ft.TextButton("Aceptar", on_click=lambda _: page.close(alerta_seleccion_insuficiente))],
                        )
                        page.open(alerta_seleccion_insuficiente)
                        return

                    resultados = logica_app.comparar_experimentos(seleccionados)
                    if resultados["success"]:
                        experimentos_param = "&".join([f"experimentos={exp}" for exp in seleccionados])
                        mostrar_cargando(page, True)
                        page.go(f"/main_usuario/experimentos/comparar_resultados?{experimentos_param}")
                    else:
                        alerta_error_comparacion = ft.AlertDialog(
                            modal=True,
                            title=ft.Text("Error"),
                            content=ft.Text(f"No se pudo completar la comparación: {resultados['error']}"),
                            actions=[ft.TextButton("Aceptar", on_click=lambda _: page.close(alerta_error_comparacion))],
                        )
                        page.open(alerta_error_comparacion)

                page.views.append(
                    ft.View(
                        "/main_usuario/experimentos/comparar",
                        [
                            ft.AppBar(
                                title = ft.Text(nombre_app, size = 30, text_align= "end", weight=ft.FontWeight.BOLD),
                                toolbar_height = 50,
                                bgcolor = ft.Colors.GREEN,
                                center_title = True,
                                automatically_imply_leading = False,
                                leading = ft.IconButton(
                                    icon = ft.Icons.ARROW_BACK,
                                    icon_color = ft.Colors.BLACK,
                                    on_click = lambda _: page.go("/main_usuario/experimentos")
                                )
                            ),
                            ft.Row(
                                expand=True,
                                alignment=ft.MainAxisAlignment.CENTER,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Column(
                                        expand=True,
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        spacing=15,
                                        scroll=ft.ScrollMode.AUTO,
                                        controls=[
                                    ft.Divider(),
                                    ft.Text("COMPARAR EXPERIMENTOS", size=24, weight=ft.FontWeight.BOLD),
                                    ft.Divider(),
                                    ft.Text(
                                        "Selecciona 2 o más experimentos para comparar sus resultados",
                                        size=13,
                                        color=ft.Colors.GREY_400
                                    ),
                                    texto_contador,
                                    # Grid de cards (wrap automático)
                                    ft.Container(
                                        content=ft.Row(
                                            wrap=True,
                                            alignment=ft.MainAxisAlignment.CENTER,
                                            controls=cards_experimentos,
                                        ),
                                        width=1100,
                                        expand=True,
                                    ),
                                    ft.Divider(),
                                    # Botones
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        spacing=20,
                                        controls=[
                                            ft.ElevatedButton(
                                                text="Limpiar selección",
                                                on_click=limpiar_seleccion,
                                                bgcolor=ft.Colors.GREY_700,
                                                color=ft.Colors.WHITE,
                                            ),
                                            ft.ElevatedButton(
                                                text="Comparar",
                                                on_click=comparar,
                                                bgcolor=ft.Colors.GREEN,
                                                color=ft.Colors.WHITE,
                                            ),
                                        ]
                                    ),
                                    ft.Container(height=10),
                                ],
                                    ),
                                ]
                            ),
                            ft.BottomAppBar(
                                height = 70.0,
                                bgcolor = ft.Colors.GREEN,
                                content = ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls= [
                                        ft.IconButton(
                                            icon=ft.Icons.HOME,
                                            icon_color=ft.Colors.WHITE,
                                            icon_size=30,
                                            tooltip="Volver al inicio",
                                            on_click=lambda _: page.open(alerta_cerrar_sesion)
                                        ),
                                        icono_about,
                                        icono_usuario
                                    ]
                                )
                            )
                        ],
                    )
                )
                mostrar_cargando(page, False)

            elif page.route.startswith("/main_usuario/experimentos/comparar_resultados"):
                params = page.route.split("?")[1].split("&")
                experimentos = [param.split("=")[1] for param in params if param.startswith("experimentos")]

                resultados = logica_app.obtener_graficos_comparacion(experimentos)

                imagen_ampliada_dialog = None
                imagen_ampliada = ft.Image(width=900, height=600, fit=ft.ImageFit.CONTAIN)
                imagen_ampliada_src = None
                imagen_ampliada_url_original = None  # Guardar URL para descargar

                """def mostrar_imagen_ampliada(src):
                    imagen_ampliada.src = src
                    imagen_ampliada.src_base64 = None
                    nonlocal imagen_ampliada_src, imagen_ampliada_url_original
                    imagen_ampliada_src = src
                    imagen_ampliada_url_original = src
                    page.dialog = imagen_ampliada_dialog
                    imagen_ampliada_dialog.open = True
                    page.update()"""
                
                def mostrar_imagen_ampliada_base64(img_b64, url_original):
                    imagen_ampliada.src = None
                    imagen_ampliada.src_base64 = img_b64
                    nonlocal imagen_ampliada_src, imagen_ampliada_url_original
                    imagen_ampliada_src = None
                    imagen_ampliada_url_original = url_original  # Guardar URL para descargar
                    page.dialog = imagen_ampliada_dialog
                    imagen_ampliada_dialog.open = True
                    page.update()

                def cerrar_imagen_ampliada():
                    imagen_ampliada_dialog.open = False
                    page.update()

                # Crear botón de descarga como variable para poder modificarlo
                btn_descargar = ft.ElevatedButton(
                    text="Descargar",
                    bgcolor=ft.Colors.BLUE,
                    color=ft.Colors.WHITE,
                )

                def descargar_imagen(e):
                    nonlocal imagen_ampliada_url_original
                    if imagen_ampliada_url_original:
                        btn_descargar.disabled = True
                        page.update()
                        
                        try:
                            # Descargar imagen usando el cliente autenticado de la app.
                            response = logica_app._get(imagen_ampliada_url_original, verify=False, timeout=10.0)
                            print(f"Respuesta descarga: {response.status_code} - {response.reason_phrase}")
                            if response.status_code == 200:
                                # Obtener ruta de Downloads
                                downloads_path = Path(os.path.expanduser("~/Downloads"))
                                downloads_path.mkdir(parents=True, exist_ok=True)
                                
                                # Crear nombre de archivo con timestamp
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                filename = f"imagen_{timestamp}.png"
                                filepath = downloads_path / filename
                                
                                # Guardar archivo
                                with open(filepath, "wb") as f:
                                    f.write(response.content)
                                
                                # Cambiar botón a "Descargado ✓"
                                btn_descargar.text = "✓ Descargado"
                                btn_descargar.bgcolor = ft.Colors.GREEN
                                btn_descargar.disabled = False
                                page.update()
                                
                                # Volver al estado original después de 2 segundos
                                def reset_button():
                                    time.sleep(2)
                                    btn_descargar.text = "Descargar"
                                    btn_descargar.bgcolor = ft.Colors.BLUE
                                    page.update()
                                
                                threading.Thread(target=reset_button, daemon=True).start()
                            else:
                                # Mostrar error temporalmente en el botón
                                btn_descargar.text = f"✗ Error {response.status_code}"
                                btn_descargar.bgcolor = ft.Colors.RED
                                btn_descargar.disabled = False
                                page.update()
                                
                                def reset_button_error():
                                    time.sleep(2)
                                    btn_descargar.text = "Descargar"
                                    btn_descargar.bgcolor = ft.Colors.BLUE
                                    page.update()
                                
                                threading.Thread(target=reset_button_error, daemon=True).start()
                        except Exception as ex:
                            # Mostrar error temporalmente en el botón
                            btn_descargar.text = "✗ Error"
                            btn_descargar.bgcolor = ft.Colors.RED
                            btn_descargar.disabled = False
                            page.update()
                            
                            def reset_button_error():
                                time.sleep(2)
                                btn_descargar.text = "Descargar"
                                btn_descargar.bgcolor = ft.Colors.BLUE
                                page.update()
                            
                            threading.Thread(target=reset_button_error, daemon=True).start()

                btn_descargar.on_click = descargar_imagen

                imagen_ampliada_dialog = ft.AlertDialog(
                    modal=True,
                    content=ft.Container(
                        content=ft.Column([
                            ft.Container(
                                content=imagen_ampliada,
                                expand=True,
                                margin=ft.margin.only(bottom=10),
                            ),
                            ft.Row([
                                btn_descargar,
                                ft.ElevatedButton(
                                    text="Cerrar",
                                    on_click=lambda _: cerrar_imagen_ampliada(),
                                    bgcolor=ft.Colors.RED,
                                    color=ft.Colors.WHITE,
                                ),
                            ], alignment=ft.MainAxisAlignment.CENTER),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        width=min(page.width * 0.9, 1000),
                        height=min(page.height * 0.85, 700),
                        padding=10,
                    ),
                )

                if resultados.get("success"):
                    graficos = resultados["graficos"]
                    # Cambiar las barras invertidas por barras normales en los nombres de los gráficos
                    # Descargar todas las imágenes en base64 primero
                    graficos_base64 = []
                    for grafico in graficos:
                        url = logica_app.get_url_imagen_comparacion(grafico)
                        b64 = logica_app.recuperar_imagen_base64(url)
                        graficos_base64.append(b64)
                    
                    filas = []
                    for i in range(0, len(graficos_base64), 2):
                        fila = ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Stack(
                                        controls=[
                                            ft.Image(
                                                src_base64=graficos_base64[j],
                                                width=550,
                                                height=370,
                                                fit=ft.ImageFit.CONTAIN,
                                            ),
                                            ft.Container(
                                                content=ft.Icon(
                                                    name=ft.Icons.ZOOM_IN,
                                                    color=ft.Colors.WHITE,
                                                    size=30,
                                                ),
                                                alignment=ft.alignment.bottom_right,
                                                padding=10,
                                            ),
                                        ],
                                    ),
                                    border=ft.border.all(2, ft.Colors.GREEN_200),
                                    border_radius=10,
                                    bgcolor=ft.Colors.WHITE,
                                    padding=10,
                                    shadow=ft.BoxShadow(
                                        spread_radius=1,
                                        blur_radius=10,
                                        color=ft.Colors.BLACK26,
                                        offset=ft.Offset(0, 2),
                                    ),
                                    ink=True,
                                    on_click=lambda e, img_b64=graficos_base64[j], url=logica_app.get_url_imagen_comparacion(graficos[j]): mostrar_imagen_ampliada_base64(img_b64, url),
                                )
                                for j in range(i, min(i + 2, len(graficos_base64)))
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=20,
                        )
                        filas.append(fila)

                    page.views.append(
                        ft.View(
                            "/main_usuario/experimentos/comparar_resultados",
                            [
                                ft.AppBar(
                                    title = ft.Text(nombre_app, size = 30, text_align= "end", weight=ft.FontWeight.BOLD),
                                    toolbar_height = 50,
                                    bgcolor = ft.Colors.GREEN,
                                    center_title = True,
                                    automatically_imply_leading = False,
                                    leading = ft.IconButton(
                                        icon = ft.Icons.ARROW_BACK,
                                        icon_color = ft.Colors.BLACK,
                                        on_click = lambda _: page.go("/main_usuario/experimentos/comparar")
                                    )
                                ),
                                ft.Row(
                                    expand=True,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Column(
                                            expand=True,
                                            alignment=ft.MainAxisAlignment.CENTER,
                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                            scroll=ft.ScrollMode.AUTO,
                                            controls=[
                                                ft.Container(
                                                    expand=True,
                                                    content=ft.Column(
                                                        alignment=ft.MainAxisAlignment.CENTER,
                                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                        controls=[
                                                            ft.Divider(),
                                                            ft.Text(
                                                                "RESULTADOS DE LA COMPARACIÓN",
                                                                size=24,
                                                                weight=ft.FontWeight.BOLD,
                                                                color=ft.Colors.WHITE,
                                                            ),
                                                            ft.Divider(),
                                                            ft.Column(
                                                                controls=filas,
                                                                spacing=20,
                                                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                            ),
                                                            ft.Container(height=20),
                                                        ],
                                                    ),
                                                ),
                                            ],
                                        ),
                                    ]
                                ),
                                imagen_ampliada_dialog,
                                ft.BottomAppBar(
                                height = 70.0,
                                bgcolor = ft.Colors.GREEN,
                                content = ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls= [
                                        ft.IconButton(
                                            icon=ft.Icons.HOME,
                                            icon_color=ft.Colors.WHITE,
                                            icon_size=30,
                                            tooltip="Volver al inicio",
                                            on_click=lambda _: page.open(alerta_cerrar_sesion)
                                        ),
                                        icono_about,
                                        icono_usuario
                                        ]
                                    )
                                )
                            ],
                            scroll=ft.ScrollMode.AUTO,
                        )
                    )
                else:
                    page.views.append(
                        ft.View(
                            "/main_usuario/experimentos/comparar_resultados",
                            [
                                ft.AppBar(
                                    title=ft.Text("Error"),
                                    center_title=True,
                                    bgcolor=ft.Colors.RED,
                                    leading=ft.IconButton(
                                        icon=ft.Icons.ARROW_BACK,
                                        on_click=lambda _: page.go("/main_usuario/experimentos/comparar"),
                                    ),
                                ),
                                ft.Column(
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    expand=True,
                                    controls=[
                                        ft.Text("No se pudo obtener los resultados de la comparación.", size=18, color=ft.Colors.RED),
                                        ft.Text(resultados.get("error", "Error desconocido"), size=14),
                                    ],
                                ),
                                ft.BottomAppBar(
                                height = 70.0,
                                bgcolor = ft.Colors.GREEN,
                                content = ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls= [
                                        ft.IconButton(
                                            icon=ft.Icons.HOME,
                                            icon_color=ft.Colors.WHITE,
                                            icon_size=30,
                                            tooltip="Volver al inicio",
                                            on_click=lambda _: page.open(alerta_cerrar_sesion)
                                        ),
                                        icono_about,
                                        icono_usuario
                                        ]
                                    )
                                )
                            ],
                            scroll=ft.ScrollMode.AUTO,
                        )
                    )
                mostrar_cargando(page, False)

            elif page.route.startswith("/main_usuario/experimentos/") and page.route != "/main_usuario/experimentos/crear":
                nombre_experimento = page.route.split("/")[-1]

                resultados = logica_app.obtener_resultados_experimento(nombre_experimento)

                imagen_ampliada_dialog = None
                imagen_ampliada = ft.Image(width=900, height=600, fit=ft.ImageFit.CONTAIN)
                imagen_ampliada_src = None
                imagen_ampliada_url_original = None  # Guardar URL para descargar

                """def mostrar_imagen_ampliada(src):
                    imagen_ampliada.src = src
                    imagen_ampliada.src_base64 = None
                    nonlocal imagen_ampliada_src, imagen_ampliada_url_original
                    imagen_ampliada_src = src
                    imagen_ampliada_url_original = src
                    page.dialog = imagen_ampliada_dialog
                    imagen_ampliada_dialog.open = True
                    page.update()"""
                
                def mostrar_imagen_ampliada_base64(img_b64, url_original):
                    imagen_ampliada.src = None
                    imagen_ampliada.src_base64 = img_b64
                    nonlocal imagen_ampliada_src, imagen_ampliada_url_original
                    imagen_ampliada_src = None
                    imagen_ampliada_url_original = url_original  # Guardar URL para descargar
                    page.dialog = imagen_ampliada_dialog
                    imagen_ampliada_dialog.open = True
                    page.update()

                def cerrar_imagen_ampliada():
                    imagen_ampliada_dialog.open = False
                    page.update()

                # Crear botón de descarga como variable para poder modificarlo
                btn_descargar = ft.ElevatedButton(
                    text="Descargar",
                    bgcolor=ft.Colors.BLUE,
                    color=ft.Colors.WHITE,
                )

                def descargar_imagen(e):
                    nonlocal imagen_ampliada_url_original
                    if imagen_ampliada_url_original:
                        btn_descargar.disabled = True
                        page.update()
                        
                        try:
                            # Descargar imagen usando el cliente autenticado de la app.
                            response = logica_app._get(imagen_ampliada_url_original, verify=False, timeout=10.0)
                            if response.status_code == 200:
                                # Obtener ruta de Downloads
                                downloads_path = Path(os.path.expanduser("~/Downloads"))
                                downloads_path.mkdir(parents=True, exist_ok=True)
                                
                                # Crear nombre de archivo con timestamp
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                filename = f"imagen_{timestamp}.png"
                                filepath = downloads_path / filename
                                
                                # Guardar archivo
                                with open(filepath, "wb") as f:
                                    f.write(response.content)
                                
                                # Cambiar botón a "Descargado ✓"
                                btn_descargar.text = "✓ Descargado"
                                btn_descargar.bgcolor = ft.Colors.GREEN
                                btn_descargar.disabled = False
                                page.update()
                                
                                # Volver al estado original después de 2 segundos
                                def reset_button():
                                    time.sleep(2)
                                    btn_descargar.text = "Descargar"
                                    btn_descargar.bgcolor = ft.Colors.BLUE
                                    page.update()
                                
                                threading.Thread(target=reset_button, daemon=True).start()
                            else:
                                # Mostrar error temporalmente en el botón
                                btn_descargar.text = f"✗ Error {response.status_code}"
                                btn_descargar.bgcolor = ft.Colors.RED
                                btn_descargar.disabled = False
                                page.update()
                                
                                def reset_button_error():
                                    time.sleep(2)
                                    btn_descargar.text = "Descargar"
                                    btn_descargar.bgcolor = ft.Colors.BLUE
                                    page.update()
                                
                                threading.Thread(target=reset_button_error, daemon=True).start()
                        except Exception as ex:
                            # Mostrar error temporalmente en el botón
                            btn_descargar.text = "✗ Error"
                            btn_descargar.bgcolor = ft.Colors.RED
                            btn_descargar.disabled = False
                            page.update()
                            
                            def reset_button_error():
                                time.sleep(2)
                                btn_descargar.text = "Descargar"
                                btn_descargar.bgcolor = ft.Colors.BLUE
                                page.update()
                            
                            threading.Thread(target=reset_button_error, daemon=True).start()

                btn_descargar.on_click = descargar_imagen

                imagen_ampliada_dialog = ft.AlertDialog(
                    modal=True,
                    content=ft.Container(
                        content=ft.Column([
                            ft.Container(
                                content=imagen_ampliada,
                                expand=True,
                                margin=ft.margin.only(bottom=10),
                            ),
                            ft.Row([
                                btn_descargar,
                                ft.ElevatedButton(
                                    text="Cerrar",
                                    on_click=lambda _: cerrar_imagen_ampliada(),
                                    bgcolor=ft.Colors.RED,
                                    color=ft.Colors.WHITE,
                                ),
                            ], alignment=ft.MainAxisAlignment.CENTER),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        width=min(page.width * 0.9, 1000),
                        height=min(page.height * 0.85, 700),
                        padding=10,
                    ),
                )

                controles_resultados = []
                if resultados.get("resultados"):
                    archivos = resultados["resultados"]
                    # Descargar todas las imágenes en base64 primero
                    archivos_base64 = []
                    for archivo in archivos:
                        url = logica_app.get_url_imagen_resultado(nombre_experimento, archivo)
                        b64 = logica_app.recuperar_imagen_base64(url)
                        archivos_base64.append(b64)
                    
                    # Título de la sección
                    controles_resultados.append(ft.Divider())
                    controles_resultados.append(
                        ft.Text(
                            f"Resultados del Experimento",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                        )
                    )
                    controles_resultados.append(ft.Divider())
                    
                    filas = []
                    for i in range(0, len(archivos_base64), 2):
                        fila = ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Stack(
                                        controls=[
                                            ft.Image(
                                                src_base64=archivos_base64[idx],
                                                width=450,
                                                height=320,
                                                fit=ft.ImageFit.CONTAIN,
                                            ),
                                            ft.Container(
                                                content=ft.Icon(
                                                    name=ft.Icons.ZOOM_IN,
                                                    color=ft.Colors.WHITE,
                                                    size=28,
                                                ),
                                                alignment=ft.alignment.bottom_right,
                                                padding=8,
                                            ),
                                        ],
                                    ),
                                    border=ft.border.all(2, ft.Colors.GREEN_200),
                                    border_radius=10,
                                    bgcolor=ft.Colors.WHITE,
                                    padding=10,
                                    shadow=ft.BoxShadow(
                                        spread_radius=1,
                                        blur_radius=10,
                                        color=ft.Colors.BLACK26,
                                        offset=ft.Offset(0, 2),
                                    ),
                                    ink=True,
                                    on_click=lambda e, img_b64=archivos_base64[idx], url=logica_app.get_url_imagen_resultado(nombre_experimento, archivos[idx]): mostrar_imagen_ampliada_base64(img_b64, url),
                                )
                                for idx in range(i, min(i + 2, len(archivos_base64)))
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=20,
                        )
                        filas.append(fila)
                    
                    controles_resultados.append(
                        ft.Column(
                            controls=filas,
                            spacing=20,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        )
                    )
                    controles_resultados.append(ft.Container(height=20))  # Espacio al final
                else:
                    controles_resultados.append(
                        ft.Text(f"Error: {resultados.get('error', 'No se pudieron cargar los resultados.')}")
                    )

                page.views.append(
                    ft.View(
                        page.route,
                        [
                            ft.AppBar(
                                title = ft.Text(nombre_app, size = 30, text_align= "end", weight=ft.FontWeight.BOLD),
                                toolbar_height = 50,
                                bgcolor = ft.Colors.GREEN,
                                center_title = True,
                                automatically_imply_leading = False,
                                leading = ft.IconButton(
                                    icon = ft.Icons.ARROW_BACK,
                                    icon_color = ft.Colors.BLACK,
                                    on_click = lambda _: page.go("/main_usuario/experimentos")
                        )
                            ),
                            ft.Row(
                                expand=True,
                                alignment=ft.MainAxisAlignment.CENTER,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Column(
                                        expand=True,
                                        controls=controles_resultados,
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        scroll=ft.ScrollMode.AUTO,
                                    ),
                                ]
                            ),
                            imagen_ampliada_dialog,
                            ft.BottomAppBar(
                                height = 70.0,
                                bgcolor = ft.Colors.GREEN,
                                content = ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls= [
                                        ft.IconButton(
                                            icon=ft.Icons.HOME,
                                            icon_color=ft.Colors.WHITE,
                                            icon_size=30,
                                            tooltip="Volver al inicio",
                                            on_click=lambda _: page.open(alerta_cerrar_sesion)
                                        ),
                                        icono_about,
                                        icono_usuario
                                    ]
                                )
                            )
                        ],
                        scroll=ft.ScrollMode.AUTO,
                    )
                )
                mostrar_cargando(page, False)

            page.update()
        

        page.on_route_change = route_change
        page.on_view_pop = view_pop
        page.go(page.route)
        
    ft.app(main)