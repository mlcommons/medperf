import os
import yaml
import argparse
import pandas as pd


def sanity_check(data_df, labels_df, report_df):
    """Runs a few checks to ensure data quality and integrity

    Args:
        data_df (pd.DataFrame): DataFrame containing transformed data.
    """
    # Here you must add all the checks you consider important regarding the
    # state of the data
    assert all(report_df["status"] == 8), "Data has not been fully prepared"
    assert all(data_df["verified"]), "Data has not been fully verified"

    assert data_df.columns.tolist() == [
        "weight",
        "volume",
        "density",
        "verified",
    ], "Data Column mismatch"

    epsilon = 1e-3
    assert (
        -epsilon < data_df["weight"].mean() < epsilon
    ), "Weight has not been normalized"
    assert (
        1 - epsilon < data_df["weight"].std() < 1 + epsilon
    ), "Weight has not been normalized"
    assert (
        -epsilon < data_df["volume"].mean() < epsilon
    ), "Volume has not been normalized"
    assert (
        1 - epsilon < data_df["volume"].std() < 1 + epsilon
    ), "Volume has not been normalized"

    assert labels_df.columns.tolist() == ["label"], "Label Column mismatch"
    assert set(labels_df["label"]) == {0, 1}, "Invalid label values"


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
        "--report", dest="report", type=str, help="path to the report file"
    )

    args = parser.parse_args()

    data_file = os.path.join(args.data, "data.csv")
    labels_file = os.path.join(args.labels, "labels.csv")

    data_df = pd.read_csv(data_file)
    labels_df = pd.read_csv(labels_file)

    with open(args.report, "r") as f:
        report_dict = yaml.safe_load(f)
        report_df = pd.DataFrame(data=report_dict)

    sanity_check(data_df, labels_df, report_df)
