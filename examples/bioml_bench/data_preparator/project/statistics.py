"""Reports the size of a prepared BioML-bench task. Only row counts are sent to
the server, nothing about the answers."""

import os

import pandas as pd
import yaml

DATA_PATH = "/mlcommons/volumes/data"
PARAMETERS_PATH = "/mlcommons/volumes/parameters/parameters_file.yaml"
STATISTICS_PATH = "/mlcommons/volumes/statistics/statistics.yaml"


def main():
    with open(PARAMETERS_PATH) as f:
        task_id = yaml.safe_load(f)["task_id"]

    rows_per_file = {}
    for name in sorted(os.listdir(DATA_PATH)):
        if name.endswith(".csv"):
            rows_per_file[name] = len(pd.read_csv(os.path.join(DATA_PATH, name)))

    statistics = {
        "task_id": task_id,
        "num_test_samples": rows_per_file["sample_submission.csv"],
        "rows_per_file": rows_per_file,
    }
    with open(STATISTICS_PATH, "w") as f:
        yaml.safe_dump(statistics, f, sort_keys=False)


if __name__ == "__main__":
    main()
