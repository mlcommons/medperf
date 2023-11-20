import os
import argparse
import sys
import re
import pandas as pd
import yaml


def create_csv(predictions, labels):
    """A function that creates a ./data.csv file from input folders."""

    # labels
    labels_dict = {}
    pattern = r".*(\d{5}-\d{3})-seg\.nii\.gz$"
    for file in os.listdir(labels):
        reg = re.match(pattern, file)
        if not reg:
            continue
        subject_id = reg.groups()[0]
        labels_dict[subject_id] = os.path.join(labels, file)

    # predictions
    predictions_dict = {}
    pattern = r".*(\d{5}-\d{3})\.nii\.gz$"
    for file in os.listdir(predictions):
        reg = re.match(pattern, file)
        if not reg:
            raise RuntimeError(f"Unexpected predictions structure: {file}")
        subject_id = reg.groups()[0]
        predictions_dict[subject_id] = os.path.join(predictions, file)
        assert (
            subject_id in labels_dict
        ), "Prediction doesn't have a corresponding label"

    assert len(labels_dict) == len(
        predictions_dict
    ), "Predictions number don't match labels"

    # generate data input dict
    input_data = []
    for subject_id in predictions_dict:
        prediction_record = {
            "SubjectID": subject_id,
            "Prediction": predictions_dict[subject_id],
            "Target": labels_dict[subject_id],
        }
        input_data.append(prediction_record)

    input_data_df = pd.DataFrame(input_data)
    input_data_df.to_csv("./data.csv", index=False)


def run_gandlf(output_path, parameters_file):
    """
    A function that calls GaNDLF's generate metrics command with the previously created csv.

    Args:
        output_path (str): The path to the output file/folder
        parameters_file (str): The path to the parameters file
    """
    with open(parameters_file) as f:
        parameters = yaml.safe_load(f)
    challenge = parameters["challenge"]

    exit_status = os.system(
        f"python3.8 gandlf_generateBraTSMetrics -c {challenge} -i ./data.csv -o {output_path}"
    )
    exit_code = os.WEXITSTATUS(exit_status)
    sys.exit(exit_code)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--parameters_file", metavar="", type=str, required=True)
    parser.add_argument("--predictions", metavar="", type=str, required=True)
    parser.add_argument("--output_path", metavar="", type=str, default=None)
    parser.add_argument("--labels", metavar="", type=str, required=True)

    args = parser.parse_args()

    create_csv(args.predictions, args.labels)
    run_gandlf(args.output_path, args.parameters_file)
