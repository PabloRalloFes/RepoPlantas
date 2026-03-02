# Plant Disease Classification via Computer Vision / Plant Leaf Image Collection and Labeling System

This repository is part of the Bachelor's Thesis in Data Science at the Universitat Politècnica de València.
The project develops a complete application to collect, store, and label images of healthy and diseased plant leaves, combining the PlantVillage dataset with real images taken using a custom app. It also aims to approach a combined predictive analysis using images from three sources: PlantVillage, the app and a small set provided by the agronomy faculty.

The system integrates a Flask API for image and user management, and a desktop application developed with Flet (Python) that allows intuitive interaction with the database.

---

## � Documentation Structure

This is the **main document** that explains the complete project architecture. Depending on what you need, consult:

| Document | Content |
|----------|----------|
| **README.md / README_ES.md** | 📍 You are here - General overview and project architecture |
| **[README_APP.md](README_APP.md)** | Guide for the **desktop application** (main_app.py) |
| **[README_APP_EN.md](README_APP_EN.md)** | English guide for the **desktop application** |
| **[server/README.md](server/README.md)** | Guide for the **backend server** (main.py) |
| **[server/README_ES.md](server/README_ES.md)** | Spanish guide for the **backend server** |

👉 **Start here if it's your first time** with a section depending on what you want to do:
- **User**: Go to [README_APP.md](README_APP.md)
- **Local Developer**: Go to [server/README.md](server/README.md)
- **System Architect**: Continue in this document

---

## �📦 General Structure

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
### trained models
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

## 🧩 General System Architecture

The project is organized into two main components that work complementarily:

### 1. 🌿 Application and Flask API (data collection and management)
This part of the system allows collecting and managing images of plant leaves, as well as users and roles that interact with the database. It also provides an app to experiment and explore the project's possibilities.
It consists of three main modules:

- **`main.py`** → Unified Flask API that manages the MongoDB database.
  - Endpoints to upload images, retrieve labels, classify leaves, and manage users.
  - Works as a backend server and connection point with the Flet application.

- **`main_app.py`** → Graphical application developed with [Flet](https://flet.dev/).
  - Allows user registration and login.
  - Offers separate interfaces for the three main roles:
    - *User:* upload images and assign labels.
    - *Labeler:* validate pending images.
    - *Administrator:* manage users and roles.

- **`logicav3.py`** → Connection module between the app and the API.
  - Sends HTTP requests (`httpx`) to the API.
  - Encodes images to base64 before uploading.
  - Manages authentication, user searches, and in-memory data flow.

The workflow is as follows:
The workflow is as follows:
1. **User / Labeler / Administrator** interacts with the system.
2. They use the **Flet Application** (`main_app.py`).
3. The app communicates via JSON/HTTP (`httpx`) with the **Flask API** (`main.py`).
4. The **Flask API** manages the **MongoDB Database**:
  - `appPlantas` (users)
  - `Repositorio_Plantas` (images)
5. The experimental module (CNN) uses the data for:
  - MobileNetV2 training
  - PlantVillage dataset usage

---

### 2. 🤖 Model and Experimentation Module (training and evaluation)
This part contains scripts and notebooks to train and evaluate classification models, based on **CNN** architectures (mainly MobileNetV2).
It uses both the **PlantVillage** dataset and images collected via the app and provided by the agronomy faculty.

Experiments are organized by folders inside `experiments/` and can be configured via `config.yaml` files.
This structure allows reproducing different training scenarios or comparing data and model configurations.

---

Both parts of the project are connected by their common purpose:
👉 **to generate a robust plant disease classification system adapted to real-world conditions.**

## 🧩 Part A — Application and Flask API

This part of the project implements the system for **collecting, storing, and labeling images**, along with **user and role management**.
It allows registering new users, uploading images from the app, validating labels, and managing the database visually.

---

### ⚙️ Main Components

| File            | Description |
|-----------------|-------------|
| **`main.py`**   | Contains the **unified Flask API**, which manages communication with the MongoDB database. Includes endpoints for user registration and login, image upload and query, label validation, and role administration. |
| **`main_app.py`** | Implements the **graphical interface** using the [Flet](https://flet.dev/) framework. Offers different views depending on the user's role (*user*, *labeler*, or *administrator*). Allows direct interaction with the API without manual scripts. |
| **`logicav3.py`** | Defines the `LogicaApp` class, which acts as a **bridge between the app and the Flask API**. Manages URL creation, sending HTTP requests, handling responses, and converting images to base64 before sending. |

---

### 🧠 User Roles

| Role            | Main Functionality |
|-----------------|-------------------|
| 🧑‍🌾 **User**         | Upload images and assign labels. |
| 🧩 **Labeler**        | Validate and correct pending images. |
| ⚙️ **Administrator**  | Manage users, roles, and passwords. |

---

### Connection Types

The system allows working with a local database or connecting to the server and working with the centralized database and API. Below is how to initialize and use the local environment:

### 🚀 Running Locally

> **📌 For detailed instructions on how to run the server and app, see:**
> - **[server/README.md](server/README.md)** - Complete backend server guide
> - **[README_APP_EN.md](README_APP_EN.md)** - Desktop application guide

**Quick summary:**

1. Install MongoDB locally (or use a remote one)
2. Start the server: `python main.py` (or use `python server/run_server.py --dev --https`)
3. In another terminal, start the app: `python main_app.py`

For more details and troubleshooting, see the documentation linked above.

## 🤖 Part B: Predictive Model and Experimentation

The project includes a complete pipeline to create and manage the image database using python scripts. The app also includes a preliminary environment for exploration and experimentation.

💡 Note: make sure to adjust the IP (in logicav3.py or in the app configuration) to the environment where the Flask API is running.

### 1. Database Initialization

Before working with the images, you need to create the basic structure of collections and labels in MongoDB.

You can easily do this by running the following script:

```
python scripts/setup_bbdd.py
```

This will automatically create:

- The necessary collections (`Clases`, `Docs`, `Formato`, `Fuente`, etc.).
- The basic labels such as `Color`, `Grayscale`, and `Segmented`.
- The registration of all available classes in PlantVillage from `clases.json`.

⚠️ Make sure the MongoDB server (`main.py`) is running before launching this step.

---

### 2. Uploading PlantVillage Images

Once the database is created, you can upload all PlantVillage dataset images in the three available formats by running:

```
python scripts/upload_images.py Color
python scripts/upload_images.py Grayscale
python scripts/upload_images.py Segmented
```

This script:
- Processes images if they are not generated (grayscale and segmented).
- Uploads images to the local database.
- Logs already uploaded images to avoid duplicates in future runs.

---

### 3. Manual Preparation of External Images

If you want to add a large set of real images (e.g., taken with a mobile app or collected manually), you must manually place them in the following path:

```
data/Imported/{source}/color/
```

Where `{source}` identifies the source (e.g., `mobile_project`, `agriculture_europe2025`, etc.).

💡 Note: if you want to implement this set of images in the centralized database, contact the developer.

These images must be organized in folders with the exact name of each class (disease), just like in PlantVillage: {plant}___{common_name}. Example:

```
data/Imported/my_source/color/Tomato___Early_blight/
├── img1.jpg
├── img2.jpg
```

This allows the system to automatically associate each image with its corresponding class during upload.

---

### 4. Automatic Processing and Upload of New Sources

Once the images are placed, you can run the entire processing and upload pipeline with a single command:

```
python scripts/subir_imagenes_nueva_fuente.py --fuente source_name
```

This script automatically:
- Registers the source in the database (if it does not already exist).
- Processes color images to generate `grayscale/` and `segmented/` versions.
- Resizes and converts to JPG.
- Uploads all three formats (`color`, `grayscale`, `segmented`) with the corresponding metadata (`source`, `format`).
- Controls duplicates using logs by format.

> You can also run only the processing (without uploading the images to the database) with:
>
> ```
> python scripts/process_imported_images.py --fuente source_name
> ```
>
> This is useful if you want to review the processed images before uploading them.


## 🧪 Reproducible and Automated Experiments

The project allows launching complete experiments in a modular and automated way. Each experiment is defined within a folder:

```
experiments/{experiment_name}/
```

This folder must contain:

- `config.yaml`: experiment configuration, including selected classes, data sources, format, number of images per class, model hyperparameters, etc.
- `run_experiment.py`: script that runs the entire pipeline (data preparation, training, and evaluation).

With these 2 files, you can run an experiment, which will generate the following:

- `data/`: CSVs automatically generated with image paths for training, validation, and test.
- `models/`: folder where the trained model is saved (`best_model.pth`).
- `results/`: metrics, graphs, confusion matrices, and evaluation logs.

This makes it easy to compare different configurations (e.g., changes in data, preprocessing, architecture, training...) without modifying the project's base code. In the experiments/BASE folder, you can find templates for the only 2 required files.

All pipeline logic is divided into reusable modules within `utils/` and `scripts/`, making it easy to maintain and scale.

Through the app, you can view results and compare experiments preliminarily.


## 📓 Auxiliary Scripts/Notebooks
- **EDA.ipynb**: Initial exploratory analysis.
- **misclassified_and_topk.ipynb**: Tool to visually analyze model errors and consult the top-k predictions for a specific image. Useful for debugging and qualitative analysis of results.

These resources are found in the `scripts/` or `notebooks/` folders and support the analysis and interpretation of the experiments performed.

---

### ⚠️ Considerations for Class Selection

In some crops from the PlantVillage dataset (`Blueberry`, `Orange`, `Raspberry`, `Soybean`, and `Squash`) there is only one available class (e.g., only healthy leaves). For this reason, it is recommended to exclude these crops from experiments, as they do not allow learning to distinguish between classes.

This criterion may change if real images are incorporated in the future that increase the number of possible classes for these crops.

---

## 🔧 Requirements

- Python ≥ 3.10
- MongoDB ≥ 6.0 (local or remote server)
- Libraries in requirements.txt

---

> 📌 Note on terminology:
> - A **field** is an attribute such as `source`, `format`, or `class`.
> - A **label** is an allowed value within a field, defined with structure and type.
> - A **class** is the main category of an image: combination of crop and disease. It is stored in the `Clases` collection.

## 📌 Final Notes

- The implemented segmentation is inspired by the original PlantVillage article (Mohanty et al. 2016), although it is not identical.
- This repository is designed to be extensible: it can be easily adapted for new sources, model changes, or new evaluation strategies.
- The `upload_images.py` script handles the creation of `grayscale` and `segmented` versions by itself if they do not exist, calling `process_imported_images.py` automatically.
- The scripts in scripts/legacy have been used as auxiliary tools and the end user will most likely not need to use them. For example, dividir_clases.py is only necessary if old classes were inserted without the crop and disease fields, and eliminar_nombre.py if you want to remove a variable from the Clases collection (in this case, name).
- If you have a compatible GPU, it is recommended to install PyTorch with CUDA support from https://pytorch.org/get-started/locally to speed up training.
- Images are physically stored in a local project folder (`data/`, `imagenes/`, etc.), while only the associated fields and relative paths to the images are saved in the database. This optimizes storage and facilitates the management of large volumes of data.
- Security and authentication are currently implemented in a basic way (custom hash). It is recommended to migrate to bcrypt and add session or JWT control before public deployment.
- BE CAREFUL WITH LOGS WHEN REPEATING MASS UPLOADS. The logs store the original paths of images that have already been uploaded in bulk. If you want to re-upload one or more images that have already been uploaded in bulk, you must delete them from the database and delete the logs.
- If you have uploaded in bulk without processing and then want to upload the processed images as well, simply use the bulk upload function for that source again but this time activating the switch.
---
