import torch.nn as nn
from torchvision.models import mobilenet_v2


class SingleTaskMobileNetV2(nn.Module):
    def __init__(self, base_model, num_classes):
        super().__init__()
        self.features = base_model.features
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.dropout = nn.Dropout(0.2)
        self.classifier = nn.Linear(base_model.last_channel, num_classes)

    def forward(self, x):
        x = self.features(x)
        x = self.avgpool(x)
        x = x.view(x.size(0), -1)
        x = self.dropout(x)
        return self.classifier(x)


def build_model(config):
    """
    Crea una MobileNetV2 de clasificación simple con una sola cabeza.
    """
    fine_tune = config["fine_tune"]
    weights = config["weights"]
    classes = config.get("classes")

    if not classes:
        raise ValueError("La configuración debe incluir 'classes' para construir el modelo.")

    base_model = mobilenet_v2(weights=weights)

    if fine_tune == "none":
        for param in base_model.parameters():
            param.requires_grad = False
    elif fine_tune == "top":
        for param in base_model.features.parameters():
            param.requires_grad = False

    model = SingleTaskMobileNetV2(base_model, len(classes))
    return model


MultiTaskMobileNetV2 = SingleTaskMobileNetV2
