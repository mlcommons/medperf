import os
import numpy as np
import SimpleITK as sitk


def check_image_dims(path):
    base_size = np.array([240, 240, 155])
    base_spacing = np.array([1.0, 1.0, 1.0])
    image = sitk.ReadImage(path)
    size_array = np.array(image.GetSize())
    spacing_array = np.array(image.GetSpacing())

    assert (base_size == size_array).all(), (
        "Image size is not [240,240,155] for " + path
    )
    assert np.isclose(base_spacing, spacing_array).all(), (
        "Image resolution is not [1,1,1] for " + path
    )


def check_subject_validity_for_segmentation(labels_path, subject_dir, parameters):
    modalities = parameters["segmentation_modalities"]

    strings_to_check = [f"-{modality}.nii.gz" for modality in modalities]

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
        os.path.join(labels_path, os.path.basename(subject_dir) + "-seg.nii.gz")
    ):
        raise ValueError(
            f"{os.path.basename(subject_dir)} does not contain segmentation labels"
        )


def check_subject_validity_for_synthesis(labels_path, subject_dir, parameters):
    modalities = parameters["segmentation_modalities"]
    original_data_in_labels = parameters["original_data_in_labels"]
    segmentation_labels = parameters["segmentation_labels"]

    strings_to_check = [f"-{modality}.nii.gz" for modality in modalities]

    for folder in [
        subject_dir,
        os.path.join(
            labels_path, original_data_in_labels, os.path.basename(subject_dir)
        ),
    ]:  # checking both data input folder and data folder copied to labels
        missing_modalities = 0
        for string in strings_to_check:
            if not os.path.isfile(
                os.path.join(folder, os.path.basename(subject_dir) + string)
            ):
                missing_modalities += 1
        if folder == subject_dir:
            if missing_modalities != 1:
                raise ValueError(
                    f"{os.path.basename(subject_dir)} does not have one missing modality"
                )
            assert (
                len(os.listdir(folder)) == len(modalities) - 1
            ), "invalid number of modalities"
        else:
            if missing_modalities != 0:
                raise ValueError(
                    f"{os.path.basename(subject_dir)} does not have all data in labels"
                )
            assert len(os.listdir(folder)) == len(
                modalities
            ), "invalid number of modalities"

    # labels
    if not os.path.isfile(
        os.path.join(
            labels_path,
            segmentation_labels,
            os.path.basename(subject_dir) + "-seg.nii.gz",
        )
    ):
        raise ValueError(
            f"{os.path.basename(subject_dir)} does not contain segmentation labels"
        )


def check_subject_validity_for_inpainting(labels_path, subject_dir, parameters):
    strings_to_check = ["-mask.nii.gz", "-t1n-voided.nii.gz"]
    for string in strings_to_check:
        if not os.path.isfile(
            os.path.join(subject_dir, os.path.basename(subject_dir) + string)
        ):
            raise ValueError(
                f"{os.path.basename(subject_dir)} does not contain {string}"
            )
    assert len(os.listdir(subject_dir)) == len(
        strings_to_check
    ), "invalid number of modalities"

    # labels
    strings_to_check = ["-mask-healthy.nii.gz", "-t1n.nii.gz"]
    for string in strings_to_check:
        if not os.path.isfile(
            os.path.join(
                labels_path,
                os.path.basename(subject_dir),
                os.path.basename(subject_dir) + string,
            )
        ):
            raise ValueError(
                f"{os.path.basename(subject_dir)} does not contain {string}"
            )
    assert len(
        os.listdir(os.path.join(labels_path, os.path.basename(subject_dir)))
    ) == len(strings_to_check), "invalid number of modalities"


def perform_sanity_checks(data_path, labels_path, parameters):
    task = parameters["task"]
    data_folders = os.listdir(data_path)

    for folder in data_folders:
        current_subject = os.path.join(data_path, folder)
        assert os.path.isdir(current_subject), "Unexpected file found"
        if task == "segmentation":
            check_subject_validity_for_segmentation(
                labels_path, current_subject, parameters
            )
        elif task == "synthesis":
            check_subject_validity_for_synthesis(
                labels_path, current_subject, parameters
            )
        else:
            check_subject_validity_for_inpainting(
                labels_path, current_subject, parameters
            )
