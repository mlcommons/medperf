import pandas as pd
import os
import yaml
import shutil
import tarfile
from pathlib import Path
from rano_monitor.constants import *

def get_tumor_review_paths(subject: pd.Series, dset_path: str):
    data_path = to_local_path(subject["data_path"], dset_path)
    labels_path = to_local_path(subject["labels_path"], dset_path)

    id, tp = subject.name.split("|")
    t1c_file = os.path.join(data_path, f"{id}_{tp}_brain_t1c.nii.gz")
    t1n_file = os.path.join(data_path, f"{id}_{tp}_brain_t1n.nii.gz")
    t2f_file = os.path.join(data_path, f"{id}_{tp}_brain_t2f.nii.gz")
    t2w_file = os.path.join(data_path, f"{id}_{tp}_brain_t2w.nii.gz")
    label_file = os.path.join(os.path.dirname(__file__), "assets/postop_gbm.label")

    if labels_path.endswith(".nii.gz"):
        seg_filename = os.path.basename(labels_path)
        seg_file = labels_path
        under_review_file = labels_path
    else:
        seg_filename = f"{id}_{tp}_{DEFAULT_SEGMENTATION}"
        seg_file = os.path.join(labels_path, seg_filename)
        under_review_file = os.path.join(
            labels_path,
            "under_review",
            seg_filename,
        )
    return (
        t1c_file,
        t1n_file,
        t2f_file,
        t2w_file,
        label_file,
        seg_file,
        under_review_file,
    )


def get_brain_path(labels_path: str):
    if labels_path.endswith(".nii.gz"):
        # We are past manual review, transform the path as necessary
        labels_path = os.path.dirname(labels_path)
        labels_path = os.path.join(labels_path, "..")
    labels_path = os.path.join(labels_path, "..")
    seg_filename = BRAINMASK
    seg_file = os.path.join(labels_path, seg_filename)

    return seg_file


def get_brain_review_paths(subject: pd.Series, dset_path: str):
    labels_path = to_local_path(subject["labels_path"], dset_path)
    seg_file = get_brain_path(labels_path)
    data_path = os.path.join(os.path.dirname(seg_file), "reoriented")
    id, tp = subject.name.split("|")
    t1c_file = os.path.join(data_path, f"{id}_{tp}_t1c.nii.gz")
    t1n_file = os.path.join(data_path, f"{id}_{tp}_t1.nii.gz")
    t2f_file = os.path.join(data_path, f"{id}_{tp}_t2f.nii.gz")
    t2w_file = os.path.join(data_path, f"{id}_{tp}_t2w.nii.gz")
    label_file = os.path.join(os.path.dirname(__file__), "assets/brainmask.label")

    return t1c_file, t1n_file, t2f_file, t2w_file, label_file, seg_file


def generate_full_report(report_dict: dict, stages_path: str):
    with open(stages_path, "r") as f:
        stages = yaml.safe_load(f)

    report_keys = ["comment", "status_name", "docs_url", "status"]
    for key in report_keys:
        if key not in report_dict:
            report_dict[key] = {}

    for case, status in report_dict["status"].items():
        stage = stages[status]
        for key, val in stage.items():
            # First make sure to populate the stage key for missing cases
            if case not in report_dict[key]:
                report_dict[key][case] = ""
            # Then, if the stage contains information for that key, add it
            if val is not None:
                report_dict[key][case] = val

    return report_dict


def delete(filepath: str, dset_path: str):
    try:
        os.remove(filepath)
        return
    except PermissionError:
        pass

    # Handle scenarios where user doesn't have permission to delete stuff
    # Instead, move the file-of-interest to a trash folder so that it can be
    # deleted by the MLCube, with proper permissions
    trash_path = os.path.join(dset_path, ".trash")
    os.makedirs(trash_path, exist_ok=True)
    num_trashfiles = len(os.listdir(trash_path))

    # Rename the file to the number of files. This is to avoid collisions
    target_filepath = os.path.join(trash_path, str(num_trashfiles))
    shutil.move(filepath, target_filepath)


def to_local_path(mlcube_path: str, local_parent_path: str):
    if not isinstance(mlcube_path, str):
        return mlcube_path
    mlcube_prefix = "mlcube_io"
    if len(mlcube_path) == 0:
        return ""

    if mlcube_path.startswith(os.path.sep):
        mlcube_path = mlcube_path[1:]

    if mlcube_path.startswith(mlcube_prefix):
        # normalize path
        mlcube_path = str(Path(*Path(mlcube_path).parts[2:]))

    local_parent_path = str(Path(local_parent_path))
    return os.path.normpath(os.path.join(local_parent_path, mlcube_path))


def package_review_cases(report: pd.DataFrame, dset_path: str):
    review_cases = report[
        (MANUAL_REVIEW_STAGE <= abs(report["status"]))
        & (abs(report["status"]) < DONE_STAGE)
    ]
    with tarfile.open(REVIEW_FILENAME, "w:gz") as tar:
        for i, row in review_cases.iterrows():
            brainscans = get_tumor_review_paths(row, dset_path)[:-2]
            rawscans = get_brain_review_paths(row, dset_path)[:-1]
            labels_path = to_local_path(row["labels_path"], dset_path)
            base_path = os.path.join(labels_path, "..")

            # Add tumor segmentations
            id, tp = row.name.split("|")
            tar_path = os.path.join("review_cases", id, tp)
            reviewed_path = os.path.join("review_cases", id, tp, "finalized")
            reviewed_dir = tarfile.TarInfo(name=reviewed_path)
            reviewed_dir.type = tarfile.DIRTYPE
            reviewed_dir.mode = 0o755
            tar.addfile(reviewed_dir)
            tar.add(labels_path, tar_path)

            brainscan_path = os.path.join("review_cases", id, tp, "brain_scans")
            for brainscan in brainscans:
                brainscan_target_path = os.path.join(
                    brainscan_path, os.path.basename(brainscan)
                )
                tar.add(brainscan, brainscan_target_path)

            # Add brain mask
            brain_mask_filename = "brainMask_fused.nii.gz"
            brain_mask_path = os.path.join(base_path, brain_mask_filename)
            brain_mask_tar_path = os.path.join(tar_path, brain_mask_filename)
            if os.path.exists(brain_mask_path):
                tar.add(brain_mask_path, brain_mask_tar_path)

            # Add raw scans
            rawscan_path = os.path.join("review_cases", id, tp, "raw_scans")
            for rawscan in rawscans:
                rawscan_target_path = os.path.join(
                    rawscan_path, os.path.basename(rawscan)
                )
                tar.add(rawscan, rawscan_target_path)

            # Add summary images
            for file in os.listdir(base_path):
                if not file.endswith(".png"):
                    continue
                img_path = os.path.join(base_path, file)
                img_tar_path = os.path.join(tar_path, file)
                tar.add(img_path, img_tar_path)

