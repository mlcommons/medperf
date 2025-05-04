import torch
from models import SimpleCNN
from tqdm import tqdm
from torch.utils.data import DataLoader
from data_loader import CustomImageDataset
import json
import yaml
import os

data_path = "/mlcommons/volumes/data"
weights = "/mlcommons/volumes/additional_files/cnn_weights.pth"

# read parameters
parameters_file = "/mlcommons/volumes/parameters/parameters_file.yaml"
with open(parameters_file) as f:
    parameters = yaml.safe_load(f)
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
output_path = "/mlcommons/volumes/predictions"
preds_file = os.path.join(output_path, "predictions.json")
with open(preds_file, "w") as f:
    json.dump(predictions_dict, f, indent=4)
