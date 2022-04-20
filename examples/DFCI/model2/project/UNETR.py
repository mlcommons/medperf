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
#from torchvision.models import vgg16_bn
import time
from typing import List
import monai



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
"""    
class UNet(nn.Module):
    def __init__(self, pretrained=True, out_channels=2):
        super().__init__()

        self.encoder = vgg16_bn(pretrained=pretrained).features
        self.block1 = nn.Sequential(*self.encoder[:6])
        self.block2 = nn.Sequential(*self.encoder[6:13])
        self.block3 = nn.Sequential(*self.encoder[13:20])
        self.block4 = nn.Sequential(*self.encoder[20:27])
        self.block5 = nn.Sequential(*self.encoder[27:34])

        self.bottleneck = nn.Sequential(*self.encoder[34:])
        self.conv_bottleneck = conv(512, 1024)

        self.up_conv6 = up_conv(1024, 512)
        self.conv6 = conv(512 + 512, 512)
        self.up_conv7 = up_conv(512, 256)
        self.conv7 = conv(256 + 512, 256)
        self.up_conv8 = up_conv(256, 128)
        self.conv8 = conv(128 + 256, 128)
        self.up_conv9 = up_conv(128, 64)
        self.conv9 = conv(64 + 128, 64)
        self.up_conv10 = up_conv(64, 32)
        self.conv10 = conv(32 + 64, 32)
        self.conv11 = nn.Conv2d(32, out_channels, kernel_size=1)
    
    def forward(self, x):
        block1 = self.block1(x)
        block2 = self.block2(block1)
        block3 = self.block3(block2)
        block4 = self.block4(block3)
        block5 = self.block5(block4)

        bottleneck = self.bottleneck(block5)
        x = self.conv_bottleneck(bottleneck)

        x = self.up_conv6(x)
        x = torch.cat([x, block5], dim=1)
        x = self.conv6(x)

        x = self.up_conv7(x)
        x = torch.cat([x, block4], dim=1)
        x = self.conv7(x)

        x = self.up_conv8(x)
        x = torch.cat([x, block3], dim=1)
        x = self.conv8(x)

        x = self.up_conv9(x)
        x = torch.cat([x, block2], dim=1)
        x = self.conv9(x)

        x = self.up_conv10(x)
        x = torch.cat([x, block1], dim=1)
        x = self.conv10(x)

        x = self.conv11(x)

        return x
"""
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



def load_data(data_id):
    print('Using dataset: {0}'.format(data_id))
    if data_id == 0:
        train_path = '/mnt/disks/lits-data/dfci-ai-pilot-federatedlearn/tcia_train'
        test_path = '/mnt/disks/lits-data/dfci-ai-pilot-federatedlearn/tcia_test'
    elif data_id == 1:
        train_path = '/mnt/disks/lits-data/dfci-ai-pilot-federatedlearn/synapse_train'
        test_path = '/mnt/disks/lits-data/dfci-ai-pilot-federatedlearn/synapse_test'
    else:
        train_path = '/mnt/disks/lits-data/dfci-ai-pilot-federatedlearn/task07_train'
        test_path = '/mnt/disks/lits-data/dfci-ai-pilot-federatedlearn/task07_test'
    
    train_dataset = CTScanDataset(train_path)
    test_dataset = CTScanDataset(test_path)
    print('# train data: {0}, # test data: {1}'.format(len(train_dataset), len(test_dataset)))
    train_loader = DataLoader(train_dataset, batch_size=4, 
                              shuffle=True, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=4,
                             shuffle=False, num_workers=0)

    return train_loader, test_loader

def train(net, criterion, optimizer, trainloader, epochs, device):
    print(f"Training {epochs} epoch(s) w/ {len(trainloader)} batches each")
    
    for epoch in range(epochs):
        running_loss = 0
        
        start_time = time.time()
        
        for i, data in enumerate(trainloader):
            images, targets = data
            images, targets = images.to(device=device, dtype=torch.float), targets.to(device=device)
            #print(targets)
            targets = F.one_hot(targets.long(), num_classes=2)
            #targets = torch.permute(targets, (0, 3, 1, 2))
            targets = targets.permute((0, 3, 1, 2))
            optimizer.zero_grad()
            
            #images = np.moveaxis(images, -1, 0)
            outputs = net(images)
            loss = criterion(outputs, targets.float()) 
            
            loss.backward()
            optimizer.step()
            
            # print statistics
            running_loss += loss.item()
            if i % 200 == 199:  # print every 1000 mini-batches
                print("[%d, %5d] loss: %.7f" % (epoch + 1, i + 1, running_loss / 200))
                running_loss = 0
                
                end_time = time.time()
                print('Training time for 100 mini-batch: {0}'.format(end_time - start_time))
                start_time = time.time()

"""def test(task_args: List[str]) -> None:
    Task: train.
    Input parameters:
        --data_id

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data_id", "--data-id", type=str, default=None, help="Dataset path."
    )
    args = parser.parse_args(args=task_args)
    """

def test(net, criterion, testloader, device):
    print("evaluating model")
    loss = 0
    dice_total_avg = 0
    dice_class0_avg = 0
    dice_class1_avg = 0
    with torch.no_grad():
        for data in testloader:
            images, targets = data
            images, targets = images.to(device=device, dtype=torch.float), targets.to(device=device)
            targets = F.one_hot(targets.long(), num_classes=2)
            #targets = torch.permute(targets, (0, 3, 1, 2))
            targets = targets.permute((0, 3, 1, 2))
            #images = np.moveaxis(images, -1, 0)
            outputs = net(images)

            loss += criterion(outputs, targets.float()).item()

            outputs_cat = F.one_hot(torch.argmax(outputs, axis=1), num_classes=2)
            #outputs_cat = torch.permute(outputs_cat, (0, 3, 1, 2))
            outputs_cat = outputs_cat.permute((0, 3, 1, 2))
            dice_avg, dice_class = dice_coef_multilabel(targets, outputs_cat, numLabels=2)
            dice_total_avg += dice_avg.item()
            dice_class0_avg += dice_class[0].item()
            dice_class1_avg += dice_class[1].item()
    torch.save(net.state_dict(), f"full_model_monai.pth")
    dice_total_avg /= len(testloader)
    dice_class0_avg /= len(testloader)
    dice_class1_avg /= len(testloader)

    return loss, dice_total_avg, dice_class0_avg, dice_class1_avg

def main():
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print('Device being used: {0}'.format(device))

    print("Centralized PyTorch training")
    print("Load data")
    train_path = '../../../mnt/disks/lits-data/train'
    test_path = '../../../mnt/disks/lits-data/test'
    trainloader, testloader = load_data(train_path, test_path)

    print("Start training")
    # net = UNet().to(device)
    
    # input channel: (512, 512, 1, 3), out_channel = (512, 512, 1)
    unetr = monai.networks.nets.UNETR(in_channels=3, out_channels=2, img_size=(512, 512), feature_size=16, spatial_dims=2)
    net = unetr().to(device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(50))
    optimizer = optim.SGD(net.parameters(), lr=0.01, momentum=0.9, weight_decay=0.0001)
    num_epoch = 1
    train(net=net, criterion=criterion, optimizer=optimizer, trainloader=trainloader, epochs=num_epoch, device=device)
    
    print("Evaluate model")
    loss, dice_total_avg, dice_class0_avg, dice_class1_avg = test(net=net, criterion=criterion, testloader=testloader, device=device)
    print('Loss: {0:.4f}'.format(loss))
    print('Averaged DICE score: {0:.4f}'.format(dice_total_avg))
    print('Averaged DICE score for class 0: {0:.4f}'.format(dice_class0_avg))
    print('Averaged DICE score for class 1: {0:.4f}'.format(dice_class1_avg))



if __name__ == "__main__":
    main()