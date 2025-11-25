import os
import flet as ft
import httpx
import logicav3 as logica

nombre_app = "Aplicación Plantas"


if __name__ == "__main__":

    logica_app = logica.LogicaApp()

    def main(page: ft.Page):
        saved_url_api = page.client_storage.get("url_api")
        if saved_url_api:
            logica_app.set_url_api(saved_url_api)

        saved_url_bbdd = page.client_storage.get("url_bbdd")
        if saved_url_bbdd:
            if saved_url_bbdd != logica_app.url_bbdd:
                logica_app.cambiar_url_bbdd()
            logica_app.set_url_bbdd(saved_url_bbdd)

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
            else: page.go("/main_admin/busqueda")

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
                        actions=[ft.TextButton("Aceptar", on_click=lambda e: page.go("/configuracion"))]
                    ))
                except httpx.RequestError as e:
                    page.open(ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Servidor inaccesible"),
                        content=ft.Text(f"No se pudo conectar con el servidor en {logica_app.url_api}.\n\nRevisa la IP en la configuración."),
                        actions=[ft.TextButton("Aceptar", on_click=lambda e: page.go("/configuracion"))]
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
            page.go("/main_admin/busqueda/datos_usuario")

        def info_usuario_seleccionado():
            doc = getattr(logica_app, "usuario_seleccionado", {}) or {}
            name = doc.get("nombre", "")
            roles = doc.get("rol", [])
            roles_text = ", ".join(str(r) for r in roles)
            return [ft.Text(f"Nombre: {name}\nRoles: [{roles_text}]")]

        def crear_columnas(datos: list[dict]):
            if len(datos) == 0: return []
            datos.sort(key=len, reverse=True)
            refe = datos[0]

            columnas = []
            for campo in refe.keys():
                columnas.append( ft.DataColumn(ft.Text(f"{campo}")) )
            
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

        def predecir_foto(modelo_seleccionado):
            resultado = logica_app.predecir_imagen(modelo_seleccionado)
            if resultado["success"]:
                pred = resultado["enfermedad_predicha"]
                planta = resultado["planta_predicha"]
                prob = round(resultado["probabilidad"] * 100, 2)
                page.open(ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Predicción del modelo"),
                    content=ft.Text(f"Planta: {planta}\nEnfermedad: {pred}\nProbabilidad: {prob}%"),
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

        def ejecutar_subida_masiva(page, logica_app, fuente_input, procesar_switch):
            fuente = fuente_input.value.strip()
            procesar = procesar_switch.value

            if not fuente:
                page.open(ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Error"),
                    content=ft.Text("Introduce el nombre de la fuente."),
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
                res = httpx.post(
                    logica_app.crear_url("/subida_masiva", logica_app.url_api),
                    json={"fuente": fuente, "procesar": procesar},
                    timeout=600
                )
                data = res.json()
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
                    "planta": dropdown_planta.value,
                    "enfermedad": dropdown_enfermedad.value,
                    "formato": dropdown_formato.value,
                    "fuente": dropdown_fuente.value,
                    "num": int(dropdown_num_imagenes.value)
                }
                logica_app.max_archivos = int(dropdown_num_imagenes.value)
                logica_app.puntero_repo = 0

                mostrar_cargando(page, True)
                cargar_datos_no_validados()
                page.update()
                page.go("/main_etiquetador/seleccion_imagenes")
            return _handler
        
        def filtrar_clases(page, clases, clases_modificadas, tabla_clases, dropdown_filtro):
            def actualizar(e, campo, cid):
                for x in clases:
                    if x.get("_id") == cid:
                        x[campo] = e.control.value
                        if x not in clases_modificadas:
                            clases_modificadas.append(x)
                        break

            def run():
                filtro = dropdown_filtro.value
                if filtro == "Incompletas":
                    visibles = [c for c in clases if not c.get("clasificacion") or not c.get("nombre_cientifico")]
                elif filtro == "Completas":
                    visibles = [c for c in clases if c.get("clasificacion") and c.get("nombre_cientifico")]
                else:
                    visibles = clases

                # Actualizar las filas de la tabla
                tabla_clases.rows.clear()
                for c in visibles:
                    clasif_input = ft.TextField(value=c.get("clasificacion", ""), width=600)
                    cient_input = ft.TextField(value=c.get("nombre_cientifico", ""), width=600)

                    clasif_input.on_change = lambda e, cid=c.get("_id"): actualizar(e, "clasificacion", cid)
                    cient_input.on_change = lambda e, cid=c.get("_id"): actualizar(e, "nombre_cientifico", cid)

                    fila = ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(c.get("_id")))),
                            ft.DataCell(ft.Text(c.get("planta", ""))),
                            ft.DataCell(ft.Text(c.get("nombre_comun", ""))),
                            ft.DataCell(clasif_input),
                            ft.DataCell(cient_input),
                        ]
                    )
                    tabla_clases.rows.append(fila)
                page.update()

            return run


        def guardar_cambios(page, clases, clases_modificadas, logica_app):
            """Devuelve handler que envía las clases modificadas al servidor (reemplazo)."""
            def handler(e):
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
            return handler
        
        def crear_experimento(nombre_experimento, config_variables, entrenar_modelo, page):
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
                        logica_app.solicitar_entrenamiento(nombre_experimento)
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

        def abrir_dialogo_seleccion_modelo():
            modelos = logica_app.obtener_modelos()  # Obtener la lista de modelos disponibles
            if not modelos:
                dialog_no_modelos = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Sin modelos disponibles"),
                    content=ft.Text("No se encontraron modelos entrenados."),
                    actions=[ft.TextButton("Aceptar", on_click=lambda e: page.close(dialog_no_modelos))]
                )
                page.open(dialog_no_modelos)
                return

            radio_group = ft.RadioGroup(
                content=ft.Column(
                    [
                        ft.Radio(label=modelo, value=modelo)
                        for modelo in modelos
                    ]
                )
            )

            def confirmar_seleccion(e):
                modelo_seleccionado = radio_group.value
                page.close(dialogo_seleccion_modelo)
                predecir_foto(modelo_seleccionado)

            dialogo_seleccion_modelo = ft.AlertDialog(
                modal=True,
                title=ft.Text("Seleccionar modelo"),
                content=radio_group,
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda _: page.close(dialogo_seleccion_modelo)),
                    ft.TextButton("Confirmar", on_click=confirmar_seleccion),
                ],
            )

            page.open(dialogo_seleccion_modelo)

        def entrenar_modelo(nombre_experimento):
            dialogo_entrenamiento = ft.AlertDialog(
                modal=True,
                title=ft.Text("Entrenamiento en progreso"),
                content=ft.Text("El entrenamiento puede tardar un tiempo. Por favor, espere."),
                actions=[],
            )

            # Mostrar el diálogo de entrenamiento
            page.open(dialogo_entrenamiento)

            try:
                resultado = logica_app.entrenar_modelo(nombre_experimento)
                if resultado["success"]:
                    page.open(ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Entrenamiento completado"),
                        content=ft.Text(f"El modelo '{nombre_experimento}' se ha entrenado correctamente."),
                        actions=[ft.TextButton("Aceptar", on_click=lambda _: (mostrar_cargando(page, True), page.go("/main_admin/entrenamientos")))]
                    ))
                else:
                    page.open(ft.AlertDialog(
                        modal=True,
                        title=ft.Text("Error en el entrenamiento"),
                        content=ft.Text(resultado.get("error", "Error desconocido")),
                        actions=[ft.TextButton("Aceptar", on_click=lambda _: (mostrar_cargando(page, True), page.go("/main_admin/entrenamientos")))]
                    ))
            except Exception as ex:
                page.open(ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Error inesperado"),
                    content=ft.Text(f"Error: {str(ex)}"),
                    actions=[ft.TextButton("Aceptar", on_click=lambda _: (mostrar_cargando(page, True), page.go("/main_admin/entrenamientos")))]
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
                mostrar_cargando(page, False)
            
            page.update()
            

        def retroceder_imagenes():
            avanzar_imagenes(reverso=True)
        
        tabla_docs_no_validados = ft.DataTable(
            columns=[
                ft.DataColumn(label=ft.Text("Imagen")),
                ft.DataColumn(label=ft.Text("Etiqueta Provisional")),
            ],
            rows=[]
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
                            ft.Image(
                                src_base64=logica_app.recuperar_imagen_base64(item["imagen_rgb"]),
                                width=25,
                                height=25,
                            )
                        ),
                        ft.DataCell(ft.Text(logica_app.procesar_nombre_una_etiqueta(item["clase"]))),
                    ],
                    on_select_changed=seleccionar_imagen,
                    data=item
                )
                tabla_docs_no_validados.rows.append(fila)
            #logica_app.evitar_recarga = False
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
                dropdown_etiquetar.options.append(ft.dropdown.Option(key=ep["key"], text=ep["texto"]))
            dropdown_etiquetar.value = opcion_por_defecto or "none"
            dropdown_etiquetar.update()

        def deseleccionar_etiqueta_dropdown(e):
            dropdown_etiquetar.value = "none"
            dropdown_etiquetar.update()
            page.snack_bar = ft.SnackBar(ft.Text("Etiqueta deseleccionada"))
            page.snack_bar.open = True
            page.update()

        dropdown_etiquetar = ft.Dropdown(
            label="Etiqueta",
            hint_text=None,
            width=450,
            options=[ft.dropdown.Option(key="none", text="Sin clasificar")],
            value="none",                 
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
            if not dropdown_etiquetar.value or dropdown_etiquetar.value == "none":
                page.open(ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Falta seleccionar una etiqueta"),
                    content=ft.Text("Por favor, selecciona una categoría antes de subir la imagen."),
                    actions=[ft.TextButton("Aceptar", on_click=lambda e: page.close(e.control.parent))]
                ))
                return
            subida_correcta = logica_app.subir_foto(dropdown_etiquetar.value)
            
            if subida_correcta:
                page.open(ft.AlertDialog(
                    modal = True,
                    title = ft.Text("Imagen subida correctamente"),
                    actions = [
                        ft.TextButton(
                            "Aceptar",
                            on_click = lambda _: view_pop(page.views[-1])
                        )
                    ]
                ))
            else:
                page.open(ft.AlertDialog(
                    modal = True,
                    title = ft.Text("No se ha podido subir la imagen"),
                    actions = [
                        ft.TextButton(
                            "Aceptar",
                            on_click = lambda _: view_pop(page.views[-1])
                        )
                    ]
                ))


        def route_change(route):
            page.views.clear()
            page.views.append(
               ft.View(
                    "/",
                    [
                        
                        ft.AppBar(
                            title = ft.Text(nombre_app, size = 40, text_align= "end"),
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
                                            "Iniciar Sesión",
                                            size=18,
                                        ),
                                        ft.Text(
                                            "Seleccionar rol:",
                                            size = 12,
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
                                        ft.Container(
                                            content=ft.Image(
                                                src="./src/assets/logos.png",
                                                fit=ft.ImageFit.CONTAIN,
                                                expand=True
                                            ),
                                            bgcolor=ft.Colors.WHITE,
                                            expand=True,
                                            alignment=ft.alignment.center
                                        )
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
                    label="Dirección del servidor Flask (ej. 192.168.1.50:5001)",
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
                                title=ft.Text("Configuración del servidor"),
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
                                controls=[
                                    ft.Text("Introduce la IP o dominio del servidor Flask:", size=18),
                                    url_input,
                                    ft.ElevatedButton(
                                        text="Guardar",
                                        bgcolor=ft.Colors.GREEN,
                                        color=ft.Colors.WHITE,
                                        on_click=guardar_url_api
                                    ),
                                    ft.Text(
                                        "Ejemplo: http://192.168.1.100:5001 o http://10.0.2.2:5001",
                                        size=12,
                                        color=ft.Colors.GREY
                                    )
                                ]
                            ),
                            ft.Column(
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                expand=True,
                                controls=[
                                    ft.Text("Introduce la URL de la base de datos MongoDB:", size=18),
                                    bbdd_url_input,
                                    ft.ElevatedButton(
                                        text="Guardar",
                                        bgcolor=ft.Colors.GREEN,
                                        color=ft.Colors.WHITE,
                                        on_click=guardar_url_bbdd
                                    ),
                                    ft.Text(
                                        "Ejemplo: mongodb://localhost:27017 o mongodb+srv://cluster0.mongodb.net",
                                        size=12,
                                        color=ft.Colors.GREY
                                    )
                                ]
                            )
                        ]
                    )
                )

            # Etiquetador - MENU PRINCIPAL
            if page.route == "/main_etiquetador":
                page.views.append(
                    ft.View(
                        "/main_etiquetador",
                        [
                            ft.AppBar(
                                title = ft.Text(nombre_app, size = 40, text_align= "end"),
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
                            # Contenedor Row para centrar vertical y horizontalmente
                            ft.Row(
                                expand=True,
                                alignment=ft.MainAxisAlignment.CENTER,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Column(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        spacing=20,
                                        controls=[
                                            ft.Text("Etiquetador - Menú", size=22),
                                            ft.ElevatedButton(
                                                "Etiquetar / Validar imágenes",
                                                bgcolor=ft.Colors.GREEN,
                                                color=ft.Colors.WHITE,
                                                on_click=lambda _: (mostrar_cargando(page, True), page.go("/main_etiquetador/filtros"))
                                            ),
                                            ft.ElevatedButton(
                                                "Editar clases",
                                                bgcolor=ft.Colors.WHITE,
                                                color=ft.Colors.BLACK,
                                                on_click=lambda _: (mostrar_cargando(page, True), page.go("/main_etiquetador/editar_clases"))
                                            ),
                                        ]
                                    )
                                ]
                            ),
                            ft.BottomAppBar(
                                height = 70.0,
                                bgcolor = ft.Colors.GREEN,
                                content = ft.Row(
                                    alignment=ft.MainAxisAlignment.END,
                                    controls= [
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

                dropdown_planta = ft.Dropdown(label="Planta", options=[ft.dropdown.Option(p) for p in plantas])
                dropdown_enfermedad = ft.Dropdown(label="Enfermedad", options=[ft.dropdown.Option(e) for e in enfermedades])
                dropdown_formato = ft.Dropdown(label="Formato", options=[ft.dropdown.Option(f["formato"]) for f in formatos])
                dropdown_fuente = ft.Dropdown(label="Fuente", options=[ft.dropdown.Option(f["fuente"]) for f in fuentes])
                dropdown_num_imagenes = ft.Dropdown(
                    label="Número de imágenes",
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
                                title = ft.Text(nombre_app, size = 40, text_align= "end"),
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
                                        spacing=15,
                                        controls=[
                                            ft.Container(width=450, content=dropdown_planta),
                                            ft.Container(width=450, content=dropdown_enfermedad),
                                            ft.Container(width=450, content=dropdown_formato),
                                            ft.Container(width=450, content=dropdown_fuente),
                                            ft.Container(width=450, content=dropdown_num_imagenes),
                                            ft.ElevatedButton(
                                                "Cargar imágenes",
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
                                    alignment=ft.MainAxisAlignment.END,
                                    controls= [
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
                page.views.append(
                    ft.View(
                    "/main_etiquetador/seleccion_imagenes",
                    [
                        ft.AppBar(
                            title = ft.Text(nombre_app, size = 40, text_align= "end"),
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
                                    controls = [
                                        ft.Column(
                                            alignment = ft.MainAxisAlignment.CENTER,
                                            horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                                            expand = True,
                                            controls = [tabla_docs_no_validados,]
                                        ),
                                        ft.Row(
                                            alignment = ft.MainAxisAlignment.CENTER,
                                            vertical_alignment = ft.CrossAxisAlignment.CENTER,
                                            expand = True,
                                            controls = [
                                                ft.ElevatedButton(text="Anterior", on_click=lambda _: (mostrar_cargando(page, True), retroceder_imagenes())),
                                                ft.ElevatedButton(text="Siguiente", on_click=lambda _: (mostrar_cargando(page, True), avanzar_imagenes())),
                                                ft.OutlinedButton(text="Volver a filtros",
                                                                  style=ft.ButtonStyle(
                                                                  color=ft.Colors.BLUE,
                                                                        overlay_color=ft.Colors.BLUE_50,
                                                                        side=ft.BorderSide(1, ft.Colors.BLUE),
                                                                    ),
                                                                    on_click=lambda _: (mostrar_cargando(page, True), page.go("/main_etiquetador/filtros"))
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
                                    alignment=ft.MainAxisAlignment.END,
                                    controls= [
                                        icono_usuario
                                    ]
                                )
                            )
                        ]
                    )
                )

            if page.route.startswith("/main_etiquetador/seleccion_imagenes/etiquetar"):
                page.views.append(
                    ft.View(
                        "/main_etiquetador/seleccion_imagenes/etiquetar",
                        [
                            ft.AppBar(
                                title = ft.Text(nombre_app, size = 40, text_align= "end"),
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
                                        controls = [
                                           ft.Image(
                                               src_base64=logica_app.recuperar_imagen_base64(logica_app.archivo_seleccionado["imagen_rgb"]),
                                               fit=ft.ImageFit.CONTAIN
                                           ),
                                           ft.Divider(),
                                           dropdown_etiquetar,
                                           ft.ElevatedButton(
                                               "Etiquetar",
                                               on_click=lambda _: etiquetar_imagen()
                                            ),
                                            ft.ElevatedButton(
                                                "Validar",
                                                bgcolor=ft.Colors.BLUE,
                                                color=ft.Colors.WHITE,
                                                on_click=lambda _: validar_imagen_actual()
                                            ),
                                        ]
                                    )
                                ]
                            ),
                            ft.BottomAppBar(
                                height = 70.0,
                                bgcolor = ft.Colors.GREEN,
                                content = ft.Row(
                                    alignment=ft.MainAxisAlignment.END,
                                    controls= [
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

                clases = res["clases"]
                clases_modificadas = []

                dropdown_filtro = ft.Dropdown(
                    label="Mostrar:",
                    options=[
                        ft.dropdown.Option("Incompletas"),
                        ft.dropdown.Option("Completas"),
                        ft.dropdown.Option("Todas")
                    ],
                    value="Incompletas"
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

                filtrar_clases_fn = filtrar_clases(page, clases, clases_modificadas, tabla_clases, dropdown_filtro)
                dropdown_filtro.on_change = lambda e: filtrar_clases_fn()
                filtrar_clases_fn()

                guardar_cambios_handler = guardar_cambios(page, clases, clases_modificadas, logica_app)

                page.views.append(
                    ft.View(
                        "/main_etiquetador/editar_clases",
                        [
                            ft.AppBar(
                                title=ft.Text("Editar clases"),
                                bgcolor=ft.Colors.GREEN,
                                center_title=True,
                                leading=ft.IconButton(
                                    icon=ft.Icons.ARROW_BACK,
                                    icon_color=ft.Colors.BLACK,
                                    on_click=lambda _: page.go("/main_etiquetador")
                                )
                            ),
                            ft.Column(
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                expand=True,
                                scroll=ft.ScrollMode.AUTO,
                                controls=[
                                    dropdown_filtro,
                                    ft.Divider(),
                                    tabla_clases,
                                    ft.Divider(),
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        controls=[
                                            ft.ElevatedButton(
                                                text="Guardar cambios",
                                                bgcolor=ft.Colors.GREEN,
                                                color=ft.Colors.WHITE,
                                                on_click=guardar_cambios_handler
                                            ),
                                            ft.ElevatedButton(
                                                text="Cancelar",
                                                bgcolor=ft.Colors.RED,
                                                color=ft.Colors.WHITE,
                                                on_click=lambda _: page.go("/main_etiquetador")
                                            ),
                                            ft.ElevatedButton(
                                                text="Añadir clase",
                                                bgcolor=ft.Colors.BLUE,
                                                color=ft.Colors.WHITE,
                                                on_click=abrir_dialogo_add_class
                                            ),
                                        ]
                                    )
                                ]
                            ),
                            ft.BottomAppBar(
                                height=70.0,
                                bgcolor=ft.Colors.GREEN,
                                content=ft.Row(
                                    alignment=ft.MainAxisAlignment.END,
                                    controls=[icono_usuario]
                                ),
                            ),
                        ]
                    )
                )
            mostrar_cargando(page, False)

                
            if page.route == ("/main_usuario"):
                file_picker = ft.FilePicker(on_result=on_image_selected)
                page.overlay.append(file_picker)

                page.views.append(
                    ft.View(
                        "/main_usuario",
                        [
                            ft.AppBar(
                                title=ft.Text(nombre_app, size=40, text_align="end"),
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
                                        controls=[
                                            ft.ElevatedButton(
                                                adaptive=True,
                                                bgcolor=ft.Colors.GREEN,
                                                color=ft.Colors.WHITE,
                                                text="SELECCIONAR FOTO",
                                                on_click=lambda _: file_picker.pick_files(allow_multiple=False),
                                            ),
                                            ft.ElevatedButton(
                                                adaptive=True,
                                                bgcolor=ft.Colors.GREEN,
                                                color=ft.Colors.WHITE,
                                                text="SUBIDA MASIVA DE IMÁGENES",
                                                on_click=lambda _: page.go("/main_usuario/subida_masiva"),
                                            ),
                                            ft.ElevatedButton(
                                                adaptive=True,
                                                bgcolor=ft.Colors.GREEN,
                                                color=ft.Colors.WHITE,
                                                text="EXPERIMENTOS",
                                                on_click=lambda _: (mostrar_cargando(page, True), page.go("/main_usuario/experimentos")),
                                            ),
                                        ]
                                    )
                                ]
                            )
                        ]
                    )
                )
                page.update()
            if page.route == "/main_usuario/foto":
                    """models = logica_app.obtener_modelos()
                    default_model = models[0] if models else None
                    dropdown_modelo = ft.Dropdown(
                        label="Seleccionar modelo",
                        options=[ft.dropdown.Option(m) for m in models],
                        value=default_model,
                    )"""

                    page.views.append(
                        ft.View(
                            "/main_usuario/foto",
                            [
                                ft.AppBar(
                                    title = ft.Text(nombre_app, size = 40, text_align= "end"),
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
                                                controls = [
                                                    ft.Container(
                                                        content=ft.Image(
                                                            src_base64=logica_app.foto_b64,
                                                            width=300,
                                                            height=300,
                                                            fit=ft.ImageFit.CONTAIN,
                                                        ),
                                                        alignment=ft.alignment.center,
                                                    ),
                                                    dropdown_etiquetar,
                                                    ft.ElevatedButton(
                                                        adaptive= True,
                                                        bgcolor = ft.Colors.GREEN,
                                                        color = ft.Colors.WHITE,
                                                        text = "Deseleccionar etiqueta",
                                                        on_click=deseleccionar_etiqueta_dropdown
                                                    ),
                                                    ft.Row(
                                                        alignment = ft.MainAxisAlignment.CENTER,
                                                        vertical_alignment = ft.CrossAxisAlignment.CENTER,
                                                        expand = True,
                                                        controls=[
                                                            ft.ElevatedButton(
                                                                adaptive= True,
                                                                bgcolor = ft.Colors.GREEN,
                                                                color = ft.Colors.WHITE,
                                                                text = "SUBIR FOTO",
                                                                on_click=lambda _: subir_foto()
                                                            ),
                                                            ft.ElevatedButton(
                                                                adaptive= True,
                                                                bgcolor = ft.Colors.RED,
                                                                color = ft.Colors.WHITE,
                                                                text = "CANCELAR",
                                                                on_click=lambda _: page.go("/main_usuario")
                                                            ),
                                                            ft.ElevatedButton(
                                                                adaptive=True,
                                                                bgcolor=ft.Colors.BLUE,
                                                                color=ft.Colors.WHITE,
                                                                text="PREDECIR ENFERMEDAD",
                                                                on_click=lambda _: abrir_dialogo_seleccion_modelo()
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
                                        alignment=ft.MainAxisAlignment.END,
                                        controls= [
                                            icono_usuario
                                        ]
                                    )
                                )
                            ]
                        )
                    )
                    page.update()
                    dropdown_etiquetar_options()
                    
            if page.route == "/main_usuario/subida_masiva":
                    es_movil = page.platform in ["android", "ios", "fuchsia"] or (page.width and page.width < 800)
                    if es_movil:
                        def cerrar_alerta(e):
                            page.close(dialogo)
                            page.go("/main_usuario")
                            page.update()

                        dialogo = ft.AlertDialog(
                            modal=True,
                            title=ft.Text("Función no disponible"),
                            content=ft.Text("La subida masiva solo está disponible en la versión de escritorio."),
                            actions=[ft.TextButton("Aceptar", on_click=cerrar_alerta)],
                        )

                        page.open(dialogo)
                        page.update()
                        return

                    fuente_input = ft.TextField(label="Nombre de la fuente (carpeta en data/Imported/)")
                    procesar_switch = ft.Switch(label="Procesar imágenes (escala de grises y segmentadas)", value=False)

                    page.views.append(
                        ft.View(
                            "/main_usuario/subida_masiva",
                            [
                                ft.AppBar(
                                    title=ft.Text("Subida masiva de imágenes"),
                                    bgcolor=ft.Colors.GREEN,
                                    center_title=True,
                                    leading=ft.IconButton(
                                        icon=ft.Icons.ARROW_BACK,
                                        icon_color=ft.Colors.BLACK,
                                        on_click=lambda _: page.go("/main_usuario")
                                    )
                                ),
                                ft.Column(
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    expand=True,
                                    controls=[
                                        fuente_input,
                                        procesar_switch,
                                        ft.ElevatedButton(
                                            text="Ejecutar subida",
                                            bgcolor=ft.Colors.GREEN,
                                            color=ft.Colors.WHITE,
                                            on_click=lambda _: ejecutar_subida_masiva(page, logica_app, fuente_input, procesar_switch)
                                        ),
                                        ft.ElevatedButton(
                                            text="Cancelar",
                                            bgcolor=ft.Colors.RED,
                                            color=ft.Colors.WHITE,
                                            on_click=lambda _: page.go("/main_usuario")
                                        ),
                                    ]
                                )
                            ]
                        )
                    )
            if page.route == "/main_usuario/experimentos":
                    experimentos = logica_app.obtener_experimentos()  

                    filas_experimentos = []
                    for exp in experimentos:
                        filas_experimentos.append(
                            ft.DataRow(
                                cells=[
                                    ft.DataCell(ft.Text(exp["nombre"])),
                                    ft.DataCell(
                                        ft.ElevatedButton(
                                            text="Ver Resultados",
                                            on_click=lambda e, exp=exp: (mostrar_cargando(page, True), page.update(), page.go(f"/main_usuario/experimentos/{exp['nombre']}")),
                                        )
                                    ),
                                ]
                            )
                        )

                    page.views.append(
                        ft.View(
                            "/main_usuario/experimentos",
                            [
                                ft.AppBar(
                                    title=ft.Text("Experimentos"),
                                    bgcolor=ft.Colors.GREEN,
                                    center_title=True,
                                    leading = ft.IconButton(
                                                icon = ft.Icons.ARROW_BACK,
                                                icon_color = ft.Colors.BLACK,
                                                on_click = lambda _: page.go("/main_usuario")
                                            )
                                ),
                                ft.Column(
                                    controls=[
                                        ft.DataTable(
                                            columns=[
                                                ft.DataColumn(ft.Text("Nombre del Experimento")),
                                                ft.DataColumn(ft.Text("Acciones")),
                                            ],
                                            rows=filas_experimentos,
                                        ),
                                        ft.ElevatedButton(
                                            text="Crear Nuevo Experimento",
                                            on_click=lambda _: page.go("/main_usuario/experimentos/crear"),
                                            bgcolor=ft.Colors.GREEN,
                                            color=ft.Colors.WHITE,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ],
                        )
                    )
                    mostrar_cargando(page, False)

            if page.route == "/main_usuario/experimentos/crear":
                    # Inputs para configurar el nuevo experimento
                    input_nombre_experimento = ft.TextField(
                        label="Nombre del experimento",
                        hint_text="Introduce un nombre único para el experimento",
                    )

                    dropdown_plantas = ft.Dropdown(
                        label="Plantas",
                        options=[
                            ft.dropdown.Option("all"),
                            ft.dropdown.Option("specific"),
                        ],
                        value="all",
                    )

                    dropdown_enfermedades = ft.Dropdown(
                        label="Enfermedades",
                        options=[
                            ft.dropdown.Option("all"),
                            ft.dropdown.Option("specific"),
                        ],
                        value="all",
                    )

                    dropdown_fuentes = ft.Dropdown(
                        label="Fuentes",
                        options=[
                            ft.dropdown.Option("PlantVillage"),
                            ft.dropdown.Option("Custom"),
                        ],
                        value="PlantVillage",
                    )

                    input_imagenes_por_clase = ft.TextField(
                        label="Imágenes por clase",
                        value="50",
                        keyboard_type=ft.KeyboardType.NUMBER,
                    )

                    dropdown_formato = ft.Dropdown(
                        label="Formato",
                        options=[
                            ft.dropdown.Option("Color"),
                            ft.dropdown.Option("Grayscale"),
                        ],
                        value="Color",
                    )

                    # Botón para crear el experimento
                    boton_crear_experimento = ft.ElevatedButton(
                        text="Crear Experimento",
                        on_click=lambda _: crear_experimento(
                            input_nombre_experimento.value,
                            {
                                "plantas": dropdown_plantas.value,
                                "enfermedades": dropdown_enfermedades.value,
                                "fuentes": [dropdown_fuentes.value],
                                "imagenes_por_clase": int(input_imagenes_por_clase.value),
                                "formato": dropdown_formato.value,
                            },
                            checkbox_entrenar_modelo.value,
                            page,
                        ),
                        bgcolor=ft.Colors.GREEN,
                        color=ft.Colors.WHITE,
                    )

                    checkbox_entrenar_modelo = ft.Checkbox(
                        label="Quiero entrenar este modelo",
                        value=False,
                    )

                    # Layout de la vista para crear un experimento
                    page.views.append(
                        ft.View(
                            "/main_usuario/experimentos/crear",
                            [
                                ft.AppBar(
                                    title=ft.Text("Crear Experimento"),
                                    center_title=True,
                                    bgcolor=ft.Colors.GREEN,
                                    leading=ft.IconButton(
                                        icon=ft.Icons.ARROW_BACK,
                                        on_click=lambda _: (mostrar_cargando(page, True), page.go("/main_usuario/experimentos")),
                                    ),
                                ),
                                ft.Column(
                                    controls=[
                                        input_nombre_experimento,
                                        dropdown_plantas,
                                        dropdown_enfermedades,
                                        dropdown_fuentes,
                                        input_imagenes_por_clase,
                                        dropdown_formato,
                                        checkbox_entrenar_modelo,
                                        boton_crear_experimento,
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ],
                        )
                    )
                    mostrar_cargando(page, False)
            # Aquí tendría que encontrar la forma de poner en la ruta el nombre específico del experimento
            elif page.route.startswith("/main_usuario/experimentos/"):
                    # Extraer el nombre del experimento de la ruta
                    nombre_experimento = page.route.split("/")[-1]

                    # Función para cargar los resultados del experimento
                    def cargar_resultados():
                        try:
                            resultados = logica_app.obtener_resultados_experimento(nombre_experimento)
                            if not resultados.get("success"):
                                return ft.Text(f"Error: {resultados.get('error')}")
                            
                            # Crear una lista de controles para mostrar los resultados
                            controles_resultados = []
                            for resultado in resultados.get("resultados", []):
                                controles_resultados.append(
                                    ft.Row(
                                        controls=[
                                            ft.Text(resultado["nombre"]),
                                            ft.ElevatedButton(
                                                text="Ver",
                                                on_click=lambda e, ruta=resultado["ruta"]: abrir_resultado(ruta),
                                            ),
                                        ]
                                    )
                                )
                            return ft.Column(controls=controles_resultados)
                        except Exception as e:
                            return ft.Text(f"Error al cargar los resultados: {str(e)}")

                    # Función para abrir un resultado (puedes personalizar esto según el tipo de archivo)
                    def abrir_resultado(ruta):
                        page.snack_bar = ft.SnackBar(ft.Text(f"Abriendo resultado: {ruta}"))
                        page.snack_bar.open()

                    # Layout de la vista
                    page.views.append(
                        ft.View(
                            page.route,
                            [
                                ft.AppBar(
                                    title=ft.Text(f"Resultados: {nombre_experimento}"),
                                    center_title=True,
                                    bgcolor=ft.Colors.GREEN,
                                    leading=ft.IconButton(
                                        icon=ft.Icons.ARROW_BACK,
                                        on_click=lambda _: (mostrar_cargando(page, True), page.update(), page.go("/main_usuario/experimentos")),
                                    ),
                                ),
                                cargar_resultados(),
                            ],
                        )
                    )
                    mostrar_cargando(page, False)

            page.update()
            if page.route.startswith("/registrarse"):
                page.views.append(
                    ft.View(
                        "/registrarse",
                        [
                            ft.AppBar(
                            title = ft.Text(nombre_app, size = 40, text_align= "end"),
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
                                        controls = [
                                            ft.Text(
                                                "Introduce los datos:",
                                                size=20,
                                            ),
                                            nombre_r,
                                            password_r_1,
                                            password_r_2,
                                            ft.ElevatedButton(
                                                "Registrarse",
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

            if page.route.startswith("/main_admin"):
                page.views.append(
                    ft.View(
                        "/main_admin",
                        [
                            ft.AppBar(
                                title = ft.Text(nombre_app, size = 40, text_align= "end"),
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
                                        controls = [
                                            ft.Text("Mostrar todos los usuarios:", size=18),
                                            ft.ElevatedButton(
                                                "Lista de usuarios",
                                                color= ft.Colors.WHITE,
                                                bgcolor = ft.Colors.GREEN,
                                                on_click=lambda _:buscar_usuarios()
                                            ),
                                            ft.Divider(),
                                            ft.Text(
                                                "Buscar usuarios:",
                                                size=18,
                                            ),
                                            ft.Text(
                                                "Buscar por nombre:",
                                                size=18,                                                 
                                            ),
                                            buscador_nombre_admin,
                                            ft.Text(
                                                "Filtrar por rol:",
                                                size=18, 
                                            ),
                                            buscar_usuario_rol_admin,
                                            ft.ElevatedButton(
                                                "Buscar",
                                                color= ft.Colors.WHITE,
                                                bgcolor = ft.Colors.GREEN,
                                                on_click=lambda _:buscar_usuarios(buscador_nombre_admin.value, buscar_usuario_rol_admin.value)
                                            ),
                                            ft.ElevatedButton(
                                                text="Ver solicitudes de entrenamiento",
                                                color= ft.Colors.WHITE,
                                                bgcolor = ft.Colors.BLUE,
                                                on_click=lambda _: (mostrar_cargando(page, True), page.go("/main_admin/entrenamientos"))
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
                                    controls= [
                                        icono_usuario
                                    ]
                                )
                            )
                        ]
                    )
                )
                if page.route.startswith("/main_admin/busqueda"):
                    page.views.append(
                        ft.View(
                            "/main_admin/busqueda",
                            [
                                ft.AppBar(
                                title = ft.Text(nombre_app, size = 40, text_align= "end"),
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
                                            controls = [
                                                ft.Text(
                                                    "Lista de usuarios:",
                                                    size=18,
                                                ),
                                                ft.DataTable(
                                                    columns = crear_columnas(logica_app.lista_usuarios),
                                                    rows = crear_filas(logica_app.lista_usuarios)
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
                                        controls= [
                                            icono_usuario
                                        ]
                                    )
                                )
                            ]
                        )
                    )
                    if page.route.startswith("/main_admin/busqueda/datos_usuario"):
                        page.views.append(
                            ft.View(
                                "/main_admin/busqueda/datos_usuario",
                                [
                                    ft.AppBar(
                                        title = ft.Text(nombre_app, size = 40, text_align= "end"),
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
                                                controls = [
                                                    ft.Text(
                                                        "Datos del usuario:",
                                                        size=18,
                                                    ),
                                                    ft.Divider(),
                                                    ft.Container(
                                                        content=ft.Column(
                                                            controls=info_usuario_seleccionado()
                                                        )
                                                    ),
                                                    ft.Divider(),
                                                    ft.ElevatedButton(
                                                        "Borrar usuario",
                                                        color = ft.Colors.WHITE,
                                                        bgcolor = ft.Colors.RED,
                                                        on_click = lambda _: page.open(alerta_borrar_usuario)
                                                    ),
                                                    ft.Divider(),
                                                    ft.Text(
                                                        "Modificar roles:",
                                                        size=16,
                                                    ),
                                                    selector_rol_editar_usuario,
                                                    ft.Row(
                                                        expand = True,
                                                        alignment = ft.MainAxisAlignment.CENTER,
                                                        vertical_alignment = ft.CrossAxisAlignment.START,
                                                        controls = [
                                                            ft.ElevatedButton(
                                                                "Eliminar rol",
                                                                color = ft.Colors.WHITE,
                                                                bgcolor = ft.Colors.RED,
                                                                on_click = lambda _: page.open(alerta_eliminar_rol)
                                                            ),
                                                            ft.ElevatedButton(
                                                                "Añadir rol",
                                                                color = ft.Colors.WHITE,
                                                                bgcolor = ft.Colors.RED,
                                                                on_click = lambda _: page.open(alerta_add_rol)
                                                            )
                                                        ]
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
                                            controls= [
                                                icono_usuario
                                            ]
                                        )
                                    )
                                ]
                            )
                        )
                if page.route.startswith("/main_admin/entrenamientos"):
                    solicitudes = logica_app.obtener_solicitudes_entrenamiento()
                    filas_solicitudes = []
                    for solicitud in solicitudes:
                        filas_solicitudes.append(
                            ft.DataRow(
                                cells=[
                                    ft.DataCell(ft.Text(solicitud["nombre"])),
                                    ft.DataCell(
                                        ft.ElevatedButton(
                                            text="Entrenar",
                                            on_click=lambda e, solicitud=solicitud: (
                                                page.open(
                                                    ft.AlertDialog(
                                                        modal=True,
                                                        title=ft.Text("Entrenamiento en progreso"),
                                                        content=ft.Text("El entrenamiento puede tardar un tiempo. Por favor, espere."),
                                                        actions=[],
                                                    )
                                                ),
                                                entrenar_modelo(solicitud["nombre"])
                                            ),
                                        ),
                                    ),
                                ]
                            )
                        )

                    page.views.append(
                        ft.View(
                            "/main_admin/entrenamientos",
                            [
                                ft.AppBar(
                                    title=ft.Text("Solicitudes de Entrenamiento"),
                                    center_title=True,
                                    bgcolor=ft.Colors.GREEN,
                                    leading = ft.IconButton(
                                                icon = ft.Icons.ARROW_BACK,
                                                icon_color = ft.Colors.BLACK,
                                                on_click = lambda _: page.go("/main_admin")
                                    )
                                ),
                                ft.DataTable(
                                    columns=[
                                        ft.DataColumn(ft.Text("Nombre del Experimento")),
                                        ft.DataColumn(ft.Text("Acciones")),
                                    ],
                                    rows=filas_solicitudes,
                                ),
                            ],
                        )
                    )
                    mostrar_cargando(page, False)
            page.update()

        

        page.on_route_change = route_change
        page.on_view_pop = view_pop
        page.go(page.route)
        
    ft.app(main)