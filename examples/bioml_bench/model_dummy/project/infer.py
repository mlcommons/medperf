"""BioML-bench's Dummy baseline: submits the task's sample submission as the
predictions. It works for every CSV task and gives the lowest reference score."""

import os
import shutil

DATA_PATH = "/mlcommons/volumes/data"
PREDICTIONS_PATH = "/mlcommons/volumes/predictions"


def main():
    sample_submission = os.path.join(DATA_PATH, "sample_submission.csv")
    if not os.path.exists(sample_submission):
        raise FileNotFoundError(f"{sample_submission} not found")
    shutil.copy(sample_submission, os.path.join(PREDICTIONS_PATH, "submission.csv"))
    print("Copied sample_submission.csv to the predictions")


if __name__ == "__main__":
    main()
