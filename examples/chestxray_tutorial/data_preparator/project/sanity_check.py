import numpy as np
import os


def perform_sanity_checks(data_path, labels_path, parameters):
    labels_list = parameters["labels_list"]

    images_files = os.listdir(data_path)
    labels_files = os.listdir(labels_path)
    images_files.sort()
    labels_files.sort()

    assert all(
        [image.endswith(".npy") for image in images_files]
    ), "images should be .npy"

    assert labels_files == images_files, "labels and images should have identical names"

    labels_files = [os.path.join(labels_path, file) for file in labels_files]
    labels = np.stack([np.load(file) for file in labels_files], axis=0)

    assert labels.shape[1] == len(
        labels_list
    ), f"Labels should be one-hot encoded with {len(labels_list)} classes"

    print("Sanity checks ran successfully.")
