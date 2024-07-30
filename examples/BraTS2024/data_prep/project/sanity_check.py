import os


def check_subject_validity_for_segmentation(labels_path, subject_dir, parameters):
    modalities = parameters["segmentation_modalities"]
    label_modality = parameters["label_modality"]

    # data
    strings_to_check = [f"_{modality}.nii.gz" for modality in modalities]
    for string in strings_to_check:
        if not os.path.isfile(
            os.path.join(subject_dir, os.path.basename(subject_dir) + string)
        ):
            raise ValueError(
                f"{os.path.basename(subject_dir)} does not contain all modalities"
            )

    assert len(os.listdir(subject_dir)) == len(
        modalities
    ), "invalid number of modalities"

    # labels
    if not os.path.isfile(
        os.path.join(
            labels_path, os.path.basename(subject_dir) + f"_{label_modality}.nii.gz"
        )
    ):
        raise ValueError(
            f"{os.path.basename(subject_dir)} does not contain segmentation labels"
        )


def check_subject_validity_for_pathology(labels_path, data_path):
    # data
    if not all(file.endswith("png") for file in os.listdir(data_path)):
        raise ValueError(
            f"{os.path.basename(data_path)} should only contain PNG files"
        )

    # labels
    assert len(os.listdir(labels_path)) == 1, "invalid number of labels file"
    if not os.listdir(labels_path)[0].endswith("csv"):
        raise ValueError(
            f"{labels_path} does not contain classification labels in a CSV file"
        )


def perform_sanity_checks(data_path, labels_path, parameters):
    task = parameters["task"]

    if task == "segmentation-radiotherapy":
        data_folders = os.listdir(data_path)
        for folder in data_folders:
            current_subject = os.path.join(data_path, folder)
            assert os.path.isdir(current_subject), "Unexpected file found"
            check_subject_validity_for_segmentation(
                labels_path, current_subject, parameters
            )
    else:
        check_subject_validity_for_pathology(labels_path, data_path)
