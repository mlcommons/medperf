import os
import numpy as np
import yaml


def generate_statistics(data_path, labels_path, parameters, out_path):
    labels_list = parameters["labels_list"]

    # number of cases
    num_cases = len(os.listdir(data_path))

    # read labels
    labels_files = os.listdir(labels_path)
    labels_files = [os.path.join(labels_path, file) for file in labels_files]
    labels = np.stack([np.load(file) for file in labels_files], axis=0)

    # calculate labels count
    labels_count = np.sum(labels, axis=0)
    labels_count_dict = {}
    for index, label in enumerate(labels_list):
        labels_count_dict[label] = labels_count[index].tolist()

    # write statistics
    statistics = {
        "num_cases": num_cases,
        "labels_count": labels_count_dict,
    }
    with open(out_path, "w") as f:
        yaml.safe_dump(statistics, f)
