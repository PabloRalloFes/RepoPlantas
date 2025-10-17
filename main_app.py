import flet as ft
import logicav3 as logica

nombre_app = "Aplicación Plantas"


if __name__ == "__main__":

    logica_app = logica.LogicaApp()

    def main(page: ft.Page):
        page.title = nombre_app

        page.theme = ft.Theme(color_scheme_seed=ft.Colors.GREEN)
        page.dark_theme = ft.Theme(color_scheme_seed=ft.Colors.GREEN)

        def view_pop(view):
            page.views.pop()
            top_view = page.views[-1]
            page.go(top_view.route)
        
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

        '''
        def buscar_usuario_admin_cambio(e):
            buscador_nombre_admin.visible = False if e.control.value is None else True
            buscador_nombre_admin.value=""
            page.update()
        '''

        buscador_nombre_admin = ft.TextField(
            label="Introducir nombre",
            visible=True,
        )
        '''
        buscar_usuario_admin = ft.RadioGroup(
            content=ft.Row(
                [
                    ft.Radio(value=None, label="No filtrar por nombre"),
                    ft.Radio(value="nombre", label="Nombre de usuario"),
                    #ft.Radio(value="nombres_antiguos", label="Nombre antiguo de usuario"),
                ]
            ),
            on_change = buscar_usuario_admin_cambio
        )
        '''

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
                if logica_app.inicio_sesion(nombre, password, rol):
                    if rol == "etiquetador": cargar_datos_no_validados()
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
                if logica_app.registro(nombre, password_1):
                    alerta_registro_correcto = ft.AlertDialog(
                        modal = True,
                        title = ft.Text("Registro completado"),
                        content = ft.Text("Por favor inicie sesión"),
                        actions=[
                            ft.TextButton("Aceptar", on_click= view_pop)
                        ]
                    )
                    page.open(alerta_registro_correcto)
                else:
                    alerta_usuario_existente = ft.AlertDialog(
                        modal = True,
                        title = ft.Text("No se ha podido completar el registro"),
                        content = ft.Text("Nombre de usuario ya en uso"),
                        actions=[
                            ft.TextButton("Aceptar", on_click= lambda _: page.close(alerta_usuario_existente))
                        ]
                    )
                    page.open(alerta_usuario_existente)
            for x in campos_borrar: x.value = ""
            page.update()

        def seleccionar_usuario(e):
            logica_app.seleccionar_usuario(e.cells[0].content.value)
            page.go("/main_admin/busqueda/datos_usuario")

        def info_usuario_seleccionado():
            info = []
            keys_usuario = list(logica_app.usuario_seleccionado.keys())
            values_usuario = list(logica_app.usuario_seleccionado.values())

            for i in range(len(keys_usuario)):
                texto = f"{keys_usuario[i]}:"
                if type(values_usuario[i]) is int and keys_usuario[i].startswith("rol_"):
                    si = "Sí"
                    no = "No"
                    texto += f"{si if values_usuario[i] == 1 else no}"
                else:
                    texto += f"{values_usuario[i]}"

                info.append(
                    ft.Text(
                        texto
                    )
                )
            return info

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
                        on_long_press=lambda e: seleccionar_usuario(e.control)
                    )
                )

            return filas

        def eliminar_usuario():
            logica_app.eliminar_usuario(logica_app.usuario_seleccionado)
            logica_app.busqueda_anterior()
            page.update()
            view_pop(page.views[-1])
            page.update()

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
            logica_app.eliminar_rol(logica_app.usuario_seleccionado['nombre'], selector_rol_editar_usuario.value)
            page.close(alerta_eliminar_rol)
            page.update()
            logica_app.busqueda_anterior()

        def add_rol():
            logica_app.add_rol(logica_app.usuario_seleccionado['nombre'], selector_rol_editar_usuario.value)
            page.close(alerta_add_rol)
            page.update()
            logica_app.busqueda_anterior()

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
                                    #color=ft.Colors.BLACK
                                ),
                                ft.Divider(),
                                ft.Text(
                                    f"Nombre de usuario: {logica_app.usuario['nombre']}",
                                    size=16,
                                    #color=ft.Colors.BLACK
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
                                    on_click=lambda e: page.close(e.control.parent.parent.parent) # línea favorita
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
            
            logica_app.seleccionar_archivo(e.control.data)
            dropdown_etiquetar_options(logica_app.archivo_seleccionado["clase"])
            page.go("/main_etiquetador/etiquetar")
           

        def avanzar_imagenes(reverso=False):
            if logica_app.avanzar_puntero_repo(reverso):
                cargar_datos_no_validados()
            
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

        def dropdown_etiquetar_options(opcion_por_defecto=None):
            etiquetas_procesadas = logica_app.procesar_nombre_key_etiquetas()

            # Limpiar opciones anteriores
            dropdown_etiquetar.options.clear()

            for ep in etiquetas_procesadas:
                dropdown_etiquetar.options.append(ft.dropdown.Option(key=ep["key"], text=ep["texto"]))

            dropdown_etiquetar.value=opcion_por_defecto

        def deseleccionar_etiqueta_dropdown(e):
            dropdown_etiquetar.value=None
            page.update()

        dropdown_etiquetar = ft.Dropdown(
            label="Sin clasificar",
        )


        alerta_imagen_etiquetada = ft.AlertDialog(
            modal = True,
            title = ft.Text("Imagen etiquetada correctamente"),
            actions = [
                ft.TextButton(
                    "Aceptar",
                    on_click = lambda _: view_pop(page.views[-1])
                )
            ]
        )

        def etiquetar_imagen():
            id_etiqueta = int(dropdown_etiquetar.value)
            res = logica_app.etiquetar_imagen(id_etiqueta)
            cargar_datos_no_validados()

            if res:
                page.open(alerta_imagen_etiquetada)

        def on_image_selected(e: ft.FilePickerResultEvent):
            if e.files:
                with open(e.files[0].path, "rb") as f:
                    img_bytes = f.read()
                    logica_app.procesar_foto(img_bytes)
                    dropdown_etiquetar_options()
                    page.go("/main_usuario/foto")

        file_picker = ft.FilePicker(on_result=on_image_selected)
        page.overlay.append(file_picker)

        def subir_foto():
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
                                            #color=ft.Colors.BLACK
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
                                            #color=ft.Colors.BLACK
                                        ),
                                        ft.Text(
                                            "Seleccionar rol:",
                                            size = 12,
                                            #color=ft.Colors.BLACK
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
            if page.route.startswith("/main_etiquetador"):
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
                                                ft.ElevatedButton(text="Anterior", on_click=lambda _: retroceder_imagenes()),
                                                ft.ElevatedButton(text="Siguiente", on_click=lambda _: avanzar_imagenes()),
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
                if page.route.startswith("/main_etiquetador/etiquetar"):
                    page.views.append(
                        ft.View(
                            "/main_etiquetador/etiquetar",
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
            if page.route.startswith("/main_usuario"):
                page.views.append(
                    ft.View(
                        "/main_usuario",
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
                                                ft.ElevatedButton(
                                                    adaptive= True,
                                                    bgcolor = ft.Colors.GREEN,
                                                    color = ft.Colors.WHITE,
                                                    text = "SELECCIONAR FOTO",
                                                    on_click=lambda _: file_picker.pick_files(allow_multiple=False)
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
                if page.route.startswith("/main_usuario/foto"):
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
                                                                on_click=view_pop
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
                                                #color=ft.Colors.BLACK
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
                                            #buscar_usuario_admin,
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
                                                    #color=ft.Colors.BLACK,
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
                                                        #color=ft.Colors.BLACK,
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
                                                        #color=ft.Colors.BLACK
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

            page.update()

        


        page.on_route_change = route_change
        page.on_view_pop = view_pop
        page.go(page.route)
        
    ft.app(main)

