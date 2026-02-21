import torch
from models import SimpleCNN
from tqdm import tqdm
from torch.utils.data import DataLoader
from data_loader import CustomImageDataset
import os
import numpy as np
import yaml
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


def calculate_metrics(labels, predictions_dict, parameters, output_path):
    threshold = parameters["threshold"]
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


data_path = os.getenv("INPUT_DATA")
weights = os.path.join(os.getenv("MODEL_FILES"), "cnn_weights.pth")

in_channels = 1
num_classes = 14
batch_size = 5

# load model
model = SimpleCNN(in_channels=in_channels, num_classes=num_classes)
model.load_state_dict(torch.load(weights))
model.eval()

# load prepared data
dataset = CustomImageDataset(data_path)
dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

# inference
predictions_dict = {}
with torch.no_grad():
    for images, files_ids in tqdm(dataloader):
        outputs = model(images)
        outputs = torch.nn.Sigmoid()(outputs)
        outputs = outputs.detach().numpy()

        for file_id, output in zip(files_ids, outputs):
            predictions_dict[file_id] = output.tolist()


labels = os.getenv("INPUT_LABELS")
output_dir = os.getenv("OUTPUT_RESULTS")
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "results.yaml")

calculate_metrics(labels, predictions_dict, {"threshold": 0.5}, output_path)
