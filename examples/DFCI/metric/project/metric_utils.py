# This scripts also follows standard Flower tutorial from 
# https://flower.dev/docs/example-pytorch-from-centralized-to-federated.html
# =======================================================

import os
import matplotlib.pyplot as plt
#import cv2

from PIL import Image
import numpy as np
import nibabel as nib

# !pip install -q torch_snippets pytorch_model_summary
#from torch_snippets import *
from torchvision import transforms
#from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset, DataLoader
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision.models import vgg16_bn
import time
from typing import List

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

        with open(os.path.join(self.root_dir, self.files[idx]), 'rb') as f:
            data = np.load(f)
            feature = data[:-1, :, :].astype('float32')
            label = data[-1, :, :].astype('int8')

        if self.transform:
            sample = self.transform(sample)

        return feature, label

class ComboLoss(nn.Module):
    def __init__(self, weight=None, size_average=True, alpha=0.5, ce_ratio=0.5):
        super(ComboLoss, self).__init__()
        self.alpha = alpha
        self.ce_ratio = ce_ratio
 
    def forward(self, inputs, targets, smooth=1):
        e = 0.0000001
        inputs = torch.sigmoid(inputs)
        
        #flatten label and prediction tensors
        inputs = inputs.contiguous().view(-1)
        targets = targets.contiguous().view(-1)
        
        #True Positives, False Positives & False Negatives
        intersection = (inputs * targets).sum()   
        dice = (2. * intersection + smooth) / (inputs.sum() + targets.sum() + smooth)
        inputs = torch.clamp(inputs, e, 1.0 - e)    
        out = - (self.alpha * (targets * torch.log(inputs)) + ((1 - self.alpha) * (1.0 - targets) * torch.log(1.0 - inputs)))

        weighted_ce = out.mean(-1)
        combo = (self.ce_ratio * weighted_ce) - ((1 - self.ce_ratio) * dice)
       
        return combo

def conv(in_channels, out_channels):
    return nn.Sequential(
        nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=1, padding=1),
        nn.BatchNorm2d(out_channels),
        nn.ReLU(inplace=True)
    )

def up_conv(in_channels, out_channels):
    return nn.Sequential(
        nn.ConvTranspose2d(in_channels, out_channels, kernel_size=2, stride=2),
        nn.ReLU(inplace=True)
    )

# Calculate DICE score
def dice_coef(y_true, y_pred, smooth=0.0001):
    y_true_f = y_true.flatten()
    y_pred_f = y_pred.flatten()
    # should y_pred be a label?
    intersection = torch.sum(y_true_f * y_pred_f)
    return (2. * intersection + smooth) / (torch.sum(y_true_f) + torch.sum(y_pred_f) + smooth)

 
# Calculate DICE score for multiple labels
def dice_coef_multilabel(y_true, y_pred, numLabels):
    dice=0
    dice_classes = []
    for index in range(numLabels):
        dice_class = dice_coef(y_true[:,index,:], y_pred[:,index,:])
        dice += dice_class
        dice_classes.append(dice_class)
    return dice/numLabels, dice_classes

