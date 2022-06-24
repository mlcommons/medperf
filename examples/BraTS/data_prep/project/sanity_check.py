import os
import argparse

import SimpleITK as sitk
import numpy as np


def check_subject_validity(subject_dir):
    """Checks if a subject folder is valid.

    Args:
        subject_dir (str): The subject folder.

    Returns:
        bool: True if the subject folder is valid, False otherwise.
    """
    subject_valid = True
    strings_to_check = [
        "_t1.nii.gz",
        "_t1ce.nii.gz",
        "_t2.nii.gz",
        "_flair.nii.gz",
        "_seg.nii.gz",
    ]

    for string in strings_to_check:
        if not os.path.isfile(
            os.path.join(subject_dir, os.path.basename(subject_dir) + string)
        ):
            subject_valid = False
            break

    return subject_valid


def sanity_check(data_path):
    """Runs a few checks to ensure data quality and integrity

    Args:
        data_path (str): The input data folder.
    """
    all_files = os.listdir(data_path)

    # define base size and spacing
    base_size = np.array([240, 240, 155])
    base_spacing = np.array([1.0, 1.0, 1.0])

    for folders in all_files:
        current_subject = os.path.join(data_path, folders)
        if os.path.isdir(current_subject):

            assert check_subject_validity(
                current_subject
            ), "Subject {} does not contain all modalities or segmentation".format(
                current_subject
            )

            for files in os.listdir(current_subject):
                current_file = os.path.join(current_subject, files)
                if os.path.isfile(current_file):
                    # perform BraTS space check for all nifti images
                    if current_file.endswith(".nii.gz"):
                        image = sitk.ReadImage(current_file)
                        size_array = np.array(image.GetSize())
                        spacing_array = np.array(image.GetSpacing())

                        assert (base_size == size_array).all(), (
                            "Image size is not [240,240,155] for " + current_file
                        )
                        assert (base_spacing == spacing_array).all(), (
                            "Image resolution is not [1,1,1] for " + current_file
                        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser("BraTS Data Sanity Check")
    parser.add_argument(
        "--data_path",
        dest="data",
        type=str,
        help="directory containing the prepared data",
    )

    args = parser.parse_args()

    sanity_check(args.data)

    print("Finished")
