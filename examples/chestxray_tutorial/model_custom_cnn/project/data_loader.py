import numpy as np
import torchvision.transforms as transforms
import os
from torch.utils.data import Dataset


class CustomImageDataset(Dataset):
    def __init__(self, data_path):
        self.transform = transforms.Compose(
            [transforms.ToTensor(), transforms.Normalize(mean=[0.5], std=[0.5])]
        )
        self.files = os.listdir(data_path)
        self.data_path = data_path

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx):
        img_path = os.path.join(self.data_path, self.files[idx])
        image = np.load(img_path, allow_pickle=True)
        image = self.transform(image)
        file_id = self.files[idx].strip(".npy")
        return image, file_id
