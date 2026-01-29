import os
import cv2
import argparse
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

def convert_to_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

def process_image(input_path, output_path):
    image = cv2.imread(input_path)
    if image is None:
        return False
    gray = convert_to_grayscale(image)
    gray_rgb = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, gray_rgb)
    return True

def gather_image_paths(input_dir, output_dir):
    image_tasks = []
    for root, _, files in os.walk(input_dir):
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                input_path = os.path.join(root, f)
                rel_path = os.path.relpath(input_path, input_dir)
                output_path = os.path.join(output_dir, rel_path)
                image_tasks.append((input_path, output_path))
    return image_tasks

def process_folder(input_dir, output_dir, max_workers=8):
    image_tasks = gather_image_paths(input_dir, output_dir)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_image, inp, outp) for inp, outp in image_tasks]
        for _ in tqdm(as_completed(futures), total=len(futures), desc="Convirtiendo a escala de grises"):
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Conversión de imágenes a escala de grises")
    parser.add_argument("--input", required=True, help="Carpeta de entrada con imágenes")
    parser.add_argument("--output", required=True, help="Carpeta de salida para imágenes en grises")
    parser.add_argument("--workers", type=int, default=8, help="Número de hilos para procesamiento concurrente")
    args = parser.parse_args()

    process_folder(args.input, args.output, args.workers)
