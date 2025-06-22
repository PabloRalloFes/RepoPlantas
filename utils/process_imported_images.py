import os
import cv2
import argparse
from tqdm import tqdm
from utils.convert_to_grayscale import convert_to_grayscale
from utils.segment_leaves import segment_leaf

def process_folder(source_dir, output_base):
    color_dir = os.path.join(source_dir, "color")
    gray_dir = os.path.join(source_dir, "grayscale")
    seg_dir = os.path.join(source_dir, "segmented")
    os.makedirs(gray_dir, exist_ok=True)
    os.makedirs(seg_dir, exist_ok=True)

    for filename in tqdm(os.listdir(color_dir), desc="Procesando imágenes"):
        if not filename.lower().endswith((".png", ".jpg", ".jpeg")):
            continue

        path = os.path.join(color_dir, filename)
        image = cv2.imread(path)
        if image is None:
            print(f"Error leyendo {filename}")
            continue

        # Redimensionar y convertir a JPG
        image_resized = cv2.resize(image, (256, 256))

        # Escala de grises
        gray = convert_to_grayscale(image_resized)
        gray_path = os.path.join(gray_dir, os.path.splitext(filename)[0] + ".jpg")
        cv2.imwrite(gray_path, gray, [cv2.IMWRITE_JPEG_QUALITY, 90])

        # Segmentación
        segmented = segment_leaf(image_resized)
        seg_path = os.path.join(seg_dir, os.path.splitext(filename)[0] + ".jpg")
        cv2.imwrite(seg_path, segmented, [cv2.IMWRITE_JPEG_QUALITY, 90])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Procesamiento por lotes de imágenes importadas")
    parser.add_argument("--fuente", required=True, help="Nombre de la fuente (subcarpeta dentro de data/importada)")
    args = parser.parse_args()

    base_path = os.path.join("data", "importada", args.fuente)
    process_folder(base_path, base_path)
