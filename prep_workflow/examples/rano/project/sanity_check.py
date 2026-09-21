import yaml
import argparse
import pandas as pd

from stages.utils import has_prepared_folder_structure


def sanity_check(data_path: str, labels_path: str):
    """Runs a few checks to ensure data quality and integrity

    Args:
        data_path (str): Path to data.
        labels_path (str): Path to labels.
    """
    # Here you must add all the checks you consider important regarding the
    # state of the data
    if not has_prepared_folder_structure(data_path, labels_path):
        print("The contents of the labels and data don't resemble a prepared dataset", flush=True)
        exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Medperf Model Sanity Check Example")
    parser.add_argument(
        "--data_path",
        dest="data",
        type=str,
        help="directory containing the prepared data",
    )
    parser.add_argument(
        "--labels_path",
        dest="labels",
        type=str,
        help="directory containing the prepared labels",
    )
    parser.add_argument(
        "--metadata_path",
        dest="metadata_path",
        type=str,
        help="path to the local metadata folder",
    )

    args = parser.parse_args()

    sanity_check(args.data, args.labels)
