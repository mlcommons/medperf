import re
import shutil
import os
import tarfile
from typer import Option, Typer, run

app = Typer()

EXTRACT_PATH = ".tmp_reviewed"
FIXED_TARBALL_NAME = "fixed_reviewed_cases.tar.gz"


def main(
        tarball_path: str = Option(..., "-t", "--tarball")
):

    # Extract cases
    with tarfile.open(tarball_path, 'r:gz') as tar:
        tar.extractall(path=EXTRACT_PATH)

    reviewed_path = os.path.join(EXTRACT_PATH, "review_cases")

    subject_ids = os.listdir(reviewed_path)
    subject_ids = [s_id for s_id in subject_ids if not s_id.startswith(".")]

    for subject_id in subject_ids:
        subject_path = os.path.join(reviewed_path, subject_id)
        timepoints = os.listdir(subject_path)
        timepoints = [tp for tp in timepoints if not tp.startswith(".")]

        for timepoint in timepoints:
            timepoint_path = os.path.join(subject_path, timepoint)

            mask_filename = f"{subject_id}_{timepoint}_tumorMask_model_0.nii.gz"
            mask_backup_filename = f".{mask_filename}.bak"
            mask_finalized_backup_filename = f".{mask_filename}.in_finalized.bak"

            mask_path = os.path.join(timepoint_path, mask_filename)
            under_review_path = os.path.join(timepoint_path, "under_review", mask_filename)
            finalized_path = os.path.join(timepoint_path, "finalized", mask_filename)

            is_under_review = os.path.exists(under_review_path)
            is_finalized = os.path.exists(finalized_path)

            mask_backup_path = os.path.join(timepoint_path, mask_backup_filename)
            shutil.copy(mask_path, mask_backup_path)

            finalized_backup_path = os.path.join(timepoint_path, mask_finalized_backup_filename)

            if is_under_review:
                # First backup this one in case there's no finalized
                shutil.copy(under_review_path, finalized_backup_path)
                os.remove(under_review_path)
                shutil.copy(mask_path, under_review_path)

            if is_finalized:
                # Overwrite under_review backup with this one if it exists
                shutil.copy(finalized_path, finalized_backup_path)
                os.remove(finalized_path)
                shutil.copy(mask_path, finalized_path)

            if is_finalized or is_under_review:
                # Use the file that was finalized or under_review
                # to recover the original mask_path
                os.remove(mask_path)
                shutil.copy(finalized_backup_path, mask_path)

    # Package fixed contents to a new tarball
    with tarfile.open(FIXED_TARBALL_NAME, "w:gz") as tar:
        tar.add(reviewed_path, arcname=os.path.basename(reviewed_path))

    # Delete temporary folder
    shutil.rmtree(EXTRACT_PATH)


if __name__ == "__main__":
    run(main)