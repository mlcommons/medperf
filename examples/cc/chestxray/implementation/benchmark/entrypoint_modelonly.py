import torch
from models import SimpleCNN
from tqdm import tqdm
from torch.utils.data import DataLoader
from data_loader import CustomImageDataset
import os
import json


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

# save

output_path = os.getenv("OUTPUT_RESULTS")
os.makedirs(output_path, exist_ok=True)

preds_file = os.path.join(output_path, "predictions.json")
with open(preds_file, "w") as f:
    json.dump(predictions_dict, f, indent=4)
