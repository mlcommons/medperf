"""MLCube handler file"""

import os
import typer
import yaml
import pandas as pd
from metrics import AUC, F1, reformat_data


app = typer.Typer()


class EvaluateTask(object):
    """Runs evaluation metrics given the predictions and label files

    Args:
        object ([type]): [description]
    """

    @staticmethod
    def run(
        labels_csv: str, preds_csv: str, parameters_file: str, output_file: str
    ) -> None:
        with open(parameters_file, "r") as f:
            params = yaml.full_load(f)

        labels = pd.read_csv(labels_csv)
        preds = pd.read_csv(preds_csv)

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

        with open(output_file, "w") as f:
            yaml.dump(results, f)


@app.command("evaluate")
def evaluate(
    labels: str = typer.Option(..., "--labels"),
    predictions: str = typer.Option(..., "--predictions"),
    parameters_file: str = typer.Option(..., "--parameters_file"),
    output_path: str = typer.Option(..., "--output_path"),
):
    files = next(os.walk(labels))[2]
    csvs = [file for file in files if file.endswith(".csv")]
    assert len(csvs) == 1, "Labels path must contain only one csv file"
    labels_csv = os.path.join(labels, csvs[0])
    preds_csv = os.path.join(predictions, "predictions.csv")
    EvaluateTask.run(labels_csv, preds_csv, parameters_file, output_path)


@app.command("test")
def test():
    pass


if __name__ == "__main__":
    app()
