"""Scores a submission with the task's own grade.py and, when the task's
leaderboard is available, ranks it as BioML-bench does (percentile, medals)."""

import math
import os
import tempfile

import pandas as pd
import yaml

from biomlbench_task import POLARIS_BENCHMARK_DIR, get_task, read_task_id, use_local_polaris_benchmark

PREDICTIONS_PATH = "/mlcommons/volumes/predictions"
LABELS_PATH = "/mlcommons/volumes/labels"
PARAMETERS_PATH = "/mlcommons/volumes/parameters/parameters_file.yaml"
ADDITIONAL_FILES_PATH = "/mlcommons/volumes/additional_files"
RESULTS_PATH = "/mlcommons/volumes/results/results.yaml"


def grade(task, submission_path):
    from biomlbench.utils import read_csv

    if not os.path.exists(submission_path):
        print(f"{submission_path} not found")
        return None
    answers = read_csv(os.path.join(LABELS_PATH, "answers.csv"))
    # None if grade.py rejects the submission, as in BioML-bench
    return task.grader(read_csv(submission_path), answers)


def main():
    task_id = read_task_id(PARAMETERS_PATH)
    with tempfile.TemporaryDirectory() as data_dir:
        task = get_task(task_id, data_dir)
    if task.data_source["type"] == "polaris":
        use_local_polaris_benchmark(task, os.path.join(LABELS_PATH, POLARIS_BENCHMARK_DIR))

    score = grade(task, os.path.join(PREDICTIONS_PATH, "submission.csv"))
    results = {"valid_submission": score is not None}
    if score is not None and math.isnan(score):
        # e.g. a correlation with constant predictions. NaN can't be sent to the
        # server as JSON, so the score is reported as missing
        print("The score is undefined (NaN)")
        score = None
    results = {"score": None if score is None else float(score), **results}

    leaderboard_path = os.path.join(ADDITIONAL_FILES_PATH, "leaderboard.csv")
    if os.path.exists(leaderboard_path):
        leaderboard = pd.read_csv(leaderboard_path)
        rank = task.grader.rank_score(score, leaderboard)
        rank["any_medal"] = rank["gold_medal"] or rank["silver_medal"] or rank["bronze_medal"]
        rank["is_lower_better"] = task.grader.is_lower_better(leaderboard)
        results.update({key: value.item() if hasattr(value, "item") else value for key, value in rank.items()})
    else:
        print("No leaderboard in the additional files: the score is not ranked")

    with open(RESULTS_PATH, "w") as f:
        yaml.safe_dump(results, f, sort_keys=False)
    print(results)


if __name__ == "__main__":
    main()
