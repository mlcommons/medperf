# Hello World Script
#
# This script is unrelated to the MLCube interface. It could be run
# independently without issues. It provides the actual implementation
# of the metrics. This file is executed by MLCube through mlcube.py
import argparse
import yaml
import pandas as pd


class ACC:
    # Given this is a toy example, the metric is implemented by hand
    # It is recommended that metrics are obtained from trusted
    # libraries
    @staticmethod
    def run(labels, preds):
        total_count = len(labels)
        correct_count = (labels == preds).sum()
        return correct_count / total_count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--labels_csv",
        "--labels-csv",
        type=str,
        required=True,
        help="File containing the labels",
    )
    parser.add_argument(
        "--preds_csv",
        "--preds-csv",
        type=str,
        required=True,
        help="File containing the predictions",
    )
    parser.add_argument(
        "--output_file",
        "--output-file",
        type=str,
        required=True,
        help="file to store metrics results as YAML",
    )
    parser.add_argument(
        "--parameters_file",
        "--parameters-file",
        type=str,
        required=True,
        help="File containing parameters for evaluation",
    )
    args = parser.parse_args()

    # Load all files

    with open(args.parameters_file, "r") as f:
        params = yaml.full_load(f)

    labels = pd.read_csv(args.labels_csv)
    preds = pd.read_csv(args.preds_csv)

    labels = reformat_data(labels, params)
    preds = reformat_data(preds, params)

    available_metrics = {
        "ACC": ACC,
    }
    results = {}
    cols = list(labels.columns)
    for metric_name in params["metrics"]:
        metric = available_metrics[metric_name]
        scores = metric.run(labels, preds)
        scores = {col: score for col, score in zip(cols, scores)}
        results[metric_name] = scores

    with open(args.output_file, "w") as f:
        yaml.dump(results, f)


def reformat_data(df, params):
    """Ensures that the dataframe contains the desired label columns and is sorted by a defined identifier column
    Args:
        df (pd.DataFrame): dataframe containing data labels and an identifier for each row
        params (dict): dictionary containing key-value pairs for identified the labels-of-interest and the common identifier column.
    Returns:
        pd.DataFrame: reformatted labels and predictions respectively
    """
    label_cols = params["label columns"]
    id_col = params["id column"]
    select_cols = label_cols + [id_col]

    df = df[select_cols]
    df = df.set_index(id_col)
    df = df.sort_index()
    return df


if __name__ == "__main__":
    main()