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
├── Real/
│   └── App/
│       ├── color/
│       ├── grayscale/
│       └── segmented/
├── PlantVillage/
│   ├── color/
│   ├── grayscale/
│   └── segmented/
utils/
├── convert_to_grayscale.py
├── segment_leaves.py
├── upload_images.py
main.py
process_imported_images.py
subir_imagenes_nueva_fuente.py
models/
### modelos entrenados
src/
### archivos auxiliares, mirar de cambiar
```

---

## ⚙️ Descripción del pipeline

El proyecto incluye un pipeline completo para incorporar imágenes externas (reales o de otras fuentes) al sistema:

### 1. Preparación manual de las imágenes

El punto de partida es tener imágenes externas descargadas manualmente o por otros medios. Para integrarlas en el sistema, se deben colocar en la siguiente ruta:

```
data/Imported/{nombre_fuente}/color/
```

Donde `{nombre_fuente}` identifica la fuente (por ejemplo, `agricultura_europa2025`, `proyecto_movil`, etc.).

Estas imágenes deben estar organizadas por carpetas con el nombre exacto de cada clase (enfermedad), igual que en PlantVillage. Ejemplo:

```
data/Imported/mi_fuente/color/Tomato___Early_blight/
                                        ├── img1.jpg
                                        ├── img2.jpg
```

Esto permite que el sistema asocie automáticamente cada imagen con su clase correspondiente durante la subida.

### 2. Procesamiento y subida automática

## 🧩 Inicialización de la base de datos

Antes de empezar a trabajar con las imágenes, es necesario inicializar la base de datos local con la estructura básica de campos y etiquetas.

Puedes hacerlo fácilmente ejecutando el siguiente script:

```bash
python setup_database.py
```

Esto creará automáticamente:

- Las colecciones necesarias (Campos, Docs, Fuente, Formato, Clase, etc.).

- Las etiquetas básicas para formato (Color, Grayscale, Segmented) y otras categorías.

- Los metadatos necesarios para que el sistema pueda validar y clasificar imágenes correctamente.

⚠️ Asegúrate de que el servidor MongoDB (main.py) esté en ejecución antes de lanzar el script.


Una vez colocadas las imágenes y creada la base de datos, puedes ejecutar todo el pipeline de subida con un solo comando:

```bash
python subir_imagenes_nueva_fuente.py --fuente nombre_fuente
```

Este script realiza automáticamente:
- Registro de la fuente en la base de datos (si aún no existe).
- Procesamiento de las imágenes en color para generar versiones en escala de grises (`grayscale/`) y segmentadas (`segmented/`), redimensionadas y en formato JPG.
- Subida de los tres formatos a la base de datos, incluyendo metainformación `fuente` y `formato`.
- Evita duplicados mediante logs por formato.

> También puedes ejecutar solo el procesamiento con:
>
> ```bash
> python utils/process_imported_images.py --fuente nombre_fuente
> ```
>
> Esto es útil si quieres revisar las imágenes procesadas antes de subirlas.

---

## 🧪 Cómo añadir una nueva fuente

1. Crea una nueva carpeta dentro de `data/Imported/` con el nombre de la fuente.
2. Dentro de esa carpeta, añade las imágenes organizadas por clase en `color/`. Si hay alguna clase nueva (que no aparezca en `clases.json`), se añadirá automáticamente durante el proceso.
3. Ejecuta:

```bash
python subir_imagenes_nueva_fuente.py --fuente {fuente}
```

4. Las imágenes se segmentarán, convertirán a escala de grises y se subirán a la base de datos local con toda la información asociada.

## 🧪 Experimentos reproducibles y automatizados

El sistema incorpora una estructura modular para lanzar experimentos completos de forma automatizada. Cada experimento se define en una carpeta experiments/{nombre} que incluye:

- config.yaml: define las clases, fuente de imágenes, número de ejemplos por clase, hiperparámetros, etc.

- run_experiment.py: ejecuta todo el pipeline (preparación de datos, entrenamiento y evaluación).

- data/: CSVs con rutas a imágenes seleccionadas para train/val/test.

- models/: modelos guardados (por ejemplo, best_model.pth).

- results/: métricas y gráficos generados automáticamente.

Esto permite comparar fácilmente distintas configuraciones (por ejemplo: cambios de arquitectura, datos, preprocesamiento, etc.), sin tocar el código base.

Además, se ha separado la lógica en módulos (utils/) y scripts (scripts/) reutilizables para facilitar la escalabilidad del proyecto.

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

---

