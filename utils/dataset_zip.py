"""Normalización de ZIPs de datasets importados a data/<fuente>/color/<clase>/..."""

import os
import shutil

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")
SKIP_DIR_NAMES = {"__MACOSX"}


def _list_immediate_subdirs(path):
    if not os.path.isdir(path):
        return []
    return [
        name
        for name in os.listdir(path)
        if name not in SKIP_DIR_NAMES and os.path.isdir(os.path.join(path, name))
    ]


def _contains_images(directory):
    for _, _, files in os.walk(directory):
        if any(f.lower().endswith(IMAGE_EXTENSIONS) for f in files):
            return True
    return False


def class_dirs_with_images(base_dir):
    """Devuelve nombres de carpetas Planta___Enfermedad con imágenes bajo base_dir."""
    if not os.path.isdir(base_dir):
        return []

    found = []
    for name in _list_immediate_subdirs(base_dir):
        if "___" not in name:
            continue
        class_path = os.path.join(base_dir, name)
        if _contains_images(class_path):
            found.append(name)
    return found


def find_class_source_root(extracted_dir):
    """Localiza el directorio que contiene las carpetas de clase.

    Soporta:
      - color/<Planta___Enfermedad>/...
      - <Planta___Enfermedad>/... en la raíz del ZIP
      - <contenedor>/color/<Planta___Enfermedad>/...
      - <contenedor>/<Planta___Enfermedad>/...
    """
    color_at_root = os.path.join(extracted_dir, "color")
    classes = class_dirs_with_images(color_at_root)
    if classes:
        return color_at_root, classes

    classes = class_dirs_with_images(extracted_dir)
    if classes:
        return extracted_dir, classes

    for wrapper_name in _list_immediate_subdirs(extracted_dir):
        if wrapper_name == "color":
            continue
        wrapper_path = os.path.join(extracted_dir, wrapper_name)

        wrapper_color = os.path.join(wrapper_path, "color")
        classes = class_dirs_with_images(wrapper_color)
        if classes:
            return wrapper_color, classes

        classes = class_dirs_with_images(wrapper_path)
        if classes:
            return wrapper_path, classes

    return None, []


def normalize_extracted_dataset(dest_dir):
    """Normaliza a dest_dir/color/<Planta___Enfermedad>/ y elimina el resto.

    Returns:
        (True, class_count) si OK
        (False, error_message) si falla
    """
    source_root, class_dirs = find_class_source_root(dest_dir)
    if not source_root or not class_dirs:
        return False, (
            "Estructura inválida. El ZIP debe contener carpetas 'Planta___Enfermedad' "
            "directamente, dentro de 'color/', o dentro de una carpeta contenedora."
        )

    final_color = os.path.join(dest_dir, "color")
    os.makedirs(final_color, exist_ok=True)

    for class_dir in class_dirs:
        src = os.path.join(source_root, class_dir)
        dst = os.path.join(final_color, class_dir)
        if os.path.normpath(src) == os.path.normpath(dst):
            continue
        if os.path.exists(dst):
            return False, (
                f"Conflicto al normalizar estructura: la carpeta '{class_dir}' "
                "ya existe en color/."
            )
        shutil.move(src, dst)

    for item in os.listdir(dest_dir):
        if item == "color":
            continue
        path = os.path.join(dest_dir, item)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

    return True, len(class_dirs)
