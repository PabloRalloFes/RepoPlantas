# Importación del dataset PlantDoc en Foliarium

PlantDoc (Singh et al., 2020) contiene imágenes de hojas capturadas en condiciones de campo. Este documento describe cómo integrarlo como fuente `plantdoc` en Foliarium.

## 1. Descarga

- Repositorio: [PlantDoc-Dataset](https://github.com/pratikkayal/PlantDoc-Dataset)
- Descomprimir en una ruta local (p. ej. `~/datasets/PlantDoc/`).

## 2. Mapeo de clases

Las etiquetas de PlantDoc se normalizan a la convención PlantVillage `Planta___Enfermedad` usada en MongoDB (`Clases`):

| Carpeta PlantDoc | Clase Foliarium |
|------------------|-----------------|
| Apple Scab Leaf | `Apple___Apple_scab` |
| Apple Rust Leaf | `Apple___Cedar_apple_rust` |
| Apple Healthy Leaf | `Apple___healthy` |
| Corn Gray leaf spot | `Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot` |
| Corn leaf blight | `Corn_(maize)___Northern_Leaf_Blight` |
| Corn rust leaf | `Corn_(maize)___Common_rust` |
| Potato Early blight | `Potato___Early_blight` |
| Potato Healthy | `Potato___healthy` |
| Potato Late blight | `Potato___Late_blight` |
| Tomato Early blight | `Tomato___Early_blight` |
| Tomato Healthy | `Tomato___healthy` |
| Tomato Late blight | `Tomato___Late_blight` |
| Tomato leaf mosaic virus | `Tomato___Tomato_mosaic_virus` |
| Tomato leaf yellow virus | `Tomato___Tomato_Yellow_Leaf_Curl_Virus` |
| Tomato mold leaf | `Tomato___Leaf_Mold` |
| Tomato Septoria leaf spot | `Tomato___Septoria_leaf_spot` |

Las clases no presentes en `src/clases.json` deben añadirse con `scripts/add_class.py` antes de la subida.

## 3. Preparación en disco

```bash
python scripts/prepare_plantdoc_import.py --input /ruta/a/PlantDoc
python scripts/process_imported_images.py --fuente plantdoc
```

Estructura resultante:

```
data/plantdoc/
  color/{clase}/...
  grayscale/{clase}/...
  segmented/{clase}/...
```

## 4. Subida a MongoDB

Con la API en marcha:

```bash
python scripts/subir_imagenes_nueva_fuente.py --fuente plantdoc --validada
```

Se crea la entrada `plantdoc` en la colección `Fuente`.

## 5. Experimento de ejemplo

Crear un experimento filtrando solo PlantDoc (desde la app o con `make_experiment.py`). Ejemplo de variables en `config.yaml`:

```yaml
fuentes:
  - plantdoc
formato: Color
imagenes_por_clase: 50
plantas:
  - all
enfermedades:
  - all
solo_validadas: true
split:
  train: 0.7
  val: 0.15
  test: 0.15
```

Comparar con un experimento equivalente sobre `plantvillage` para analizar domain shift (capítulo 8 de la memoria).
