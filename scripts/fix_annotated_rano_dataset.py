import os
import shutil
from medperf import config
from medperf.init import initialize
from typer import Option, Typer, run

app = Typer()

def main(
        dataset_uid: str = Option(..., "-d", "--dataset"),
):
    initialize()
    dset_path = os.path.join(config.datasets_folder, dataset_uid)
    annots_path = os.path.join(dset_path, "data/tumor_extracted/DataForQC")
    nnunet_backups_path = os.path.join(dset_path, "labels/.tumor_segmentation_backup")
    subject_ids = os.listdir(annots_path)
    subject_ids = [id for id in subject_ids if not id.startswith(".")]

    corrected_count = 0

    for subject_id in subject_ids:
        subject_path = os.path.join(annots_path, subject_id)
        timepoints = os.listdir(subject_path)
        timepoints = [tp for tp in timepoints if not tp.startswith(".")]

        for timepoint in timepoints:
            timepoint_path = os.path.join(subject_path, timepoint)
            tumor_mask_path = os.path.join(timepoint_path, "TumorMasksForQC")
            nnunet_backup_path = os.path.join(nnunet_backups_path, subject_id, timepoint)

            mask_file = f"{subject_id}_{timepoint}_tumorMask_model_0.nii.gz"
            backup_file = f".{mask_file}.bak"
            finalized_backup_file = f".{mask_file}.in_finalized_folder.bak"

            # 1) Verify if a backup of the previously reviewed file exists. If it does
            # we can assume the fix has been applied
            backup_path = os.path.join(tumor_mask_path, backup_file)
            if os.path.exists(backup_path):
                # Do nothing. Fix was already applied
                continue

            # 2) Verify if the case has been reviewed or is under review
            under_review_path = os.path.join(tumor_mask_path, "under_review", mask_file)
            finalized_path = os.path.join(tumor_mask_path, "finalized", mask_file)
            is_under_review  = os.path.exists(under_review_path)
            is_finalized = os.path.exists(finalized_path)

            # 3) Create backup of original file. This is the file that, due to the bug, contains the annotations
            backup_path = os.path.join(tumor_mask_path, backup_file)
            mask_path = os.path.join(tumor_mask_path, mask_file)
            shutil.copy(mask_path, backup_path)


            # 4) Move the reviewed file to the under_review and finalized locations. Create backup before
            finalized_backup_path = os.path.join(tumor_mask_path, finalized_backup_file)

            if is_finalized:
                shutil.copy(finalized_path, finalized_backup_path)
                os.remove(finalized_path)
                shutil.copy(mask_path, finalized_path)

            if is_under_review:
                os.remove(under_review_path)
                shutil.copy(mask_path, under_review_path)

            # 5) Copy the backup segmentation to the original segmentation location
            if is_finalized or is_under_review:
                # Only need to run this if the case was affected by the bug
                orig_backup_path = os.path.join(nnunet_backup_path, "TumorMasksForQC", mask_file)

                os.remove(mask_path)
                shutil.copy(orig_backup_path, mask_path)

                corrected_count += 1

    print(f"Corrected {corrected_count} cases")

if __name__ == "__main__":
    run(main)