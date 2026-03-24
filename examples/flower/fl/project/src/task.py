"""pytorchexample: A Flower / PyTorch app."""

import torch
import numpy as np
from sklearn.metrics import roc_auc_score


def train(net, trainloader, epochs, lr, device):
    """Train the model on the training set."""
    net.to(device)  # move model to GPU if available
    criterion = torch.nn.CrossEntropyLoss().to(device)
    optimizer = torch.optim.SGD(net.parameters(), lr=lr, momentum=0.9)
    net.train()
    running_loss = 0.0
    for _ in range(epochs):
        for images, labels in trainloader:
            images = images.to(device)
            labels = labels.to(device)
            optimizer.zero_grad()
            loss = criterion(net(images), labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
    avg_trainloss = running_loss / len(trainloader)
    return avg_trainloss


def test(net, testloader, device):
    """Validate the model on the test set."""
    net.to(device)
    net.eval()
    all_labels, all_probs, all_preds = [], [], []
    criterion = torch.nn.CrossEntropyLoss()
    loss = 0.0
    with torch.no_grad():
        for images, labels in testloader:
            images = images.to(device)
            labels = labels.to(device)
            outputs = net(images)

            probs = torch.sigmoid(outputs)
            preds = (probs > 0.5).int()

            all_labels.append(labels.cpu().numpy())
            all_probs.append(probs.cpu().numpy())
            all_preds.append(preds.cpu().numpy())
            loss += criterion(outputs, labels).item()

        if all_labels:
            y_true = np.vstack(all_labels)
            y_prob = np.vstack(all_probs)
            y_pred = np.vstack(all_preds)

            # Accuracy (all classes must match exactly)
            acc = (y_pred == y_true).all(axis=1).mean() * 100.0

            # AUC (macro average across classes)
            try:
                auc = roc_auc_score(y_true, y_prob, average="macro", multi_class="ovr")
            except ValueError:
                auc = float("nan")  # if only one class is present
        else:
            acc, auc = 0.0, float("nan")

    loss = loss / len(testloader)
    return loss, acc, auc
