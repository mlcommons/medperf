"""Adapted from MedMnist Evaluator"""

import numpy as np
import yaml
import os
from sklearn.metrics import accuracy_score, roc_auc_score
import json


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

    predictions_file = os.path.join(predictions, "predictions.json")

    with open(predictions_file) as f:
        predictions_dict = json.load(f)
    predictions = []
    labels_array = []
    for file_id in predictions_dict:
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


if __name__ == "__main__":
    parameters_file = "/mlcommons/volumes/parameters/parameters_file.yaml"
    predictions = "/mlcommons/volumes/predictions"
    labels = "/mlcommons/volumes/labels"
    output_path = "/mlcommons/volumes/results/results.yaml"

    with open(parameters_file) as f:
        parameters = yaml.safe_load(f)

    calculate_metrics(labels, predictions, parameters, output_path)
