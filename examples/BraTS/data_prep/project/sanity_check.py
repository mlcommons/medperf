from pathlib import Path
from typing import List, Tuple

import SimpleITK as sitk
import numpy as np


def check_subject_validity(subject_dir: Path, labels_dir: Path) -> List[Path]:
    """Runs a few checks to ensure data quality and integrity
    """
    subject_valid = True
    files_to_check = [
        subject_dir / f"{subject_dir.name}_brain_t1.nii.gz",
        subject_dir / f"{subject_dir.name}_brain_t1ce.nii.gz",
        subject_dir / f"{subject_dir.name}_brain_t2.nii.gz",
        subject_dir / f"{subject_dir.name}_brain_flair.nii.gz",
        labels_dir / f"{subject_dir.name}_final_seg.nii.gz",
    ]

    # check existance
    for file_ in files_to_check:
        if not file_.exists():
            subject_valid = False
            print(f"Missing file: {file_}")
    return subject_valid


def check_subject_images(subject_dir: Path, labels_dir: Path) -> Tuple[List[Path], List[Path]]:
    wrong_size = []
    wrong_spacing = []

    files_to_check = [
        subject_dir / f"{subject_dir.name}_brain_t1.nii.gz",
        subject_dir / f"{subject_dir.name}_brain_t1ce.nii.gz",
        subject_dir / f"{subject_dir.name}_brain_t2.nii.gz",
        subject_dir / f"{subject_dir.name}_brain_flair.nii.gz",
        labels_dir / f"{subject_dir.name}_final_seg.nii.gz",
    ]
    # check image properties
    BASE_SIZE = np.array([240, 240, 155])
    BASE_SPACING = np.array([1.0, 1.0, 1.0])
    for file_ in files_to_check:
        image = sitk.ReadImage(str(file_))
        size_array = np.array(image.GetSize())
        spacing_array = np.array(image.GetSpacing())

        if not (BASE_SIZE == size_array).all():
            wrong_size.append(file_)
        if not (BASE_SPACING == spacing_array).all():
            wrong_spacing.append(file_)
    return wrong_size, wrong_spacing


def run_sanity_check(data_path: str, labels_path: str):
    for curr_subject_dir in Path(data_path).iterdir():
        if curr_subject_dir.is_dir():
            assert check_subject_validity(
                curr_subject_dir, Path(labels_path)
            ), f"Subject {curr_subject_dir.name} does not contain all modalities or segmentation."
            wrong_size, wrong_spacing = check_subject_images(curr_subject_dir, Path(labels_path))
            assert len(wrong_size) == 0, (
                f"Image size is not [240,240,155] for {wrong_size}"
            )
            assert len(wrong_spacing) == 0, (
                f"Image resolution is not [1,1,1] for {wrong_spacing}"
            )
    print("Finished")
