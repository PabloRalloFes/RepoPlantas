# 🌿 Clasificación de enfermedades de plantas mediante visión por computador

Este proyecto permite construir un sistema de clasificación de imágenes de hojas de plantas con y sin enfermedades. Utiliza el dataset PlantVillage junto con imágenes reales capturadas desde una app móvil, entrenando un modelo MobileNetV2 con capacidad de generalización a condiciones reales.

---

## 📦 Estructura general

```
data/
├── PlantVillage/
├── Real/
├── Imported/

experiments/
├── exp01_nombre_experimento/
│   ├── data/
│   ├── notebooks/
│   └── models/

src/
├── campos.json
├── clases.json
├── clases_combinadas.json
├── etiquetas.json

scripts/
├── setup_bbdd.py
├── reemplazar_clases.py
├── add_class.py
├── editar_clases.py
├── upload_images.py
├── subir_imagenes_nueva_fuente.py
```

---

## ⚙️ Inicialización del sistema

### 📂 Estructura de base de datos

Ejecuta el script base:

```bash
python scripts/setup_bbdd.py
```

Esto crea las colecciones necesarias en MongoDB:
- `Docs`: almacena la información sobre cada imagen
- `Etiquetas`: contiene las etiquetas principales como formatos, fuentes, clases, etc.
- `Fuentes`: catálogos de origen de imágenes
- `Clases`: se completa con el siguiente paso

---

## 🧠 Gestión de clases

### 1. Reemplazar toda la colección de clases

Edita o completa `src/clases_combinadas.json` y luego ejecuta:

```bash
python scripts/reemplazar_clases.py
```

Esto eliminará e insertará todas las clases en MongoDB.

### 2. Añadir una nueva clase individualmente

```bash
python scripts/add_class.py Tomato___Mildiu
```

Esto añade:
- Un nuevo `_id` en `clases.json`
- Un nuevo documento en `clases_combinadas.json`
- Inserta la clase en MongoDB

Si la clase ya existe, la ignora.

### 3. Completar información adicional de clases

Ejecuta el siguiente script para editar campos vacíos (`clasificacion`, `nombre_cientifico`):

```bash
python scripts/editar_clases.py
```

Al finalizar, el script preguntará si deseas actualizar MongoDB. Si aceptas, ejecutará automáticamente `reemplazar_clases.py`.

---

## 🖼️ Subida de imágenes desde nueva fuente

### 📁 Organización esperada

Cada conjunto debe contener carpetas `color/`, `grayscale/` y `segmented/`. Si `grayscale/` o `segmented/` no existen, se generan automáticamente desde `color/`.

### 🚀 Proceso automático

Usa el script:

```bash
python scripts/subir_imagenes_nueva_fuente.py --ruta data/Imported/NuevaFuente
```

Esto hará lo siguiente:

- Recorrerá todas las imágenes
- Detectará clases nuevas (ej. `Vid___Botritis`)
- Llamará a `add_class.py` para añadirlas si no existen
- Añadirá etiquetas en MongoDB (formato, clase, fuente, etc.)
- Insertará un documento por imagen en la colección `Docs`
- Mostrará un resumen de errores o clases nuevas detectadas

---

## 🧪 Gestión de experimentos

Cada experimento se organiza en su carpeta con la siguiente estructura:

```
experiments/expXX_nombre/
├── config.yaml
├── data/
│   ├── train.csv
│   ├── val.csv
│   └── test.csv
├── results/
│   ├── history.png
│   └── metrics.json
├── models/
│   └── modelo_final.pth
```


---

## 🔧 Requisitos

- Python ≥ 3.7
- MongoDB local
- Bibliotecas: `torch`, `torchvision`, `pymongo`, `Pillow`, `scikit-learn`, `matplotlib`, `opencv-python`, etc.

---

## 📌 Notas finales

- El archivo `clases_combinadas.json` es la fuente de verdad de las clases: debe mantenerse actualizado.
- Siempre que edites manualmente las clases, recuerda ejecutar `reemplazar_clases.py`.
- Las imágenes reales subidas desde la app móvil también siguen esta estructura, y pueden integrarse en nuevos experimentos.

