"""Estilo visual y etiquetas legibles para gráficos de experimentos Foliarium."""
from __future__ import annotations

import re

import matplotlib.pyplot as plt

# Paleta alineada con la app (verde Foliarium + acentos)
COLORS = {
    "primary": "#2E7D32",
    "primary_light": "#66BB6A",
    "primary_dark": "#1B5E20",
    "secondary": "#388E3C",
    "accent": "#1565C0",
    "accent_light": "#42A5F5",
    "neutral": "#757575",
    "grid": "#E0E0E0",
    "text": "#212121",
}

# Barras agrupadas (accuracy / F1 / comparativas)
BAR_COLORS = ["#2E7D32", "#66BB6A", "#1B5E20", "#388E3C", "#A5D6A7"]

METRIC_LABELS = {
    "accuracy_planta": "Acc. planta",
    "accuracy_enfermedad": "Acc. enfermedad",
    "accuracy_combinada": "Acc. combinada",
    "f1_planta": "F1 planta",
    "f1_enfermedad": "F1 enfermedad",
    "precision_planta": "Prec. planta",
    "precision_enfermedad": "Prec. enfermedad",
    "recall_planta": "Recall planta",
    "recall_enfermedad": "Recall enfermedad",
}

PLANTA_LABELS = {
    "Apple": "Manzana",
    "Blueberry": "Arándano",
    "Cherry_(including_sour)": "Cereza",
    "Corn_(maize)": "Maíz",
    "Grape": "Uva",
    "Orange": "Naranja",
    "Peach": "Melocotón",
    "Pepper_bell": "Pimiento",
    "Potato": "Patata",
    "Raspberry": "Frambuesa",
    "Soybean": "Soja",
    "Squash": "Calabaza",
    "Strawberry": "Fresa",
    "Tomato": "Tomate",
    "Vid": "Vid",
}

ENFERMEDAD_LABELS = {
    "healthy": "Sana",
    "Sin_clasificar": "Sin clasificar",
    "Apple_scab": "Sarna manzana",
    "Black_rot": "Podredumbre negra",
    "Cedar_apple_rust": "Roya del cedro",
    "Cercospora_leaf_spot_Gray_leaf_spot": "Mancha gris (Cercospora)",
    "Common_rust": "Roya común",
    "Early_blight": "Tizón temprano",
    "Late_blight": "Tizón tardío",
    "Esca_(Black_Measles)": "Esca",
    "Haunglongbing_(Citrus_greening)": "Huanglongbing",
    "Leaf_blight_(Isariopsis_Leaf_Spot)": "Mancha foliar (Isariopsis)",
    "Bacterial_spot": "Mancha bacteriana",
    "Powdery_mildew": "Oídio",
    "Leaf_scorch": "Quemadura foliar",
    "Leaf_Mold": "Moho foliar",
    "Septoria_leaf_spot": "Septoria",
    "Spider_mites_Two-spotted_spider_mite": "Ácaros",
    "Target_Spot": "Mancha anular",
    "Tomato_mosaic_virus": "Virus del mosaico",
    "Tomato_Yellow_Leaf_Curl_Virus": "Virus rizado amarillo",
    "Northern_Leaf_Blight": "Tizón norteño",
    "Boro": "Carencia B",
    "Clorosis_Ferrica": "Clorosis férrica",
    "Magnesio": "Carencia Mg",
    "Potasio": "Carencia K",
    "Botritis": "Botrytis",
    "Eutipiosis": "Eutipiosis",
    "Mildiu": "Mildiu",
    "Oidio": "Oídio",
    "Podredumbre_Acida": "Podredumbre ácida",
    "Tuberculosis": "Tuberculosis",
    "Xylella": "Xylella",
    "Yesca": "Yesca",
    "Acariosis": "Acariosis",
    "Erinosis": "Erinosis",
    "Filoxera": "Filoxera",
    "Trips": "Trips",
    "Aclaramiento_de_nervios": "Aclaram. nervios",
    "Enrollamiento_Virotico": "Enroll. virosis",
    "Entrenudo_Corto": "Entrenudo corto",
    "Madera_Rizada_Madera_Acorchada": "Madera rizada",
}


def apply_plot_style():
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": COLORS["neutral"],
            "axes.labelcolor": COLORS["text"],
            "text.color": COLORS["text"],
            "xtick.color": COLORS["text"],
            "ytick.color": COLORS["text"],
            "grid.color": COLORS["grid"],
            "grid.alpha": 0.8,
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
            "axes.labelsize": 10,
            "legend.fontsize": 9,
            "figure.dpi": 100,
            "savefig.dpi": 180,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.15,
        }
    )


def save_figure(path: str):
    plt.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close()


def format_metric_label(metric_key: str) -> str:
    return METRIC_LABELS.get(metric_key, metric_key.replace("_", " ").title())


def _fallback_label(name: str, max_len: int = 22) -> str:
    text = re.sub(r"\([^)]*\)", "", str(name)).strip()
    text = text.replace("___", " · ").replace("_", " ").strip()
    text = re.sub(r"\s+", " ", text)
    if len(text) > max_len:
        text = text[: max_len - 1].rstrip() + "…"
    return text or str(name)


def format_planta_label(name: str) -> str:
    return PLANTA_LABELS.get(name, _fallback_label(name, max_len=16))


def format_enfermedad_label(name: str) -> str:
    return ENFERMEDAD_LABELS.get(name, _fallback_label(name, max_len=24))


def format_class_labels(labels, kind: str = "auto") -> list[str]:
    formatters = {
        "planta": format_planta_label,
        "enfermedad": format_enfermedad_label,
    }
    formatter = formatters.get(kind, format_enfermedad_label)

    display = [formatter(label) for label in labels]
    seen: dict[str, int] = {}
    unique: list[str] = []
    for raw, disp in zip(labels, display):
        if disp not in seen:
            seen[disp] = 1
            unique.append(disp)
        else:
            seen[disp] += 1
            short_raw = _fallback_label(raw, max_len=12)
            unique.append(f"{disp} ({short_raw})")
    return unique


def infer_label_kind(title: str) -> str:
    title_low = (title or "").lower()
    if "planta" in title_low:
        return "planta"
    if "enfermedad" in title_low:
        return "enfermedad"
    return "enfermedad"
