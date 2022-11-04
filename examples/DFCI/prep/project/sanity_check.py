import numpy as np
import glob
import os
import yaml


def check(data_path, params_file):
    params = yaml.safe_load(open(params_file, "r"))
    images_path = os.path.join(data_path, "images")
    labels_path = os.path.join(data_path, "labels")

    images = glob.iglob(os.path.join(images_path, "*"))
    for image_path in images:
        assert image_path.endswith(".npy")
        image = np.load(image_path)
        assert image.shape[:2] == (params["image_height"], params["image_width"],)
        assert len(image.shape) == 3
        number = os.path.basename(image_path).replace(".npy", "")

        label_path = os.path.join(labels_path, f"{number}.npy")
        assert os.path.exists(label_path)
        label = np.load(label_path)
        assert label.shape == image.shape, f"{label.shape} != {image.shape}"
        assert np.unique(label).tolist() == [0, 1]
