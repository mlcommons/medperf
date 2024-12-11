import os
import yaml
import argparse
import pandas as pd


if __name__ == "__main__":
    parser = argparse.ArgumentParser("MedPerf Statistics Example")
    parser.add_argument(
        "--data_path",
        dest="data",
        type=str,
        help="directory containing the prepared data",
    )
    parser.add_argument(
        "--labels_path",
        dest="labels",
    )
    parser.add_argument(
        "--out_file", dest="out_file", type=str, help="file to store statistics"
    )
    parser.add_argument(
        "--metadata_path",
        dest="metadata_path",
        type=str,
        help="path to the local metadata folder",
    )

    args = parser.parse_args()

    splits_path = os.path.join(args.data, "splits.csv")
    invalid_path = os.path.join(args.metadata_path, ".invalid.txt")

    invalid_subjects = []
    if os.path.exists(invalid_path):
        with open(invalid_path, "r") as f:
            invalid_subjects = f.readlines()

    splits_df = pd.read_csv(splits_path)

    num_train_subjects = len(splits_df[splits_df["Split"] == "Train"])
    num_val_subjects = len(splits_df[splits_df["Split"] == "Val"])

    num_invalid_subjects = len(invalid_subjects)

    stats = {
        "num_train_subjects": num_train_subjects,
        "num_val_subjects": num_val_subjects,
        "num_invalid_subjects": num_invalid_subjects
    }

    with open(args.out_file, "w") as f:
        yaml.dump(stats, f)
