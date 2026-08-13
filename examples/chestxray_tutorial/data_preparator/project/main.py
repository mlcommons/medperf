import argparse

import yaml

from prepare import prepare_dataset
from sanity_check import perform_sanity_checks
from statistics import generate_statistics


PARAMETERS_FILE = "/mlcommons/volumes/parameters/parameters_file.yaml"
RAW_DATA = "/mlcommons/volumes/raw_data"
RAW_LABELS = "/mlcommons/volumes/raw_labels"
DATA = "/mlcommons/volumes/data"
LABELS = "/mlcommons/volumes/labels"
STATISTICS_FILE = "/mlcommons/volumes/statistics/statistics.yaml"


def main():
    parser = argparse.ArgumentParser(description="ChestXRay data preparator")
    parser.add_argument(
        "--start",
        choices=["prepare", "sanity_check"],
        default="prepare",
    )
    args = parser.parse_args()

    with open(PARAMETERS_FILE) as f:
        parameters = yaml.safe_load(f)

    if args.start == "prepare":
        prepare_dataset(RAW_DATA, RAW_LABELS, parameters, DATA, LABELS)
    else:
        perform_sanity_checks(DATA, LABELS, parameters)
        generate_statistics(DATA, LABELS, parameters, STATISTICS_FILE)


if __name__ == "__main__":
    main()
