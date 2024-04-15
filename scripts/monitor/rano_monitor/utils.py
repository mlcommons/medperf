import hashlib
import re
import os
import shutil
import tarfile
from pathlib import Path
from subprocess import DEVNULL, Popen

import pandas as pd
import yaml
from rano_monitor.constants import (
    REVIEW_COMMAND,
    BRAINMASK_BAK,
    DEFAULT_SEGMENTATION,
    BRAINMASK,
    MANUAL_REVIEW_STAGE,
    DONE_STAGE,
    REVIEW_FILENAME,
    REVIEWED_PATTERN,
    UNDER_REVIEW_PATTERN,
    BRAINMASK_PATTERN,
)


def is_editor_installed():
    review_command_path = shutil.which(REVIEW_COMMAND)
    return review_command_path is not None


def get_hash(filepath: str):
    with open(filepath, "rb") as f:
        contents = f.read()
        file_hash = hashlib.md5(contents).hexdigest()
    return file_hash


def run_editor(t1c, flair, t2, t1, seg, label, cmd=REVIEW_COMMAND):
    review_cmd = "{cmd} -g {t1c} -o {flair} {t2} {t1} -s {seg} -l {label}"
    review_cmd = review_cmd.format(
        cmd=REVIEW_COMMAND,
        t1c=t1c,
        flair=flair,
        t2=t2,
        t1=t1,
        seg=seg,
        label=label,
    )
    Popen(review_cmd.split(), shell=False, stdout=DEVNULL, stderr=DEVNULL)


def review_tumor(subject: str, data_path: str, labels_path: str):
    (
        t1c_file,
        t1n_file,
        t2f_file,
        t2w_file,
        label_file,
        seg_file,
        under_review_file,
    ) = get_tumor_review_paths(subject, data_path, labels_path)

    is_nifti = labels_path.endswith(".nii.gz")
    is_under_review = os.path.exists(under_review_file)

    if not is_nifti and not is_under_review:
        shutil.copyfile(seg_file, under_review_file)

    run_editor(t1c_file, t2f_file, t2w_file, t1n_file, under_review_file, label_file)


def review_brain(subject, labels_path, data_path=None):
    (
        t1c_file,
        t1n_file,
        t2f_file,
        t2w_file,
        label_file,
        seg_file,
    ) = get_brain_review_paths(subject, labels_path, data_path=data_path)

    backup_path = os.path.join(os.path.dirname(seg_file), BRAINMASK_BAK)
    if not os.path.exists(backup_path):
        shutil.copyfile(seg_file, backup_path)

    run_editor(t1c_file, t2f_file, t2w_file, t1n_file, seg_file, label_file)


def finalize(subject: str, labels_path: str):
    id, tp = subject.split("|")
    filename = f"{id}_{tp}_{DEFAULT_SEGMENTATION}"
    under_review_filepath = os.path.join(
        labels_path,
        "under_review",
        filename,
    )
    finalized_filepath = os.path.join(labels_path, "finalized", filename)
    shutil.copyfile(under_review_filepath, finalized_filepath)


def get_tumor_review_paths(subject: str, data_path: str, labels_path: str):
    id, tp = subject.split("|")
    filepath = os.path.dirname(__file__)
    t1c_file = os.path.join(data_path, f"{id}_{tp}_brain_t1c.nii.gz")
    t1n_file = os.path.join(data_path, f"{id}_{tp}_brain_t1n.nii.gz")
    t2f_file = os.path.join(data_path, f"{id}_{tp}_brain_t2f.nii.gz")
    t2w_file = os.path.join(data_path, f"{id}_{tp}_brain_t2w.nii.gz")
    label_file = os.path.join(filepath, "assets/postop_gbm.label")

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
    if BRAINMASK not in os.listdir(labels_path):
        labels_path = os.path.join(labels_path, "..")
    seg_filename = BRAINMASK
    seg_file = os.path.join(labels_path, seg_filename)

    return seg_file


def get_brain_review_paths(subject: str, labels_path, data_path: str = None):
    seg_file = get_brain_path(labels_path)
    if data_path is None:
        data_path = os.path.join(os.path.dirname(seg_file), "reoriented")
    id, tp = subject.split("|")
    filepath = os.path.dirname(__file__)
    t1c_file = os.path.join(data_path, f"{id}_{tp}_t1c.nii.gz")
    t1n_file = os.path.join(data_path, f"{id}_{tp}_t1.nii.gz")
    t2f_file = os.path.join(data_path, f"{id}_{tp}_t2f.nii.gz")
    t2w_file = os.path.join(data_path, f"{id}_{tp}_t2w.nii.gz")
    label_file = os.path.join(filepath, "assets/brainmask.label")

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
            data_path = to_local_path(row["data_path"], dset_path)
            labels_path = to_local_path(row["labels_path"], dset_path)
            brainscans = get_tumor_review_paths(row.name, data_path, labels_path)[:-2]
            rawscans = get_brain_review_paths(row.name, labels_path)[:-1]
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


def get_tar_identified_masks(file):
    identified_reviewed = []
    identified_under_review = []
    identified_brainmasks = []
    try:
        with tarfile.open(file, "r") as tar:
            for member in tar.getmembers():
                review_match = re.match(REVIEWED_PATTERN, member.name)
                if review_match:
                    identified_reviewed.append(review_match)

                under_review_match = re.match(UNDER_REVIEW_PATTERN, member.name)
                if under_review_match:
                    identified_under_review.append(under_review_match)

                brainmask_match = re.match(BRAINMASK_PATTERN, member.name)
                if brainmask_match:
                    identified_brainmasks.append(brainmask_match)
    except Exception:
        return [], [], []

    return identified_reviewed, identified_under_review, identified_brainmasks


def get_identified_extract_paths(
    identified_reviewed, identified_under_review, identified_brainmasks, dset_data_path
):
    extracts = []
    for reviewed in identified_reviewed:
        id, tp, filename = reviewed.groups()
        src_path = reviewed.group(0)
        dest_path = os.path.join(
            dset_data_path,
            "tumor_extracted",
            "DataForQC",
            id,
            tp,
            "TumorMasksForQC",
            "finalized",
        )

        # dest_path = os.path.join(dest_path, filename)
        extracts.append((src_path, dest_path))

    for under_review in identified_under_review:
        id, tp, filename = under_review.groups()
        src_path = under_review.group(0)
        dest_path = os.path.join(
            dset_data_path,
            "tumor_extracted",
            "DataForQC",
            id,
            tp,
            "TumorMasksForQC",
            "under_review",
        )

        # dest_path = os.path.join(dest_path, filename)
        extracts.append((src_path, dest_path))

    for mask in identified_brainmasks:
        id, tp = mask.groups()
        src_path = mask.group(0)
        dest_path = os.path.join(
            dset_data_path,
            "tumor_extracted",
            "DataForQC",
            id,
            tp,
        )
        extracts.append((src_path, dest_path))

    return extracts


def unpackage_reviews(file, app, dset_data_path):
    identified_masks = get_tar_identified_masks(file)
    identified_reviewed, identified_under_review, identified_brainmasks = (
        identified_masks
    )

    if len(identified_reviewed):
        app.notify("Reviewed cases identified")

    if len(identified_brainmasks):
        app.notify("Brain masks identified")

    extracts = get_identified_extract_paths(
        identified_reviewed,
        identified_under_review,
        identified_brainmasks,
        dset_data_path,
    )

    with tarfile.open(file, "r") as tar:
        for src, dest in extracts:
            member = tar.getmember(src)
            member.name = os.path.basename(member.name)
            target_file = os.path.join(dest, member.name)
            # TODO: this might be problematic UX.
            # The brainmask might get overwritten unknowingly
            if os.path.exists(target_file):
                delete(target_file, dset_data_path)
            tar.extract(member, dest)
