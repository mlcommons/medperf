import torch
from models import SimpleCNN
from tqdm import tqdm
from torch.utils.data import DataLoader
from data_loader import CustomImageDataset
from pprint import pprint


data_path = "path/to/data/folder"
weights = "path/to/weights.pt"
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
            predictions_dict[file_id] = output

pprint(predictions_dict)
