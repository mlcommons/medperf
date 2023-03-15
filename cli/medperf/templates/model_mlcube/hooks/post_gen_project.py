#!/usr/bin/env python
import os

PROJECT_DIRECTORY = os.path.realpath(os.path.curdir)


if __name__ == "__main__":
    data_path = "mlcube/workspace/data"
    preds_path = "mlcube/workspace/predictions"

    paths = [preds_path, data_path]
    for path in paths:
        os.makedirs(path, exist_ok=True)
