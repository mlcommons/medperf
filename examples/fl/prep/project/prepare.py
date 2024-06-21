import os
import numpy as np
import pandas as pd
import shutil
from tqdm import tqdm
from PIL import Image


def prepare_split(split, arrays, output_path, output_labels_path):
    subfolder = os.path.join(output_path, "pathmnist")
    os.makedirs(subfolder, exist_ok=True)

    arrs = arrays[f"{split}_images"]
    labels = arrays[f"{split}_labels"]
    csv_data = []
    for i in tqdm(range(arrs.shape[0])):
        name = f"{split}_{i}.png"
        out_path = os.path.join(subfolder, name)
        Image.fromarray(arrs[i]).save(out_path)
        record = {
            "SubjectID": str(i),
            "Channel_0": os.path.join("pathmnist", name),
            "valuetopredict": labels[i][0],
        }
        csv_data.append(record)

    if split == "train":
        csv_file = os.path.join(output_path, "train.csv")
    if split == "val":
        csv_file = os.path.join(output_path, "valid.csv")
    if split == "test":
        csv_file = os.path.join(output_path, "data.csv")

    pd.DataFrame(csv_data).to_csv(csv_file, index=False)

    if split == "test":
        csv_file_in_labels = os.path.join(output_labels_path, "data.csv")
        shutil.copyfile(csv_file, csv_file_in_labels)


def prepare_dataset(data_path, labels_path, output_path, output_labels_path):
    os.makedirs(output_path, exist_ok=True)
    os.makedirs(output_labels_path, exist_ok=True)

    file_path = os.path.join(data_path, "pathmnist.npz")
    arrays = np.load(file_path)
    for key in arrays.keys():
        if key.endswith("images"):
            split = key.split("_")[0]
            prepare_split(split, arrays, output_path, output_labels_path)
