import torch.nn as nn
from torchvision.models import mobilenet_v2, MobileNet_V2_Weights


class MultiTaskMobileNetV2(nn.Module):
    def __init__(self, base_model, num_plantas, num_enfermedades):
        super().__init__()
        self.features = base_model.features
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))  # Aseguramos compatibilidad
        self.dropout = nn.Dropout(0.2)
        self.classifier_planta = nn.Linear(base_model.last_channel, num_plantas)
        self.classifier_enfermedad = nn.Linear(base_model.last_channel, num_enfermedades)

    def forward(self, x):
        x = self.features(x)
        x = self.avgpool(x)
        x = x.view(x.size(0), -1)
        x = self.dropout(x)
        out_planta = self.classifier_planta(x)
        out_enfermedad = self.classifier_enfermedad(x)
        return out_planta, out_enfermedad


def build_model(config):
    """
    Crea una MobileNetV2 multitarea con dos cabezas de clasificación.
    """
    fine_tune = config["fine_tune"]
    weights = config["weights"]
    
    base_model = mobilenet_v2(weights=weights)

    # Congelación de capas según config
    if fine_tune == "none":
        for param in base_model.parameters():
            param.requires_grad = False
    elif fine_tune == "top":
        for param in base_model.features.parameters():
            param.requires_grad = False
        for param in base_model.classifier.parameters():
            param.requires_grad = True

    num_plantas = len(config["plantas"])
    num_enfermedades = len(config["enfermedades"])

    model = MultiTaskMobileNetV2(base_model, num_plantas, num_enfermedades)
    return model
