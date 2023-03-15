#!/usr/bin/env python
import os

PROJECT_DIRECTORY = os.path.realpath(os.path.curdir)


if __name__ == "__main__":
    input_data_path = "mlcube/workspace/input_data"
    input_labels_path = "mlcube/workspace/input_labels"
    data_path = "mlcube/workspace/data"

    paths = [input_data_path, input_labels_path, data_path]

    if "{{ cookiecutter.use_separate_output_labels }}" == "y":
        labels_path = "mlcube/workspace/labels"
        paths.append(labels_path)

    for path in paths:
        os.makedirs(path, exist_ok=True)
