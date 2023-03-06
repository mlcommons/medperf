#!/usr/bin/env python
import os

PROJECT_DIRECTORY = os.path.realpath(os.path.curdir)


if __name__ == "__main__":
    preds_path = "mlcube/workspace/predictions"
    labels_path = "mlcube/workspace/labels"

    paths = [preds_path, labels_path]

    if "{{ cookiecutter.use_separate_output_labels }}" == "y":
        input_labels_path = "mlcube/workspace/input_labels"
        paths.append(input_labels_path)

    for path in paths:
        os.makedirs(path, exist_ok=True)
