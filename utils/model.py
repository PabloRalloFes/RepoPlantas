import torch.nn as nn
from torchvision.models import mobilenet_v2

from utils.database import get_project_config


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


class MultiTaskMobileNetV2(nn.Module):
    def __init__(self, base_model, head_sizes):
        super().__init__()
        self.features = base_model.features
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.dropout = nn.Dropout(0.2)
        self.heads = nn.ModuleList([nn.Linear(base_model.last_channel, size) for size in head_sizes])

    def forward(self, x):
        x = self.features(x)
        x = self.avgpool(x)
        x = x.view(x.size(0), -1)
        x = self.dropout(x)
        return [head(x) for head in self.heads]


def build_model(config):
    """
    Crea una MobileNetV2 de clasificación simple con una sola cabeza.
    """
    fine_tune = config["fine_tune"]
    weights = config["weights"]
    project_config = get_project_config()
    target_fields = config.get("target_fields") or project_config.get("target_fields") or [config.get("class_field", "class_label")]
    target_fields = [field for field in target_fields if field]
    target_classes = config.get("target_classes") or project_config.get("target_classes") or {}

    if not target_fields:
        raise ValueError("La configuración debe incluir al menos un campo objetivo para construir el modelo.")

    base_model = mobilenet_v2(weights=weights)

    if fine_tune == "none":
        for param in base_model.parameters():
            param.requires_grad = False
    elif fine_tune == "top":
        for param in base_model.features.parameters():
            param.requires_grad = False

    if len(target_fields) == 1:
        target_field = target_fields[0]
        classes = target_classes.get(target_field) or config.get("classes")
        if not classes:
            raise ValueError(f"No se pudieron resolver las clases para el campo objetivo '{target_field}'.")
        model = SingleTaskMobileNetV2(base_model, len(classes))
    else:
        head_sizes = []
        for field_name in target_fields:
            field_classes = target_classes.get(field_name)
            if not field_classes:
                raise ValueError(f"No se pudieron resolver las clases para el campo objetivo '{field_name}'.")
            head_sizes.append(len(field_classes))
        model = MultiTaskMobileNetV2(base_model, head_sizes)
    return model
