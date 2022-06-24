# Hello World Script
#
# This script is unrelated to the MLCube interface. It could be run
# independently without issues. It provides the actual implementation
# of the app.
import os
import csv
import argparse
import matplotlib.pyplot as plt

from PIL import Image
import numpy as np
import nibabel as nib

# !pip install -q torch_snippets pytorch_model_summary
# from torchvision import transforms
# from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset, DataLoader
import torch
import torch.nn as nn

import torch.nn.functional as F
from torchvision.models import vgg16_bn
import time
from typing import List

import metric_utils
from metric_utils import dice_coef_multilabel, dice_coef
import yaml

# Define PyTorch Dataloader
class CTScanDataset(Dataset):
    """
    KAGGLE dataset.
    Accredit to https://pytorch.org/tutorials/beginner/data_loading_tutorial.html
    """

    def __init__(self, data_dir, transform=None):
        """
        Args:
            data_dir: data folder directory
            transform (callable, optional): Optional transform to be applied
                on a sample.
        """
        self.root_dir = data_dir
        self.files = os.listdir(data_dir)
        self.transform = transform

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()

        # file_path = os.path.join(self.root_dir, self.files[idx])

        with open(os.path.join(self.root_dir, self.files[idx]), "rb") as f:
            data = np.load(f)
            feature = data[:-1, :, :].astype("float32")
            label = data[-1, :, :].astype("int8")

        if self.transform:
            sample = self.transform(sample)

        return feature, label


def unet_metrics(images_path, preds, output):
    """
    Generates predictions for images
    
    Args:
        images: images to be predicted
        model_path: path to PyTorch model"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    test_dataset = images_path
    # define test loader
    test_loader = DataLoader(test_dataset, batch_size=1, shuffle=False, num_workers=0)
    criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(50))
    # optimizer = torch.optim.SGD(net.parameters(), lr=0.01, momentum=0.9, weight_decay=0.0001)
    # load dataset
    test_dataset = CTScanDataset(images_path)
    # define test_loader
    testloader = DataLoader(test_dataset, batch_size=1, shuffle=False, num_workers=0)

    loss = 0
    dice_total_avg = 0
    dice_class0_avg = 0
    dice_class1_avg = 0

    included_extensions = [".npy"]
    file_names = [
        fn
        for fn in os.listdir(preds)
        if any(fn.endswith(ext) for ext in included_extensions)
    ]

    print("ap", file_names)
    idx = 0
    with torch.no_grad():
        for data in testloader:
            images, targets = data
            images, targets = (
                images.to(device=device, dtype=torch.float),
                targets.to(device=device),
            )
            targets = F.one_hot(targets.long(), num_classes=2)
            targets = torch.permute(targets, (0, 3, 1, 2))
            # outputs = net(images)
            labels = torch.load(os.path.join(preds, file_names[idx]))
            labels = torch.unsqueeze(labels, 0)
            print("labels", labels)
            loss += criterion(labels, targets.float()).item()

            outputs_cat = F.one_hot(torch.argmax(labels, axis=1), num_classes=2)
            outputs_cat = torch.permute(outputs_cat, (0, 3, 1, 2))

            dice_avg, dice_class = dice_coef_multilabel(
                targets, outputs_cat, numLabels=2
            )
            dice_total_avg += dice_avg.item()
            dice_class0_avg += dice_class[0].item()
            dice_class1_avg += dice_class[1].item()
            idx += 1

    dice_total_avg /= len(testloader)
    dice_class0_avg /= len(testloader)
    dice_class1_avg /= len(testloader)

    return loss, dice_total_avg, dice_class0_avg, dice_class1_avg


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--labels_csv",
        "--labels-csv",
        type=str,
        required=True,
        help="Dir containing the labels",
    )
    parser.add_argument(
        "--preds_csv",
        "--preds-csv",
        type=str,
        required=True,
        help="Dir containing the predictions",
    )
    parser.add_argument(
        "--output_file",
        "--output-file",
        type=str,
        required=True,
        help="file to store metrics results as YAML",
    )
    parser.add_argument(
        "--parameters_file",
        "--parameters-file",
        type=str,
        required=True,
        help="File containing parameters for evaluation",
    )
    args = parser.parse_args()

    loss, dice_total_avg, dice_class0_avg, dice_class1_avg = unet_metrics(
        args.labels_csv, args.preds_csv, args.output_file
    )
    list_vals = [loss, dice_total_avg, dice_class0_avg, dice_class1_avg]

    results = {}
    idx = 0
    cols = ["loss", "dice_total_avg", "dice_class0_avg", "dice_class1_avg"]
    for metric_name in cols:
        results[metric_name] = list_vals[idx]
        idx += 1

    with open(args.output_file, "w") as f:
        yaml.dump(results, f)
