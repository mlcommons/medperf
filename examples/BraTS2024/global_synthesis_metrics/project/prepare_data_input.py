import argparse
import os
import shutil
import re
import yaml
import json
import pandas as pd


def prepare_data_input(
    predictions, original_data, missing_modality_json, intermediate_folder, ssim_csv
):
    modalities = {"t1c": "t1ce", "t1n": "t1", "t2f": "flair", "t2w": "t2"}
    os.makedirs(intermediate_folder, exist_ok=True)

    # parse predictions
    predictions_dict = {}
    for file in os.listdir(predictions):
        subj_id = file[-len("xxxxx-xxx-mmm.nii.gz") : -len("-mmm.nii.gz")]
        predictions_dict[subj_id] = os.path.join(predictions, file)

    # read original data and rename
    original_missing = {}
    for subj in os.listdir(original_data):
        pattern = r".*(\d{5}-\d{3})$"
        reg = re.match(pattern, subj)
        if not reg:
            continue
        subj_id = reg.groups()[0]
        missing_modality = missing_modality_json[subj]

        folder = os.path.join(original_data, subj)
        inter_folder = os.path.join(intermediate_folder, subj)
        os.makedirs(inter_folder, exist_ok=True)

        for file in os.listdir(folder):
            if file.endswith(f"{missing_modality}.nii.gz"):
                original_missing[subj_id] = os.path.join(folder, file)
                continue
            file_path = os.path.join(folder, file)
            for modality in modalities:
                if modality == missing_modality:
                    continue
                suffix = f"-{modality}.nii.gz"
                if file.endswith(suffix):
                    newfile = file.replace(suffix, f"_{modalities[modality]}.nii.gz")
                    newfile = os.path.join(inter_folder, newfile)
                    shutil.copyfile(file_path, newfile)
                    break

        # move the prediction
        prediction = predictions_dict[subj_id]
        assert prediction.endswith(
            f"{missing_modality}.nii.gz"
        ), "Prediction is not the missing modality"
        prediction_name = os.path.basename(prediction)
        suffix = f"-{missing_modality}.nii.gz"
        newfile = prediction_name.replace(
            suffix, f"_{modalities[missing_modality]}.nii.gz"
        )
        newfile = os.path.join(inter_folder, newfile)
        shutil.copyfile(prediction, newfile)

    # prepare data csv for ssim
    input_data = []
    for subject_id in predictions_dict:
        prediction_record = {
            "SubjectID": subject_id,
            "Prediction": predictions_dict[subject_id],
            "Target": original_missing[subject_id],
        }
        input_data.append(prediction_record)

    input_data_df = pd.DataFrame(input_data)
    os.makedirs(os.path.dirname(os.path.abspath(ssim_csv)), exist_ok=True)
    input_data_df.to_csv(ssim_csv, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions")
    parser.add_argument("--labels")
    parser.add_argument("--intermediate_folder")
    parser.add_argument("--ssim_csv")
    parser.add_argument("--parameters_file")

    args = parser.parse_args()
    labels = args.labels
    predictions = args.predictions
    intermediate_folder = args.intermediate_folder
    ssim_csv = args.ssim_csv

    with open(args.parameters_file) as f:
        parameters = yaml.safe_load(f)

    original_data_in_labels = parameters["original_data_in_labels"]
    missing_modality_json = parameters["missing_modality_json"]
    segmentation_labels = parameters["segmentation_labels"]

    original_data_in_labels = os.path.join(labels, original_data_in_labels)
    missing_modality_json = json.load(open(os.path.join(labels, missing_modality_json)))
    segmentation_labels_folder = os.path.join(labels, segmentation_labels)

    prepare_data_input(
        predictions,
        original_data_in_labels,
        missing_modality_json,
        intermediate_folder,
        ssim_csv,
    )
