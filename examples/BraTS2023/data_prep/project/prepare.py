import os
import shutil
from glob import iglob
import random
import json

random.seed(7)


def __copy_modalities(input_folder, modalities, output_folder):
    for file in iglob(os.path.join(input_folder, "*.nii.gz")):
        for modality in modalities:
            if file.endswith(f"{modality}.nii.gz"):
                new_file = os.path.join(output_folder, os.path.basename(file))
                shutil.copyfile(file, new_file)
                break


def copy_segmentation_data(
    data_path, labels_path, parameters, output_path, output_labels_path
):
    # copy data
    modalities = parameters["segmentation_modalities"]
    for folder in iglob(os.path.join(data_path, "*/")):
        outfolder = os.path.join(
            output_path, os.path.basename(os.path.normpath(folder))
        )
        os.makedirs(outfolder, exist_ok=True)
        __copy_modalities(folder, modalities, outfolder)

    # copy labels
    for folder_or_file in iglob(os.path.join(labels_path, "*")):
        if os.path.isdir(folder_or_file):
            __copy_modalities(folder_or_file, ["seg"], output_labels_path)
        else:
            file = folder_or_file
            if file.endswith(f"seg.nii.gz"):
                new_file = os.path.join(output_labels_path, os.path.basename(file))
                shutil.copyfile(file, new_file)


def post_process_for_synthesis(parameters, output_path, output_labels_path):
    modalities = parameters["segmentation_modalities"]
    original_data_in_labels = parameters["original_data_in_labels"]
    segmentation_labels = parameters["segmentation_labels"]
    missing_modality_json = parameters["missing_modality_json"]

    # move labels to a sub directory
    labels_subdir = os.path.join(output_labels_path, segmentation_labels)
    os.makedirs(labels_subdir, exist_ok=True)
    for obj in iglob(os.path.join(output_labels_path, "*")):
        if os.path.normpath(obj) != os.path.normpath(labels_subdir):
            shutil.move(obj, labels_subdir)

    # copy data to labels for metrics calculation
    data_subdir = os.path.join(output_labels_path, original_data_in_labels)
    shutil.copytree(output_path, data_subdir)

    # drop modalities
    missing_modality_dict = {}
    for folder in iglob(os.path.join(output_path, "*/")):
        missing_modality = random.choice(modalities)
        for file in iglob(os.path.join(folder, "*.nii.gz")):
            if file.endswith(f"{missing_modality}.nii.gz"):
                os.remove(file)
                break
        foldername = os.path.basename(os.path.normpath(folder))
        missing_modality_dict[foldername] = missing_modality

    out_json = os.path.join(output_labels_path, missing_modality_json)
    with open(out_json, "w") as f:
        json.dump(missing_modality_dict, f)


def copy_inpainting_data(
    data_path, labels_path, parameters, output_path, output_labels_path
):
    # copy data
    modalities = ["mask", "t1n-voided"]
    for folder in iglob(os.path.join(data_path, "*/")):
        outfolder = os.path.join(
            output_path, os.path.basename(os.path.normpath(folder))
        )
        os.makedirs(outfolder, exist_ok=True)
        __copy_modalities(folder, modalities, outfolder)

    # copy labels
    modalities = ["mask-healthy", "t1n"]
    for folder in iglob(os.path.join(labels_path, "*/")):
        outfolder = os.path.join(
            output_labels_path, os.path.basename(os.path.normpath(folder))
        )
        os.makedirs(outfolder, exist_ok=True)
        __copy_modalities(folder, modalities, outfolder)


def prepare_dataset(
    data_path, labels_path, parameters, output_path, output_labels_path
):
    task = parameters["task"]
    assert task in ["segmentation", "inpainting", "synthesis"], "Invalid task"
    os.makedirs(output_path, exist_ok=True)
    os.makedirs(output_labels_path, exist_ok=True)

    if task in ["segmentation", "synthesis"]:
        copy_segmentation_data(
            data_path, labels_path, parameters, output_path, output_labels_path
        )
        if task == "synthesis":
            post_process_for_synthesis(parameters, output_path, output_labels_path)

    else:
        copy_inpainting_data(
            data_path, labels_path, parameters, output_path, output_labels_path
        )
