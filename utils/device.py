import os

def get_device():
    """Devuelve el dispositivo a usar para PyTorch.

    Comportamiento:
    - Si la variable de entorno `FORCE_CPU` está a true (1/true/yes), devuelve 'cpu'.
    - Si la variable de entorno `USE_CUDA` está a true (1/true/yes), intenta usar 'cuda' si está disponible, si no 'cpu'.
    - Por defecto devuelve 'cpu' para evitar que entornos sin GPU intenten usar CUDA.
    """
    force_cpu = os.getenv("FORCE_CPU", "").lower() in ("1", "true", "yes")
    use_cuda_env = os.getenv("USE_CUDA", "").lower()

    if force_cpu:
        return "cpu"

    if use_cuda_env in ("1", "true", "yes"):
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            return "cpu"

    if use_cuda_env in ("0", "false", "no"):
        return "cpu"

    # Default: cpu
    return "cpu"
