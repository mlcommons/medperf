"""Checks a prepared BioML-bench task: the model gets a sample submission, the
evaluator gets the answers, and both list the same test ids."""

import os

import pandas as pd

DATA_PATH = "/mlcommons/volumes/data"
LABELS_PATH = "/mlcommons/volumes/labels"


def main():
    sample_submission = pd.read_csv(os.path.join(DATA_PATH, "sample_submission.csv"))
    answers = pd.read_csv(os.path.join(LABELS_PATH, "answers.csv"))
    assert os.path.exists(os.path.join(DATA_PATH, "description.md")), "description.md is missing"
    assert len(sample_submission) > 0, "sample_submission.csv is empty"
    assert not os.path.exists(os.path.join(DATA_PATH, "answers.csv")), "answers.csv must not be in the data"

    submission_ids = sample_submission.iloc[:, 0]
    answer_ids = answers.iloc[:, 0]
    assert submission_ids.is_unique, "sample_submission.csv has duplicated ids"
    assert answer_ids.is_unique, "answers.csv has duplicated ids"
    assert set(submission_ids) == set(answer_ids), "sample_submission.csv and answers.csv list different ids"
    assert not answers.iloc[:, 1:].isna().all(axis=None), "answers.csv has no answers"
    print(f"Sanity check passed: {len(answers)} test samples")


if __name__ == "__main__":
    main()
