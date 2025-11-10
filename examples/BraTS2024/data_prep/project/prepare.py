import os
import random
import shutil
from glob import iglob

random.seed(7)


def __copy_modalities(input_folder, modalities, output_folder):
    for file in iglob(os.path.join(input_folder, "*.nii.gz")):
        for modality in modalities:
            if file.endswith(f"{modality}.nii.gz"):
                new_file = os.path.join(output_folder, os.path.basename(file))
                shutil.copyfile(file, new_file)
                break


def copy_radiotherapy_data(
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
    modality = parameters["label_modality"]
    for f in iglob(os.path.join(labels_path, "*")):
        if os.path.isdir(f):
            __copy_modalities(f, [modality], output_labels_path)
        else:
            if f.endswith(f"{modality}.nii.gz"):
                new_file = os.path.join(output_labels_path, os.path.basename(f))
                shutil.copyfile(f, new_file)


def copy_pathology_data(data_path, labels_path, output_path, output_labels_path):
    # copy data
    for file in iglob(os.path.join(data_path, "*.png")):
        new_file = os.path.join(output_path, os.path.basename(file))
        shutil.copyfile(file, new_file)

    # copy labels
    for file in iglob(os.path.join(labels_path, "*.csv")):
        new_file = os.path.join(output_labels_path, os.path.basename(file))
        shutil.copyfile(file, new_file)


def prepare_dataset(
    data_path, labels_path, parameters, output_path, output_labels_path
):
    task = parameters["task"]
    assert task in ["segmentation-radiotherapy", "pathology"], "Invalid task"
    os.makedirs(output_path, exist_ok=True)
    os.makedirs(output_labels_path, exist_ok=True)

    if task == "segmentation-radiotherapy":
        copy_radiotherapy_data(data_path, labels_path, parameters, output_path, output_labels_path)
    else:
        copy_pathology_data(data_path, labels_path, output_path, output_labels_path)
