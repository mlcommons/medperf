"""Adapted from MedMnist Evaluator"""
import numpy as np
import yaml
import os
from sklearn.metrics import accuracy_score, roc_auc_score


def global_accuracy(y_true, y_score, threshold=0.5):
    y_pre = y_score > threshold
    acc = 0
    for label in range(y_true.shape[1]):
        label_acc = accuracy_score(y_true[:, label], y_pre[:, label])
        acc += label_acc
    return acc / y_true.shape[1]


def global_auc(y_true, y_score):
    auc = 0
    for i in range(y_score.shape[1]):
        try:
            label_auc = roc_auc_score(y_true[:, i], y_score[:, i])
        except ValueError:
            continue
        auc += label_auc
    return auc / (y_score.shape[1])


def calculate_metrics(labels, predictions, parameters, output_path):
    threshold = parameters["threshold"]

    predictions_file = os.path.join(predictions, "predictions.npz")

    predictions_dict = np.load(predictions_file)
    predictions = []
    labels_array = []
    for file_id in predictions_dict.files:
        predictions.append(predictions_dict[file_id])
        label_file = os.path.join(labels, f"{file_id}.npy")
        labels_array.append(np.load(label_file))

    labels = np.stack(labels_array)
    predictions = np.stack(predictions)

    metrics = {
        "Accuracy": global_accuracy(labels, predictions, threshold).tolist(),
        "AUC": global_auc(labels, predictions).tolist(),
    }

    with open(output_path, "w") as f:
        yaml.safe_dump(metrics, f)
