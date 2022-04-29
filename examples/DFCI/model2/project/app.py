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

import UNETR
from UNETR import dice_coef_multilabel, dice_coef
import monai

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
        # print("self files:", self.files)
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
            # print("len label:", label)

        if self.transform:
            sample = self.transform(sample)

        return feature, label


def unet_model(images, model_path, output):
    """
    Generates predictions for images
    
    Args:
        images: images to be predicted
        model_path: path to PyTorch model"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    test_dataset = images
    # define test loader
    test_loader = DataLoader(test_dataset, batch_size=1, shuffle=False, num_workers=0)
    print("t l:", len(test_loader))
    # load pre-trained torch model
    # net = torch.load(model_path, map_location=torch.device(device))
    net = monai.networks.nets.UNETR(
        in_channels=3,
        out_channels=2,
        img_size=(512, 512),
        feature_size=16,
        spatial_dims=2,
    )
    net.load_state_dict(torch.load(model_path, map_location=torch.device(device)))
    criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(50))
    optimizer = torch.optim.SGD(
        net.parameters(), lr=0.01, momentum=0.9, weight_decay=0.0001
    )
    # load dataset
    test_dataset = CTScanDataset(images)
    # define test_loader
    testloader = DataLoader(test_dataset, batch_size=8, shuffle=False, num_workers=0)
    # print("len testloader:", len(testloader))

    file_names = os.listdir(images)
    print(file_names)
    idx = 0
    with torch.no_grad():
        print(len(testloader))
        for data in testloader:
            images, targets = data
            images, targets = (
                images.to(device=device, dtype=torch.float),
                targets.to(device=device),
            )
            print(images)
            targets = F.one_hot(targets.long(), num_classes=2)
            targets = torch.permute(targets, (0, 3, 1, 2))
            outputs = net(images)
            print("saving:", file_names[idx])
            for row in range(len(outputs)):
                pred = outputs[row]
                torch.save(pred, os.path.join(output, file_names[idx]))
                idx = idx + 1
            # print(outputs)
            # print("save:",os.path.join(output, file_names[idx]))
            # np.save(outputs, os.path.join(output, file_names[idx]))
            # outputs_cat = F.one_hot(torch.argmax(outputs, axis=1), num_classes=2)
            # outputs_cat = torch.permute(outputs_cat, (0, 3, 1, 2))

            # torch.save(outputs_cat, os.path.join(output, file_names[idx]))
            # idx += 1


if __name__ == "__main__":
    print("App")
    parser = argparse.ArgumentParser("MedPerf DFCI Example")
    parser.add_argument(
        "--names", dest="names", type=str, help="directory containing names"
    )
    parser.add_argument(
        "--out", dest="out", type=str, help="path to store resulting predictions"
    )

    parser.add_argument(
        "--model_info",
        dest="model_info",
        type=str,
        help="directory containing model info",
    )

    # parser.add_argument('--data_p', dest="data", type=str, help="directory containing images")

    args = parser.parse_args()
    print(args.out)
    print(args.model_info)
    print(args.names)
    print("run unet model")
    unet_model(args.names, args.model_info, args.out)
    # list_vals = [loss, dice_total_avg, dice_class0_avg, dice_class1_avg]
    # loss, dice_total_avg, dice_class0_avg, dice_class1_avg = unet_model(args.names, args.model_info)
    # list_vals = [loss, dice_total_avg, dice_class0_avg, dice_class1_avg]
