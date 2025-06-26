import torch.nn as nn
from torchvision import models

def build_model(config):
    """
    Crea un modelo MobileNetV2 para clasificación multiclase.
    Usa pesos preentrenados de ImageNet y adapta la última capa.

    Args:
        config: diccionario con al menos:
            - clases: lista de nombres de clase
            - pretrained: True/False
            - fine_tune: "all", "none", "top"

    Returns:
        modelo (nn.Module)
    """
    num_classes = len(config["clases"])
    pretrained = config["pretrained"]
    fine_tune = config["fine_tune"]  # "all", "none", "top"

    model = models.mobilenet_v2(pretrained=pretrained)

    # Congelar capas si es necesario
    if fine_tune == "none":
        for param in model.parameters():
            param.requires_grad = False
    elif fine_tune == "top":
        for param in model.features.parameters():
            param.requires_grad = False
        for param in model.classifier.parameters():
            param.requires_grad = True
    # si es "all", no tocamos nada (todo entrenable)

    # Sustituir capa final para clasificación multiclase
    model.classifier[-1] = nn.Linear(model.last_channel, num_classes)

    return model