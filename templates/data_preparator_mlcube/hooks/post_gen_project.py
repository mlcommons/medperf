#!/usr/bin/env python
import os
import shutil

PROJECT_DIRECTORY = os.path.realpath(os.path.curdir)


if __name__ == "__main__":
    if "{{ cookiecutter.use_separate_output_labels }}" != "y":
        input_labels_path = os.path.join(
            "{{ cookiecutter.project_slug }}", "mlcube/workspace/input_labels"
        )
        shutil.rmtree()
