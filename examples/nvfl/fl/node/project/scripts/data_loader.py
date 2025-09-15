import os
import numpy as np
import torch
from torch.utils.data import Dataset


class ChestXrayDataset(Dataset):
    def __init__(self, images_dir, labels_dir, transform=None):
        self.images_dir = images_dir
        self.labels_dir = labels_dir
        self.transform = transform
        self.image_ids = [
            f.split(".npy")[0] for f in os.listdir(images_dir) if f.endswith(".npy")
        ]

    def __len__(self):
        return len(self.image_ids)

    def __getitem__(self, idx):
        img_id = self.image_ids[idx]
        img = np.load(os.path.join(self.images_dir, f"{img_id}.npy"))
        label = np.load(os.path.join(self.labels_dir, f"{img_id}.npy"))

        # Convert to tensor
        img = torch.tensor(img, dtype=torch.float32).permute(2, 0, 1)  # HWC -> CHW
        label = torch.tensor(label, dtype=torch.float32)

        if self.transform:
            img = self.transform(img)

        return img, label
