# Clasificación de enfermedades de plantas mediante visión por computador

Este repositorio forma parte de un Trabajo de Fin de Grado (TFG) de Ciencia de Datos en la Universitat Politècnica de València. Su objetivo es entrenar y evaluar modelos de clasificación de enfermedades de plantas a partir de imágenes, combinando el dataset PlantVillage (en condiciones controladas) con imágenes tomadas en entornos reales.

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
└── EDA.ipynb
scripts/
├── legacy/
├── add_class.py
├── convert_to_grayscale.py
├── editar_clases.py
├── predict_image.py
├── process_imported_images.py
├── reemplazar_clases.py
├── segment_leaves.py
├── setup_bbdd.py
├── subir_imagenes_nueva_fuente.py
└── upload_images.py
src/
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
requirements.txt
```

---

## ⚙️ Descripción del pipeline

El proyecto incluye un pipeline completo para crear y gestionar la base de datos de imágenes:

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

Estas imágenes deben estar organizadas por carpetas con el nombre exacto de cada clase (enfermedad), igual que en PlantVillage. Ejemplo:

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
> python utils/process_imported_images.py --fuente nombre_fuente
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

Esto permite comparar fácilmente diferentes configuraciones (por ejemplo, cambios en los datos, preprocesamiento, arquitectura, entrenamiento...), sin modificar el código base del proyecto.

Toda la lógica del pipeline está dividida en módulos reutilizables dentro de `utils/` y `scripts/`, lo que facilita su mantenimiento y escalabilidad.

---

### ⚠️ Consideraciones para la selección de clases

En algunos cultivos del dataset PlantVillage (como `Orange` o `Raspberry`) solo hay una clase disponible (por ejemplo, solo hojas sanas). Por este motivo, se recomienda excluir esos cultivos en los experimentos, ya que no permiten aprender a distinguir entre clases.

Este criterio puede cambiar si en el futuro se incorporan imágenes reales que amplíen el número de clases posibles para esos cultivos.


---

## 🔧 Requisitos

- Python 3.8+
- OpenCV (`cv2`)
- pandas
- requests
- tqdm

---

> 📌 Nota sobre la terminología:
> - Un **campo** es un atributo como `fuente`, `formato` o `clase`.
> - Una **etiqueta** es un valor permitido dentro de un campo, definido con estructura y tipo.
> - Una **clase** es la categoría principal de una imagen: combinación de cultivo y enfermedad. Se almacena en la colección `Clases`.

## 📌 Notas finales

- La segmentación implementada se inspira en el artículo original de PlantVillage, aunque no es idéntica.
- Este repositorio está diseñado para ser extensible: se puede adaptar fácilmente para nuevas fuentes, cambios en el modelo o nuevas estrategias de evaluación.
- El script `upload_images.py` maneja por sí solo la creación de versiones en `grayscale` y `segmented` si no existen, llamando a `process_imported_images.py` automáticamente.
- Los scripts en scripts/legacy han sido usados de manera auxiliar y el usuario final con toda seguridad no necesitará utilizarlos. dividir_clases.py solo es necesario si ya se habían insertado clases antiguas sin los campos cultivo y enfermedad y eliminar_nombre.py si hay una variable de la coleccion Clases que se quiere eliminar (en este caso nombre).
- Si se dispone de una GPU compatible, se recomienda instalar PyTorch con soporte CUDA desde https://pytorch.org/get-started/locally para acelerar el entrenamiento.

---

