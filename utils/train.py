import torch
import torch.nn as nn
import torch.optim as optim
import os
from tqdm import tqdm
import numpy as np

def train_model(model, train_loader, val_loader, config):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)

    epochs = config["epochs"]
    lr = config["lr"]
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)

    history = {"train_loss": [], "val_loss": []}

    for epoch in range(epochs):
        # Entrenamiento
        model.train()
        running_loss = 0.0
        #print(train_loader)
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            #print(f"Images shape: {images.shape}, Labels shape: {labels.shape}")
            optimizer.zero_grad()
            outputs = model(images)
            #print(f"Output shape: {outputs.shape}, Labels shape: {labels.shape}")
            #print(f"Output: {outputs}, Labels: {labels}")
            #break
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
        avg_train_loss = running_loss / len(train_loader)
        history["train_loss"].append(avg_train_loss)
        #break
        # Validación (solo pérdida)
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                val_loss += loss.item()
        avg_val_loss = val_loss / len(val_loader)
        history["val_loss"].append(avg_val_loss)

        print(f"Epoch {epoch+1}/{epochs} - Train Loss: {avg_train_loss:.4f} - Val Loss: {avg_val_loss:.4f}")

    return model, history

def evaluate(model, dataloader, device="cuda"):
    criterion = nn.CrossEntropyLoss()
    
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in dataloader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            total_loss += loss.item() * images.size(0)
            preds = outputs.argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)

    avg_loss = total_loss / total
    accuracy = correct / total
    return avg_loss, accuracy
