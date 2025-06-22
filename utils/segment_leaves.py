import os
import cv2
import numpy as np
import argparse
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

def refine_mask(mask):
    h, w = mask.shape
    flood_mask = np.zeros((h + 2, w + 2), np.uint8)
    cleaned = mask.copy()
    cv2.floodFill(cleaned, flood_mask, (0, 0), 0)
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return mask
    largest_contour = max(contours, key=cv2.contourArea)
    refined_mask = np.zeros_like(mask)
    cv2.drawContours(refined_mask, [largest_contour], -1, 255, thickness=cv2.FILLED)
    return refined_mask

def segment_leaf(image):
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2Lab)
    L, a, b = cv2.split(lab)
    L_eq = cv2.equalizeHist(L)
    L_blur = cv2.GaussianBlur(L_eq, (5, 5), 0)
    a_blur = cv2.GaussianBlur(a, (5, 5), 0)
    b_blur = cv2.GaussianBlur(b, (5, 5), 0)
    border = 10
    edges_a = np.concatenate([
        a_blur[:border, :].flatten(),
        a_blur[-border:, :].flatten(),
        a_blur[:, :border].flatten(),
        a_blur[:, -border:].flatten()
    ])
    edges_b = np.concatenate([
        b_blur[:border, :].flatten(),
        b_blur[-border:, :].flatten(),
        b_blur[:, :border].flatten(),
        b_blur[:, -border:].flatten()
    ])
    bg_a = np.median(edges_a)
    bg_b = np.median(edges_b)
    diff = np.sqrt((a_blur - bg_a) ** 2 + (b_blur - bg_b) ** 2)
    color_mask = (diff > 10).astype(np.uint8) * 255
    shadow_mask = ((L_blur < 100) & (diff < 15)).astype(np.uint8) * 255
    mask = cv2.bitwise_and(color_mask, cv2.bitwise_not(shadow_mask))
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = refine_mask(mask)
    result = cv2.bitwise_and(image, image, mask=mask)
    return result

def get_all_images(input_dir):
    image_files = []
    for root, _, files in os.walk(input_dir):
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                abs_path = os.path.join(root, f)
                rel_path = os.path.relpath(abs_path, input_dir)
                image_files.append((abs_path, rel_path))
    return image_files

def process_image(args):
    abs_path, rel_path, input_dir, output_dir = args
    image = cv2.imread(abs_path)
    if image is None:
        return None
    segmented = segment_leaf(image)
    out_path = os.path.join(output_dir, rel_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cv2.imwrite(out_path, segmented, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    return rel_path

def process_folder(input_dir, output_dir, max_workers=8):
    images = get_all_images(input_dir)
    tasks = [(abs_path, rel_path, input_dir, output_dir) for abs_path, rel_path in images]
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_image, t) for t in tasks]
        for _ in tqdm(as_completed(futures), total=len(futures), desc="Segmentando"):
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Segmentación mejorada estilo PlantVillage")
    parser.add_argument("--input", required=True, help="Carpeta de entrada con imágenes")
    parser.add_argument("--output", required=True, help="Carpeta de salida para imágenes segmentadas")
    parser.add_argument("--workers", type=int, default=8, help="Número de hilos para procesamiento paralelo")
    args = parser.parse_args()
    process_folder(args.input, args.output, max_workers=args.workers)
