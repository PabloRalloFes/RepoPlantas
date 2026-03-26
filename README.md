# 🌿 PlantAID - Sistema de Clasificación de Enfermedades de Plantas

Herramienta para recopilar, etiquetar y clasificar imágenes de hojas de plantas sanas y enfermas.

**Trabajo de Fin de Grado (TFG)** en Ciencia de Datos - Universitat Politècnica de València

---

## 🚀 ¿Qué quieres hacer?

Selecciona tu rol para ir a la documentación correcta:

### 👤 **Soy usuario final - Quiero descargar y usar la aplicación**

Sin conocimientos técnicos. Paso a paso.

[**→ Ir a docs/USUARIO.md**](docs/USUARIO.md)

---

### 👨‍💻 **Soy desarrollador - Quiero entender o modificar el código**

Instalación de entorno, estructura del proyecto, cómo ejecutar en local.

[**→ Ir a docs/DESARROLLO.md**](docs/DESARROLLO.md)

---

### 🐳 **Quiero desplegar en servidor o usar Docker**

Docker Compose, variables de entorno, producción.

[**→ Ir a docs/DOCKER.md**](docs/DOCKER.md)

---




## 🧩 Arquitectura general del sistema

El proyecto se organiza en dos componentes principales que trabajan de forma complementaria:

### 1. 🌿 Aplicación y API Flask (recopilación y gestión de datos)
Esta parte del sistema permite recopilar y gestionar imágenes de hojas de plantas, así como los usuarios y roles que interactúan con la base de datos. Además, da una app para experimentar y explorar las posibilidades del proyecto. 
Está formada por tres módulos principales:

- **`main.py`** → API Flask que gestiona la base de datos MongoDB.  
  - Endpoints para subir imágenes, recuperar etiquetas, clasificar hojas y gestionar usuarios.  
  - Funciona como servidor backend y punto de conexión con la aplicación Flet.

- **`main_app.py`** → Aplicación gráfica desarrollada con [Flet](https://flet.dev/).  
  - Permite el registro e inicio de sesión de usuarios.  
  - Ofrece interfaces separadas para los tres roles principales:
    - *Usuario:* subir imágenes y ver experimentos.
    - *Etiquetador:* clasificar y validar imágenes pendientes.
    - *Administrador:* gestionar usuarios y roles.

- **`logicav3.py`** → Módulo de conexión entre la app y la API.  
  - Envía peticiones HTTP (`httpx`) a la API.  
  - Codifica imágenes a base64 antes de subirlas.  
  - Gestiona la autenticación, las búsquedas de usuarios y el flujo de datos en memoria.

El flujo de funcionamiento es el siguiente:
1. **Usuario / Etiquetador / Administrador** interactúa con el sistema.
2. Utiliza la **Aplicación Flet** (`main_app.py`).
3. La app se comunica vía JSON/HTTP (`httpx`) con la **API Flask** (`main.py`).
4. La **API Flask** gestiona la **Base de datos MongoDB**:
  - `appPlantas` (usuarios)
  - `Repositorio_Plantas` (imágenes)
5. El módulo experimental (CNN) utiliza los datos para:
  - Entrenamiento MobileNetV2
  - Uso del dataset PlantVillage

---

### 2. 🤖 Módulo de modelo y experimentación (entrenamiento y evaluación)
Esta parte contiene los scripts y notebooks para entrenar y evaluar modelos de clasificación, basados en arquitecturas **CNN** (principalmente MobileNetV2).  
Utiliza tanto el dataset **PlantVillage** como las imágenes recopiladas mediante la app y aportadas por la facultad de agrónomos.

Los experimentos se organizan por carpetas dentro de `experiments/` y pueden configurarse mediante ficheros `config.yaml`.  
Esta estructura permite reproducir distintos escenarios de entrenamiento o comparar configuraciones de datos y modelos.

---

Ambas partes del proyecto están conectadas por su propósito común:  
👉 **generar un sistema de clasificación de enfermedades de plantas robusto y adaptado a condiciones reales.**

---

### ⚠️ Consideraciones para la selección de clases

En algunos cultivos del dataset PlantVillage (`Blueberry`, `Orange`, `Raspberry`, `Soybean` y `Squash`) solo hay una clase disponible (por ejemplo, solo hojas sanas). Por este motivo, se recomienda excluir esos cultivos en los experimentos, ya que no permiten aprender a distinguir entre clases.

Este criterio puede cambiar si en el futuro se incorporan imágenes reales que amplíen el número de clases posibles para esos cultivos.


---

## 🔧 Requisitos

- Python ≥ 3.11
- MongoDB ≥ 6.0 (servidor local o remoto)
- Librerías en requirements.txt

---

> 📌 Nota sobre la terminología:
> - Un **campo** es un atributo como `fuente`, `formato` o `clase`.
> - Una **etiqueta** es un valor permitido dentro de un campo, definido con estructura y tipo.
> - Una **clase** es la categoría principal de una imagen: combinación de cultivo y enfermedad. Se almacena en la colección `Clases`.

## 📌 Notas finales

- La segmentación implementada se inspira en el artículo original de PlantVillage (Mohanty et al. 2016), aunque no es idéntica.
- Este repositorio está diseñado para ser extensible: se puede adaptar fácilmente para nuevas fuentes, cambios en el modelo o nuevas estrategias de evaluación.
- Los scripts en scripts/legacy han sido usados de manera auxiliar y el usuario final con toda seguridad no necesitará utilizarlos. Por ejemplo, dividir_clases.py solo es necesario si ya se habían insertado clases antiguas sin los campos cultivo y enfermedad y eliminar_nombre.py si hay una variable de la colección Clases que se quiere eliminar (en este caso nombre).
- Si se dispone de una GPU compatible, se recomienda instalar PyTorch con soporte CUDA desde https://pytorch.org/get-started/locally para acelerar el entrenamiento.
- Las imágenes se almacenan físicamente en una carpeta local del proyecto (`data/`, `imagenes/`, etc.), mientras que en la base de datos solo se guardan los campos asociados y las rutas relativas a las imágenes. Esto optimiza el almacenamiento y facilita la gestión de grandes volúmenes de datos.
- CUIDADO CON LOS LOGS AL REPETIR SUBIDAS MASIVAS. En los logs se guardan las rutas originales de las imagenes que ya has subido masivamente. Si quisieras volver a subir una o varias imágenes que ya has subido masivamente, tendrías que eliminarla de la base de datos y borrar los logs. 
- Si has subido masivamente sin procesar y después quieres subir las imágenes procesadas también, simplemente vuelve utilizar la funcion de subir masivamente para esa fuente pero esta vez activando el switch.
---

