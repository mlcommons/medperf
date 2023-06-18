import os
from PIL import Image
import numpy as np
import csv
from tqdm import tqdm


def prepare_dataset(
    data_path, labels_path, parameters, output_path, output_labels_path
):
    labels_list = parameters["labels_list"]
    image_column_id = parameters["image_column_id"]
    label_column_id = parameters["label_column_id"]
    image_output_size = parameters["image_output_size"]

    labels_file = os.path.join(labels_path, "labels.csv")
    labels_file_stream = open(labels_file)
    labels = csv.DictReader(labels_file_stream)

    for row in tqdm(labels):
        image_id = row[image_column_id]
        img_path = os.path.join(data_path, f"{image_id}.png")
        img = Image.open(img_path)
        resized_img = img.resize(image_output_size[:-1])
        img_array = np.asarray(resized_img)
        img_array = np.expand_dims(img_array, -1)

        label = labels_list.index(row[label_column_id])
        # one-hot encoding
        encoded_label = np.eye(len(labels_list), dtype=int)[label, :]
        np.save(os.path.join(output_path, f"{image_id}.npy"), img_array)
        np.save(os.path.join(output_labels_path, f"{image_id}.npy"), encoded_label)

    labels_file_stream.close()
