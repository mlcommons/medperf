import argparse
import csv
from pathlib import Path
import yaml
import numpy as np
from sklearn.metrics import (
    f1_score,
    accuracy_score,
    jaccard_score,
    recall_score,
    precision_score,
)


class MetricsClass:
    """Class wrapper for calculating the supported metrics
    
    Args:
        num_classes (int): The number of classes in the dataset

    """

    def __init__(self, num_classes):
        self.num_classes = num_classes

    def f1_score(self, labels, preds):
        """Calculates the F1-score metric using scikit-learn library
        with macro-averaging across classes.
    
        Args:
            labels (1D-array[int]): The ground-truth labels
            preds (1D-array[int]): The predictions

        Returns:
            float: the F1-score metric
        """
        return f1_score(
            labels, preds, average="macro", labels=list(range(self.num_classes))
        )

    def precision(self, labels, preds):
        """Calculates the Precision metric using scikit-learn library
        with macro-averaging across classes.
    
        Args:
            labels (1D-array[int]): The ground-truth labels
            preds (1D-array[int]): The predictions

        Returns:
            float: the Precision metric
        """
        return precision_score(
            labels, preds, average="macro", labels=list(range(self.num_classes))
        )

    def jaccard(self, labels, preds):
        """Calculates the Jaccard-score metric using scikit-learn library
        with macro-averaging across classes.
    
        Args:
            labels (1D-array[int]): The ground-truth labels
            preds (1D-array[int]): The predictions

        Returns:
            float: the Jaccard-score metric
        """
        return jaccard_score(
            labels, preds, average="macro", labels=list(range(self.num_classes))
        )

    def recall(self, labels, preds):
        """Calculates the Recall metric using scikit-learn library
        with macro-averaging across classes.
    
        Args:
            labels (1D-array[int]): The ground-truth labels
            preds (1D-array[int]): The predictions

        Returns:
            float: the Recall metric
        """
        return recall_score(
            labels, preds, average="macro", labels=list(range(self.num_classes))
        )

    def accuracy(self, labels, preds):
        """Calculates the Accuracy metric using scikit-learn library
    
        Args:
            labels (1D-array[int]): The ground-truth labels
            preds (1D-array[int]): The predictions

        Returns:
            float: the Accuracy metric
        """
        return accuracy_score(labels, preds)


class Evaluation:
    """Class wrapper for calculating the supported metrics
    
    For each supported metric in the configuration file:
        - the overall metric value across the videos is calculated
        - the video-level mean and standard deviation of the metric
          value across the videos are calculated.

    Args:
        preds_path (str): predictions location.
        parameters_file (str): yaml file with additional parameters
        output_file (str): location to the results

    """

    def __init__(self, preds_path, parameters_file, output_file):
        with open(parameters_file, "r") as f:
            self.params = yaml.full_load(f)

        metrics_class = MetricsClass(self.params["num_classes"])
        self.available_metrics = {
            "f1-score": metrics_class.f1_score,
            "recall": metrics_class.recall,
            "precision": metrics_class.precision,
            "jaccard": metrics_class.jaccard,
            "accuracy": metrics_class.accuracy,
        }

        self.output_file = output_file
        self.preds_path = Path(preds_path)

    def run(self):
        labels = list()
        preds = list()

        preds_files = self.preds_path.glob("*.csv")
        for file in preds_files:
            labels.append([])
            preds.append([])
            with open(file) as f:
                reader = csv.reader(f)
                for i, row in enumerate(reader):
                    if i == 0:
                        continue
                    labels[-1].append(int(row[1]))
                    preds[-1].append(int(row[2]))

        results = {"overall": {}, "per_video": {}}

        for metric_name in self.params["metrics"]:
            metric = self.available_metrics[metric_name]
            scores_per_video = []
            for vid_labels, vid_preds in zip(labels, preds):
                scores = metric(vid_labels, vid_preds)
                scores_per_video.append(float(scores))
            scores = metric(sum(labels, []), sum(preds, []))
            results["overall"][metric_name] = float(scores)
            results["per_video"][metric_name] = {
                "mean": float(np.mean(scores_per_video)),
                "std": float(np.std(scores_per_video)),
            }

        with open(self.output_file, "w") as f:
            yaml.dump(results, f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--preds_path",
        "--preds-path",
        type=str,
        required=True,
        help="folder containing the labels and preds",
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

    evaluator = Evaluation(args.preds_path, args.parameters_file, args.output_file)

    evaluator.run()
