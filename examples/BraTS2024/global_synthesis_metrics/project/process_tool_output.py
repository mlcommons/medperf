import argparse
import os
import re
import yaml
import json
import pandas as pd
import SimpleITK as sitk


def convert_to_brats_label_style(tool_outputs_dict):
    output_folder = "/corrected_predictions"
    os.makedirs(output_folder, exist_ok=True)
    tool_outputs_dict_corrected = {}
    for subj, path in tool_outputs_dict.items():
        img = sitk.ReadImage(path)
        mask_array = sitk.GetArrayFromImage(img)
        mask_array[mask_array == 4] = 3  # set the label from FeTS style to BraTS style
        new_img = sitk.GetImageFromArray(mask_array)
        new_img.CopyInformation(img)  # copy all meta information from the previous mask
        target_path = os.path.join(output_folder, os.path.basename(path))
        sitk.WriteImage(new_img, target_path)
        tool_outputs_dict_corrected[subj] = target_path

    return tool_outputs_dict_corrected


def process_tool_output(
    intermediate_folder, segmentation_labels_folder, seg_csv
):
    # collect tool output
    tool_outputs_dict = {}
    pattern = r".*(\d{5}-\d{3})\.nii\.gz$"
    for subj in os.listdir(intermediate_folder):
        reg = re.match(pattern, subj) 
        if not reg:
            continue
        
        subj_id = subj.split(".")[0]
        if os.path.isdir(subj):
            continue
        
        tool_outputs_dict[subj_id] = os.path.join(intermediate_folder, subj)
            
    tool_outputs_dict = convert_to_brats_label_style(tool_outputs_dict)

    # Read labels
    labels_dict = {}
    pattern = r".*(\d{5}-\d{3})-seg\.nii\.gz$"
    for file in os.listdir(segmentation_labels_folder):
        reg = re.match(pattern, file)
        if not reg:
            continue
        subject_id = reg.groups()[0]
        labels_dict[subject_id] = os.path.join(segmentation_labels_folder, file)

    # create csv
    input_data = []
    for subject_id in tool_outputs_dict:
        prediction_record = {
            "SubjectID": subject_id,
            "Prediction": tool_outputs_dict[subject_id],
            "Target": labels_dict[subject_id],
        }
        input_data.append(prediction_record)

    input_data_df = pd.DataFrame(input_data)
    os.makedirs(os.path.dirname(os.path.abspath(seg_csv)), exist_ok=True)
    input_data_df.to_csv(seg_csv, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--intermediate_folder")
    parser.add_argument("--labels")
    parser.add_argument("--parameters_file")
    parser.add_argument("--seg_csv")
 
    args = parser.parse_args()
    intermediate_folder = args.intermediate_folder
    labels = args.labels
    seg_csv = args.seg_csv

    with open(args.parameters_file) as f:
        parameters = yaml.safe_load(f)

    segmentation_labels = parameters["segmentation_labels"]
    segmentation_labels_folder = os.path.join(labels, segmentation_labels)

    process_tool_output(
        intermediate_folder, segmentation_labels_folder, seg_csv
    )
