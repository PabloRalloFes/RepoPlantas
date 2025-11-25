# Clasificación de enfermedades de plantas mediante visión por computador/ Sistema de recopilación y etiquetado de imágenes de hojas de plantas

Este repositorio forma parte del Trabajo de Fin de Grado (TFG) en Ciencia de Datos en la Universitat Politècnica de València.  
El proyecto desarrolla una aplicación completa para recopilar, almacenar y etiquetar imágenes de hojas de plantas sanas y enfermas, combinando el dataset PlantVillage con imágenes reales tomadas mediante una app propia.

El sistema integra una API Flask para la gestión de imágenes y usuarios, y una aplicación de escritorio desarrollada con Flet (Python) que permite interactuar con la base de datos de manera intuitiva.


---

## 📦 Estructura general

```
data/
├── Imported/
│   └── {fuente}/
│       ├── color/
│       ├── grayscale/
│       └── segmented/
├── PlantVillage/
│   ├── color/
│   ├── grayscale/
│   └── segmented/
experiments/
├── BASE
│   ├── data/
│   ├── models/
│   ├── results/
│   ├── config.yaml
│   └── run_experiment.py
...
models/
### modelos entrenados
notebooks/
├── legacy/
├── comprobaciones_imagenes.ipynb
├── EDA.ipynb
└── misclassified_and_topk.ipynb
scripts/
├── legacy/
├── add_class.py
├── compare_experiments.py
├── convert_to_grayscale.py
├── editar_clases.py
├── make_experiment.py
├── predict_image.py
├── process_imported_images.py
├── reemplazar_clases.py
├── segment_leaves.py
├── setup_bbdd.py
├── subir_imagenes_nueva_fuente.py
└── upload_images.py
src/
├── assets/
    ├── icon.png
    └── logos.png
├── campos.json
├── clases_combinadas.json
├── clases.json
└── etiquetas.json
utils/
├── data.py
├── database.py
├── io.py
├── model.py
└── train.py
main.py
main_app.py
logicav3.py
pyproject.toml
requirements.txt
```

---

## 🧩 Arquitectura general del sistema

El proyecto se organiza en dos componentes principales que trabajan de forma complementaria:

### 1. 🌿 Aplicación y API Flask (recopilación y gestión de datos)
Esta parte del sistema permite recopilar y gestionar imágenes de hojas de plantas, así como los usuarios y roles que interactúan con la base de datos.  
Está formada por tres módulos principales:

- **`main.py`** → API Flask unificada que gestiona la base de datos MongoDB.  
  - Endpoints para subir imágenes, recuperar etiquetas, clasificar hojas, y gestionar usuarios.  
  - Funciona como servidor backend y punto de conexión con la aplicación Flet.

- **`main_app.py`** → Aplicación gráfica desarrollada con [Flet](https://flet.dev/).  
  - Permite el registro e inicio de sesión de usuarios.  
  - Ofrece interfaces separadas para los tres roles principales:
    - *Usuario:* subir imágenes y asignar etiquetas.
    - *Etiquetador:* validar imágenes pendientes.
    - *Administrador:* gestionar usuarios y roles.

- **`logicav3.py`** → Módulo de conexión entre la app y la API.  
  - Envía peticiones HTTP (`httpx`) a la API.  
  - Codifica imágenes a base64 antes de subirlas.  
  - Gestiona la autenticación, las búsquedas de usuarios y el flujo de datos en memoria.

El flujo de funcionamiento es el siguiente:
[Usuario / Etiquetador / Administrador]
│
▼
┌────────────────────┐
│ Aplicación Flet │
│ (main_app.py) │
└────────────────────┘
│ JSON / HTTP (httpx)
▼
┌────────────────────┐
│ API Flask │
│ (main.py) │
└────────────────────┘
│
▼
┌────────────────────────┐
│ Base de datos MongoDB │
│ ├─ appPlantas (usuarios)
│ └─ Repositorio_Plantas (imágenes)
└────────────────────────┘
│
▼
┌─────────────────────────────┐
│ Módulo experimental (CNN) │
│ ├─ Entrenamiento MobileNetV2
│ └─ Uso del dataset PlantVillage
└─────────────────────────────┘

---

### 2. 🤖 Módulo de modelo y experimentación (entrenamiento y evaluación)
Esta parte contiene los scripts y notebooks para entrenar y evaluar modelos de clasificación, basados en arquitecturas **CNN** (principalmente MobileNetV2).  
Utiliza tanto el dataset **PlantVillage** como las imágenes recopiladas mediante la app.

Los experimentos se organizan por carpetas dentro de `experiments/` y pueden configurarse mediante ficheros `config.yaml`.  
Esta estructura permite reproducir distintos escenarios de entrenamiento o comparar configuraciones de datos y modelos.

---

Ambas partes del proyecto están conectadas por su propósito común:  
👉 **generar un sistema de clasificación de enfermedades de plantas robusto y adaptado a condiciones reales.**

## 🧩 Parte A — Aplicación y API Flask

Esta parte del proyecto implementa el sistema de **recopilación, almacenamiento y etiquetado de imágenes**, junto con la **gestión de usuarios y roles**.  
Permite registrar nuevos usuarios, subir imágenes desde la app, validar etiquetas y administrar la base de datos de forma visual.

---

### ⚙️ Componentes principales

| Archivo | Descripción |
|----------|--------------|
| **`main.py`** | Contiene la **API Flask unificada**, que gestiona la comunicación con la base de datos MongoDB. Incluye endpoints para el registro e inicio de sesión de usuarios, subida y consulta de imágenes, validación de etiquetas y administración de roles. |
| **`main_app.py`** | Implementa la **interfaz gráfica** mediante el framework [Flet](https://flet.dev/). Ofrece distintas vistas según el rol del usuario (*usuario*, *etiquetador* o *administrador*). Permite interactuar directamente con la API sin necesidad de scripts manuales. |
| **`logicav3.py`** | Define la clase `LogicaApp`, que actúa como **puente entre la app y la API Flask**. Gestiona la creación de URLs, el envío de peticiones HTTP, el tratamiento de respuestas y la conversión de imágenes a formato base64 antes de su envío. |

---

### 🧠 Roles de usuario

| Rol | Funcionalidad principal |
|------|---------------------------|
| 🧑‍🌾 **Usuario** | Subir imágenes y asignar etiquetas. |
| 🧩 **Etiquetador** | Validar y corregir imágenes pendientes. |
| ⚙️ **Administrador** | Gestionar usuarios, roles y contraseñas. |

---

### 🚀 Ejecución en entorno local

1. **Iniciar MongoDB**  
   Asegúrate de tener un servidor MongoDB ejecutándose en `mongodb://localhost:27017/`.

2. **Ejecutar la API Flask**  
   En una terminal dentro del proyecto:
   ```bash
   python main.py
   ```
   Esto levantará el servidor en http://127.0.0.1:5001

3. **Ejecutar la aplicación Flet**
   En otra terminal:
   ```bash
   python main.py
   ```
   La aplicación se abrirá en una ventana de escritorio o en el navegador.

### 🧩 Integración futura
   En próximas versiones, la aplicación incluirá nuevas funcionalidades actualmente gestionadas por scripts. Además, será de acceso público mediante un entorno virtual de la universidad y tendrá versión para móviles.


## 🤖 Parte B: Modelo predictivo y experimentación

El proyecto incluye un pipeline completo para crear y gestionar la base de datos de imágenes mediante scripts de python.

💡 Nota: asegúrate de ajustar la IP en logicav3.py (atributo self.url_api) al entorno donde se ejecuta la API Flask.
Si trabajas en local, usa http://127.0.0.1:5001

### 1. Inicialización de la base de datos

Antes de trabajar con las imágenes, es necesario crear en MongoDB la estructura básica de colecciones y etiquetas.

Puedes hacerlo fácilmente ejecutando el siguiente script:

```
python scripts/setup_bbdd.py
```


Esto creará automáticamente:

- Las colecciones necesarias (`Clases`, `Docs`, `Formato`, `Fuente`, etc.).
- Las etiquetas básicas como `Color`, `Grayscale` y `Segmented`.
- El registro de todas las clases disponibles en PlantVillage a partir de `clases.json`.

⚠️ Asegúrate de que el servidor de MongoDB (`main.py`) esté en ejecución antes de lanzar este paso.

---

### 2. Subida de imágenes de PlantVillage

Una vez creada la base de datos, puedes subir todas las imágenes del dataset PlantVillage en los tres formatos disponibles ejecutando:

```
python scripts/upload_images.py Color
python scripts/upload_images.py Grayscale
python scripts/upload_images.py Segmented
```


Este script:
- Procesa las imágenes si no están generadas (escala de grises y segmentadas).
- Sube las imágenes a la base de datos local.
- Registra en logs las imágenes ya subidas para evitar duplicados en futuras ejecuciones.

---

### 3. Preparación manual de imágenes externas

Si quieres añadir imágenes reales (por ejemplo, tomadas con una app móvil o recopiladas manualmente), debes colocarlas manualmente en la siguiente ruta:

```
data/Imported/{nombre_fuente}/color/
```

Donde `{nombre_fuente}` identifica la fuente (por ejemplo, `proyecto_movil`, `agricultura_europa2025`, etc.).

Estas imágenes deben estar organizadas por carpetas con el nombre exacto de cada clase (enfermedad), igual que en PlantVillage: {planta}___{nombre_comun}. Ejemplo:

```
data/Imported/mi_fuente/color/Tomato___Early_blight/
├── img1.jpg
├── img2.jpg
```

Esto permite que el sistema asocie automáticamente cada imagen con su clase correspondiente durante la subida.

---

### 4. Procesamiento y subida automática de nuevas fuentes

Una vez colocadas las imágenes, puedes ejecutar todo el pipeline de procesamiento y subida con un solo comando:

```
python scripts/subir_imagenes_nueva_fuente.py --fuente nombre_fuente
```

Este script realiza automáticamente:
- Registro de la fuente en la base de datos (si aún no existe).
- Procesamiento de las imágenes en color para generar versiones `grayscale/` y `segmented/`.
- Redimensionado y conversión a JPG.
- Subida de los tres formatos (`color`, `grayscale`, `segmented`) con la metainformación correspondiente (`fuente`, `formato`).
- Control de duplicados mediante logs por formato.

> También puedes ejecutar solo el procesamiento (sin subir) con:
>
> ```
> python scripts/process_imported_images.py --fuente nombre_fuente
> ```
>
> Esto es útil si quieres revisar las imágenes procesadas antes de subirlas.


## 🧪 Experimentos reproducibles y automatizados

El proyecto permite lanzar experimentos completos de forma modular y automatizada. Cada experimento se define dentro de una carpeta:

```
experiments/{nombre_experimento}/
```

Esta carpeta debe contener:

- `config.yaml`: configuración del experimento, incluyendo clases seleccionadas, fuentes de datos, formato, número de imágenes por clase, hiperparámetros del modelo, etc.
- `run_experiment.py`: script que ejecuta todo el pipeline (preparación de datos, entrenamiento y evaluación).

Con estos 2 ficheros es suficiente para ejecutar un experimento, que generaría lo siguiente: 

- `data/`: CSVs generados automáticamente con las rutas a imágenes para entrenamiento, validación y test.
- `models/`: carpeta donde se guarda el modelo entrenado (`best_model.pth`).
- `results/`: métricas, gráficas, matrices de confusión y logs de evaluación.

Esto permite comparar fácilmente diferentes configuraciones (por ejemplo, cambios en los datos, preprocesamiento, arquitectura, entrenamiento...), sin modificar el código base del proyecto. En la carpeta experiments/BASE se encuentran plantillas de los 2 únicos ficheros necesarios.

Toda la lógica del pipeline está dividida en módulos reutilizables dentro de `utils/` y `scripts/`, lo que facilita su mantenimiento y escalabilidad.


## 📓 Scripts/Notebooks auxiliares

- **analyze_experiments.py**: Script para comparar métricas entre varios experimentos. Permite analizar y visualizar resultados de diferentes configuraciones de entrenamiento. *Quiero mejorar los gráficos para una visualización más clara y comparativa.*
- **notebook o script para mostrar imágenes mal clasificadas y top-k predicciones**: Herramienta para analizar visualmente los errores del modelo y consultar las top-k predicciones para una imagen concreta. Útil para depuración y análisis cualitativo de los resultados.

Estos recursos se encuentran en la carpeta `scripts/` o `notebooks/` y sirven de apoyo para el análisis y la interpretación de los experimentos realizados.

---

### ⚠️ Consideraciones para la selección de clases

En algunos cultivos del dataset PlantVillage (`Blueberry`, `Orange`, `Raspberry`, `Soybean` y `Squash`) solo hay una clase disponible (por ejemplo, solo hojas sanas). Por este motivo, se recomienda excluir esos cultivos en los experimentos, ya que no permiten aprender a distinguir entre clases.

Este criterio puede cambiar si en el futuro se incorporan imágenes reales que amplíen el número de clases posibles para esos cultivos.


---

## 🔧 Requisitos

- Python ≥ 3.10
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
- El script `upload_images.py` maneja por sí solo la creación de versiones en `grayscale` y `segmented` si no existen, llamando a `process_imported_images.py` automáticamente.
- Los scripts en scripts/legacy han sido usados de manera auxiliar y el usuario final con toda seguridad no necesitará utilizarlos. Por ejemplo, dividir_clases.py solo es necesario si ya se habían insertado clases antiguas sin los campos cultivo y enfermedad y eliminar_nombre.py si hay una variable de la coleccion Clases que se quiere eliminar (en este caso nombre).
- Si se dispone de una GPU compatible, se recomienda instalar PyTorch con soporte CUDA desde https://pytorch.org/get-started/locally para acelerar el entrenamiento.
- Las imágenes se almacenan físicamente en una carpeta local del proyecto (`data/`, `imagenes/`, etc.), mientras que en la base de datos solo se guardan los campos asociados y las rutas relativas a las imágenes. Esto optimiza el almacenamiento y facilita la gestión de grandes volúmenes de datos.
- La seguridad y autenticación se implementan actualmente de forma básica (hash propio). Se recomienda migrar a bcrypt y añadir control de sesiones o JWT antes de un despliegue público.
- CUIDADO CON LOS LOGS AL REPETIR SUBIDAS MASIVAS. En los logs se guardan las rutas originales de las imagenes que ya has subido masivamente. Si quisieras volver a subir una o varias imágenes que ya has subido masivamente, tendrías que eliminarla de la base de datos y borrar los logs. 
- Si has subido masivamente sin procesar y después quieres subir las imágenes procesadas también, simplemente vuelve utilizar la funcion de subir masivamente para esa fuente pero esta vez activando el switch.
---

