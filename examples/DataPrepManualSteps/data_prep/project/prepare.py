import os
import shutil
import argparse
import pandas as pd
import yaml


def prepare(data: pd.DataFrame, labels: pd.DataFrame, report: pd.DataFrame):
    """Takes a dataframe containing the raw data and transforms the data.


    Args:
        data (pd.DataFrame): DataFrame containing the data to be prepared
        labels (pd.DataFrame): DataFrame containing the labels to be prepared
        report (pd.DataFrame): DataFrame that will contain information of
        per-case preparation status, as well as comments for next steps
    """

    processing_df = pd.concat([data, labels, report], axis=1)
    if "density" not in processing_df.columns:
        processing_df["density"] = None
    if "verified" not in processing_df.columns:
        processing_df["verified"] = 0
    if "test_passed" in processing_df.columns:
        processing_df.rename(columns={"test_passed": "label"}, inplace=True)

    # Apply per-sample transforms
    processing_df = processing_df.apply(transform_row, axis=1)

    # Apply whole dataset transforms
    processing_df = transform_dataframe(processing_df)

    # TODO: decide if "verified" goes here
    data = processing_df[["weight", "volume", "density", "verified"]]
    report = processing_df[["status", "status_name", "comment"]]

    return data, labels, report


def transform_row(row: pd.Series):
    """Checks the status of the row, and applies transformations accordingly

    Args:
        row (pd.Series): Dataframe with data, labels and report information
    """

    # We could probably come up with ways of skipping failed transforms
    # and applying later ones if they don't interfere.
    # e.g. transform the volume even if weight transformation failed
    # But, this might be error-prone and unintuitive for the user

    # Current implementation assumes sequential, non-avoidable steps
    if row["status"] == 0:
        row["status"] = 1
        row["status_name"] = "PROCESSING_STARTED"

    if abs(row["status"]) == 1:
        try:
            # kg to g
            row["weight"] = float(row["weight"]) * 1000
            row["status"] = 2
            row["status_name"] = "WEIGHT_TRANSFORMED"
            row["comment"] = ""
        except:
            row["status"] = -1
            row["status_name"] = "WEIGHT_ERROR"
            row["comment"] = "The weight could not be scaled. Check the weight value"

    if abs(row["status"]) == 2:
        try:
            # m^3 to cm^3
            row["volume"] *= 1e6
            row["status"] = 3
            row["status_name"] = "VOLUME_TRANSFORMED"
            row["comment"] = ""
        except:
            row["status"] = -2
            row["status_name"] = "VOLUME_ERROR"
            row["comment"] = "Volume could not be scaled. Check volume value"

    if abs(row["status"]) == 3:
        try:
            # compute density g/cm^3
            row["density"] = row["weight"] / row["volume"]
            row["status"] = 4
            row["status_name"] = "DENSITY_COMPUTED"
            row["comment"] = ""
        except:
            row["density"] = -1
            row["status"] = -3
            row["status_name"] = "DENSITY_ERROR"
            row["comment"] = "Density computation could not be done. Check your data"

    if abs(row["status"]) == 4:
        try:
            # Transform labels
            row["test_passed"] = row["test_passed"] == "YES"
            row["status"] = 5
            row["status_name"] = "LABEL_TRANSFORMED"
            row["comment"] = ""
        except:
            row["status"] = -4
            row["status_name"] = "LABEL_ERROR"
            row[
                "comment"
            ] = 'Could not transform label. Check labels are either YES or NO and label name is "test_passed"'

    if abs(row["status"]) == 5:
        if "verified" in row and row["verified"]:
            row["status"] = 6
            row["status_name"] = "VERIFIED"
            row["comment"] = ""
        else:
            row["verified"] = 0
            row["status"] = -5
            row["status_name"] = "UNVERIFIED_ERROR"
            row[
                "comment"
            ] = 'Ensure the sample looks correct, and manually change the "verified" flag to 1 if so'

    return row


def transform_dataframe(df: pd.DataFrame):
    """Applies dataset-wise transformations

    Args:
        df (pd.DataFrame): Dataframe with data, labels and report information
    """
    if all(abs(df["status"]) == 6):
        try:
            df["weight"] = (df["weight"] - df["weight"].mean()) / df["weight"].std()
            df["status"] = 7
            df["status_name"] = "WEIGHT_NORMALIZED"
            df["comment"] = ""
        except:
            df["status"] = -6
            df["status_name"] = "WEIGHT_NORMALIZATION_ERROR"
            df["comment"] = "Weight could not be normalized. Check the weight values"

    if all(abs(df["status"]) == 7):
        try:
            df["volume"] = (df["volume"] - df["volume"].mean()) / df["volume"].std()
            df["status"] = 8
            df["status_name"] = "VOLUME_NORMALIZED"
            df["comment"] = ""
        except:
            df["status"] = -7
            df["status_name"] = "VOLUME_NORMALIZATION_ERROR"
            df["comment"] = "Volume could not be normalized. Check the volume values"

    return df


def generate_report(data: pd.DataFrame):
    """Generates a status report for the data preparation

    Args:
        data (pd.DataFrame): DataFrame containing the raw data
    """
    report = pd.DataFrame(index=data.index)
    report["status"] = 0
    report["status_name"] = "unprocessed"
    report["comment"] = ""
    return report


def get_data_df(files):
    files = os.listdir(files)
    csv_files = [file for file in files if file.endswith(".csv")]

    if len(csv_files):
        filepath = os.path.join(files, csv_files[0])
        df = pd.read_csv(filepath)
        return df


def get_df(path):
    names_files = os.listdir(path)
    csv_files = [file for file in names_files if file.endswith(".csv")]

    if len(csv_files) == 1:
        filepath = os.path.join(path, csv_files[0])
        df = pd.read_csv(filepath)
        return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Medperf Data Preparator Example")
    parser.add_argument(
        "--data_path", dest="data", type=str, help="path containing raw data"
    )
    parser.add_argument(
        "--labels_path", dest="labels", type=str, help="path containing labels"
    )
    parser.add_argument(
        "--data_out", dest="data_out", type=str, help="path to store prepared data"
    )
    parser.add_argument(
        "--labels_out",
        dest="labels_out",
        type=str,
        help="path to store prepared labels",
    )
    parser.add_argument(
        "--report", dest="report", type=str, help="path to the report csv file to store"
    )

    args = parser.parse_args()

    out_data = os.path.join(args.data_out, "data.csv")

    if os.path.exists(out_data):
        data_df = pd.read_csv(out_data)
    else:
        data_df = get_df(args.data)

    out_labels = os.path.join(args.labels_out, "labels.csv")
    if os.path.exists(out_labels):
        labels_df = pd.read_csv(out_labels)
    else:
        labels_df = get_df(args.labels)

    if os.path.exists(args.report):
        with open(args.report, "r") as f:
            report_dict = yaml.safe_load(f)

        report = pd.DataFrame(data=report_dict)
    else:
        report = generate_report(data_df)

    prepared_data, prepared_labels, report = prepare(data_df, labels_df, report)

    prepared_data.to_csv(out_data, index=False)
    prepared_labels.to_csv(out_labels, index=False)

    report_dict = report.to_dict()
    with open(args.report, "w") as f:
        yaml.dump(report_dict, f)
