"""Corrige imagenes_por_clase: 0 -> all en config.yaml de experimentos existentes."""

import os
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.data import is_unlimited_imagenes_por_clase, normalize_imagenes_por_clase_for_storage


def main():
    base = ROOT / "experiments"
    if not base.is_dir():
        print(f"No existe {base}")
        return

    for name in sorted(os.listdir(base)):
        exp_dir = base / name
        if not exp_dir.is_dir() or name == "comparison":
            continue
        config_path = exp_dir / "config.yaml"
        if not config_path.is_file():
            continue

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

        old = config.get("imagenes_por_clase")
        if not is_unlimited_imagenes_por_clase(old):
            continue

        config["imagenes_por_clase"] = normalize_imagenes_por_clase_for_storage(old)
        if "plantas" in config or "enfermedades" in config:
            config.pop("classes", None)

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)

        print(f"{name}: {old!r} -> {config['imagenes_por_clase']!r}")


if __name__ == "__main__":
    main()
