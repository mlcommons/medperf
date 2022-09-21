import numpy as np
import glob
import os
import yaml


def get_stats(data_path, params_file, output_path):

    stats = {}
    images_path = os.path.join(data_path, "images")
    labels_path = os.path.join(data_path, "labels")

    images = glob.iglob(os.path.join(images_path, "*"))
    for image_path in images:
        image = np.load(image_path)

        number = os.path.basename(image_path).replace(".npy", "")
        label_path = os.path.join(labels_path, f"{number}.npy")
        label = np.load(label_path)

        stats[f"Patient_{number}"] = {
            "volume_shape": list(image.shape),
            "average_intensity": np.mean(image).tolist(),
            "max_intensity": np.max(image).tolist(),
            "min_intensity": np.min(image).tolist(),
            "pancreas_volume_ratio": np.mean(label).tolist(),
        }

    with open(output_path, "w") as f:
        yaml.safe_dump(stats, f)
