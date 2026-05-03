# 👨‍💻 Guía para Desarrolladores

**Para técnicos que quieren entender, modificar o extender el proyecto.**

---

## 🔧 Instalación del Entorno de Desarrollo

### Requisitos Previos
- Python 3.11+
- Git
- Conda (recomendado) o venv

### Paso 1: Clonar el Repositorio
```bash
git clone https://github.com/PabloRalloFes/RepoPlantas.git
cd RepoPlantas
```

### Paso 2: Crear Entorno Virtual
```bash
# Con Conda (recomendado)
conda create -n {entorno} python=3.11
conda activate {entorno}

# O con venv
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### Paso 3: Instalar Dependencias
```bash
pip install -r requirements.txt
```

---

## 🏗️ Arquitectura del Proyecto

```
data/
├── PlantVillage/
│   ├── color/
│   ├── grayscale/
│   └── segmented/
├── {fuente_x}/
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
Dockerfile
docker-compose.yml
.env.docker.example
.dockerignore
```

---

## 🚀 Ejecutar en Desarrollo

### Opción 1: Servidor + App en Ventanas Diferentes

**Terminal 1 - Servidor (API Backend)**
```bash
conda activate {entorno}
python run_server.py --https --dev
```
La API estará en `https://localhost:5001`

**Terminal 2 - Aplicación de Escritorio**
```bash
conda activate {entorno}
python main_app.py
```

### Opción 2: Solo Servidor
```bash
python run_server.py --https
```

### Opción 3: Generar la app de Windows

Si quieres crear un ejecutable para usuarios finales, usa el empaquetado de Flet sobre la interfaz principal:

```bash
flet build windows
```

El resultado se genera en `build/windows/` y se distribuye como app de escritorio. Esa app es un cliente que se conecta al backend remoto configurado desde la propia interfaz o mediante variables de entorno.

---

## 🪟 Crear una app de Windows

El proyecto ya tiene un launcher de escritorio en `windows_launcher.py` que arranca la API local y luego abre la interfaz Flet. Para generar el ejecutable de Windows usa:

```bash
flet build windows
```

El resultado se genera dentro de `build/windows/` y puede distribuirse como carpeta portable o instalarse con el empaquetado que genere Flet.

Si al compilar aparece un error de CMake o del generador de Visual Studio, borra `build/flutter/build/windows/x64` o `build/flutter/build/windows` y vuelve a lanzar el build.

---


## Tipos de conexión

El sistema permite trabajar con una base de datos propia en local o conectarse al servidor y trabajar con la base de datos y la API centralizadas. A continuación se detalla cómo inicializar y utilizar el entorno local:

### 🚀 Ejecución en entorno local
Si deseas trabajar con tu propia base de datos MongoDB local, sigue estos pasos adicionales:

1. **Clonar el repositorio:**
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd <CARPETA_DEL_REPOSITORIO>
   ```

2. **Configurar la base de datos local:**
  - Asegúrate de tener MongoDB instalado y corriendo en tu máquina.
  - Ejecuta el script setup_bbdd.py para inicializar la base de datos:
  ```bash
  python scripts/setup_bbdd.py
  ```

3. **Ejecuta el servidor**
```bash
python run_server.py --https
```

4. **Cambiar la URL de la API y la base de datos:**
  - Desde la app, cambia la URL de la API para que apunte a tu máquina local (por ejemplo, http://127.0.0.1:5001).

5. **Subir imágenes y trabajar con tu base de datos:**
  - Usa la funcionalidad de subida masiva o individual desde la app.
  - Realiza validaciones, ediciones y experimentos con tu base de datos local.


---

## Preparación manual de imágenes externas

Si quieres añadir un congunto grande de imágenes reales (por ejemplo, tomadas con una app móvil o recopiladas manualmente), debes colocarlas manualmente en la siguiente ruta:

```
data/{nombre_fuente}/color/
```

Donde `{nombre_fuente}` identifica la fuente (por ejemplo, `proyecto_movil`, `agricultura_europa2025`, etc.).

Dentro de esta carpeta, las imágenes deben estar organizadas por subcarpetas con el nombre exacto de cada clase (enfermedad): {planta}___{nombre_comun}. Ejemplo:

```
data/mi_fuente/color/Tomato___Early_blight/
├── img1.jpg
├── img2.jpg
```

Esto permite que el sistema asocie automáticamente cada imagen con su clase correspondiente durante la subida.

---

## Procesamiento y subida automática de nuevas fuentes

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

> También puedes ejecutar solo el procesamiento (sin subir las imágenes a la base de datos) con:
>
> ```
> python scripts/process_imported_images.py --fuente nombre_fuente
> ```
>
> Esto es útil si quieres revisar las imágenes procesadas antes de subirlas.

También puedes hacer todo esto usando la funcionalidad de subida masiva de la app.


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

---

## ✅ Guía de comprobación manual

Esta lista es la mejor forma de validar que el refactor a clasificación simple sigue funcionando de punta a punta.

### 1. Preparar la demo mínima

- Ejecuta `python scripts/setup_demo_minimal.py --experiment-name DemoMinimal --db-name Demo_Grietas --class-names Inofensiva Neutra Peligrosa --images-per-class 1 --overwrite`.
- Comprueba que se crea `experiments/DemoMinimal/` con `config.yaml`, `run_experiment.py`, `data/`, `models/` y `results/`.
- Verifica que la base de datos demo se llama `Demo_Grietas` y contiene varias clases con `nombre` y `clase` iguales a `Inofensiva`, `Neutra` y `Peligrosa`.

### 2. Arrancar backend y app

- Inicia la API con `python run_server.py --https --dev`.
- Abre la app con `python main_app.py`.
- Comprueba que la pantalla inicial carga sin errores de conexión.

### 3. Probar predicción de una sola clase

- Sube una imagen manualmente desde la app.
- Lanza una predicción con un modelo disponible.
- Verifica que el resultado muestra solo `Clase` y `Confianza`, no dos salidas separadas.
- Comprueba que el valor de confianza tiene sentido y que la clase devuelta coincide con una etiqueta conocida o plausible.

### 4. Probar filtros de imágenes

- Abre la vista de etiquetado o filtrado de imágenes.
- Selecciona una clase, un formato y una fuente.
- Verifica que el listado cambia y que la API devuelve imágenes coherentes con el filtro.
- Cambia el filtro a `Cualquiera` y comprueba que vuelve a mostrar resultados amplios.

### 5. Probar experimentos

- Abre la pantalla de experimentos.
- Comprueba que se ve `classes` en la configuración del experimento y que no aparecen dependencias visuales de `plantas/enfermedades` en los experimentos nuevos.
- Abre el detalle de un experimento y revisa que las métricas mostradas sean `accuracy`, `precision`, `recall` y `f1`.
- Si el experimento es el demo, verifica que la ruta y los resultados se leen correctamente desde `experiments/DemoMinimal/`.

### 6. Probar scripts auxiliares

- Ejecuta `python scripts/predict_image.py <ruta_imagen> --experiment experiments/DemoMinimal` y comprueba que imprime una sola clase y una confianza.
- Ejecuta `python scripts/compare_experiments.py <exp1> <exp2>` con dos experimentos que tengan métricas y verifica que genera el gráfico comparativo.

### 7. Comprobación rápida de salud general

- Repite un ciclo corto completo: login, subida de imagen, predicción, filtrado y apertura de experimento.
- Si alguno falla, revisa primero que la URL de la API, Mongo y el modelo seleccionado sean los correctos.

### Resultado esperado

- La app arranca.
- La demo mínima se crea.
- La predicción devuelve una sola clase.
- Los filtros funcionan con `class_label`.
- Los experimentos y scripts ya no dependen del flujo antiguo de dos salidas.

A través de la app se puede ejecutar todo este proceso de manera sencilla, además de visualizar los resultados y comparar experimentos de forma preliminar.

---

## 📦 Dependencias Principales

| Librería | Uso |
|----------|-----|
| Flask | Backend REST API |
| PyMongo | Conexión a MongoDB |
| PyTorch | Modelos de visión |
| Flet | GUI de escritorio |
| JWT | Autenticación |
| Requests | HTTP client |

---

## 🐛 Debugging

### Ver logs del servidor
```bash
python run_server.py --https --dev
# Los logs aparecerán en la terminal
```

---

## 🔗 Enlaces Útiles

- [MongoDB Intro](https://docs.mongodb.com/)
- [Flask Official Docs](https://flask.palletsprojects.com/)
- [Flet Docs](https://flet.dev/)
- [PyTorch Docs](https://pytorch.org/docs/)

---


