import os
import shutil
from drop_modalities import drop_modalities


def prepare_dataset(
    data_path, labels_path, parameters, output_path, output_labels_path
):
    task = parameters["task"]
    assert task in ["segmentation", "inpainting", "synthesis"], "Invalid task"

    if task in ["segmentation", "inpainting"]:
        shutil.copytree(data_path, output_path, dirs_exist_ok=True)
        shutil.copytree(labels_path, output_labels_path, dirs_exist_ok=True)

    else:
        modalities = parameters["segmentation_modalities"]
        original_data_in_labels = parameters["original_data_in_labels"]
        segmentation_labels = parameters["segmentation_labels"]
        original_data_in_labels = os.path.join(
            output_labels_path, original_data_in_labels
        )
        segmentation_labels = os.path.join(output_labels_path, segmentation_labels)
        drop_modalities(data_path, output_path, modalities)

        shutil.copytree(output_path, original_data_in_labels, dirs_exist_ok=True)
        shutil.copytree(labels_path, segmentation_labels, dirs_exist_ok=True)
