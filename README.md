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
├── process_imported_images.py
scripts/
├── main.py
├── test.py
├── pipeline_importar_fuente.py
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
data/importada/{nombre_fuente}/color/
```

Donde `{nombre_fuente}` identifica la fuente (por ejemplo, `agricultura_europa2025`, `proyecto_movil`, etc.).

# CAMBIAR: Deberían tener la misma estructura interna que indique las clases que PlantVillage

### 2. Procesamiento y subida automática

Una vez colocadas las imágenes, puedes ejecutar todo el pipeline con un solo comando:

```bash
python importar.py --fuente nombre_fuente
```

Este script realiza automáticamente:
- Procesamiento de las imágenes en color para generar versiones en escala de grises (`grayscale/`) y segmentadas (`segmented/`), redimensionadas y en formato JPG.
- Subida de ambas versiones a la base de datos.
- Registro de las imágenes subidas para evitar duplicados.

> También puedes ejecutar solo el procesamiento con:
>
> ```bash
> python process_imported_images.py --fuente nombre_fuente
> ```
>
> Esto es útil si quieres revisar las imágenes procesadas antes de subirlas.

---

## 🧪 Cómo añadir una nueva fuente

1. Crea una nueva carpeta dentro de `data/importada/` con el nombre de la fuente.
2. Coloca las imágenes sin procesar en `data/importada/{fuente}/color/`.
3. Ejecuta:

```bash
python importar.py --fuente {fuente}
```

4. Las imágenes se segmentarán, convertirán a escala de grises y se subirán a la base de datos local.

---

## 🔧 Requisitos

- Python 3.8+
- OpenCV (`cv2`)
- pandas, requests, tqdm

---

## 📎 Notas finales

- La segmentación implementada se inspira en el artículo original de PlantVillage, aunque no es idéntica.
- Este repositorio está diseñado para ser extensible: se puede adaptar fácilmente para nuevas fuentes, cambios en el modelo o nuevas estrategias de evaluación.
