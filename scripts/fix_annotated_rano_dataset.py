
import re
import os
import tarfile
from medperf import config
from medperf.init import initialize
from typer import Option, Typer, run

app = Typer()

REVIEWED_PATTERN = r".*?\/([^\/]*)\/(((?!finalized|under_review).)*)\/(((?!finalized|under_review).)*_tumorMask_model_0\.nii\.gz)"


def main(
        dataset_uid: str = Option(None, "-d", "--dataset"),
):
    initialize()
    dset_path = os.path.join(config.datasets_folder, dataset_uid)
    annots_path = os.path.join(dset_path, "data/tumor_extracted/DataForQC")
    subject_ids = os.listdir(annots_path)
    subject_ids = [id for id in subject_ids if not id.startswith(".")]

    for subject_id in subject_ids:
        subject_path = os.path.join(annots_path, subject_id)
        timepoints = os.listdir(subject_path)
        timepoints = [tp for tp in timepoints if not tp.startswith(".")]

        for timepoint in timepoints:
            timepoint_path = os.path.join(subject_path, timepoint)
            tumor_mask_path = os.path.join(timepoint_path, "TumorMasksForQC")
            reviewed_file = f"{subject_id}_{timepoint}_tumorMask_model_0.nii.gz"

            # 1) Check hashes with the backed up segmentation

            # 2) Move the reviewed file to the under_review and finalized locations


            # 3) Copy the backup segmentation to the original segmentation location

if __name__ == "__main__":
    run(main)