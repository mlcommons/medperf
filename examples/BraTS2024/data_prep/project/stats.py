import os
import yaml


def generate_statistics(data_path, labels_path, parameters, out_path):
    stats = {
        "Number of Subjects": len(os.listdir(data_path)),
    }

    with open(out_path, "w") as f:
        yaml.dump(stats, f)
