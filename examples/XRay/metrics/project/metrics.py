import argparse
import yaml
import pandas as pd
from sklearn.metrics import roc_auc_score, f1_score


class AUC:
    @staticmethod
    def run(labels, preds):
        results = roc_auc_score(labels, preds, average=None)
        return results.tolist()


class F1:
    @staticmethod
    def run(labels, preds):
        preds = preds > 0.5
        results = f1_score(labels, preds, average=None)
        return results.tolist()


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
        "AUC": AUC,
        "F1": F1,
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
