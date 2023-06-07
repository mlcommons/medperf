import numpy as np
import torch
import torchvision.transforms as transforms
import os
from models import SimpleCNN
from tqdm import tqdm
from torch.utils.data import Dataset, DataLoader


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
        image = np.load(img_path)
        image = self.transform(image)
        file_id = self.files[idx].strip(".npy")
        return image, file_id


def run_inference(data_path, parameters, output_path, weights):
    in_channels = parameters["in_channels"]
    num_classes = parameters["num_classes"]
    batch_size = parameters["batch_size"]

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
                predictions_dict[file_id] = output

    # save
    preds_file = os.path.join(output_path, "predictions.npz")
    np.savez(preds_file, **predictions_dict)
