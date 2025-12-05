from .dset_stage import DatasetStage
import pandas as pd
import numpy as np
import os
import re
import shutil
from typing import Tuple
from .utils import has_prepared_folder_structure, md5_dir, get_data_csv_filepath
from .constants import INTERIM_FOLDER, FINAL_FOLDER, TUMOR_MASK_FOLDER
from .mlcube_constants import SETUP_STAGE_STATUS, FINALIZED_PATH

DICOM_MODALITIES_PREFIX = {
    "fl": "t2_Flair",
    "t1": "t1_axial-3",
    "t1c": "t1_axial_stealth",
    "t2": "T2_SAG",
}
NIFTI_MODALITIES = ["t1c", "t1n", "t2f", "t2w"]
BRAIN_SCAN_NAME = "brain_(.*)"
TUMOR_SEG_NAME = "final_seg"
CSV_HEADERS = ["SubjectID", "Timepoint", "T1", "T1GD", "T2", "FLAIR"]


def get_index(subject, timepoint):
    return f"{subject}|{timepoint}"


def has_alternative_folder_structure(subject_tp_path, og_path):
    contents = os.listdir(subject_tp_path)
    prefixes_presence = {prefix: False for prefix in DICOM_MODALITIES_PREFIX.values()}
    for content in contents:
        content_path = os.path.join(subject_tp_path, content)
        # Search recursively across folders
        if os.path.isdir(content_path):
            return has_alternative_folder_structure(content_path, og_path)

        # Check if the file is a dicom file with an expected prefix
        if not content.endswith(".dcm"):
            continue

        for prefix in DICOM_MODALITIES_PREFIX.values():
            if content.startswith(prefix):
                prefixes_presence[prefix] = True

        # If all prefixes are found within the current path, then it has the folder structure
        if all(prefixes_presence.values()):
            return True, subject_tp_path

    # Structure not identified at this tree
    return False, og_path


def to_expected_folder_structure(subject_tp_path, contents_path):
    # Create the modality folders
    for modality in DICOM_MODALITIES_PREFIX.keys():
        modality_path = os.path.join(subject_tp_path, modality)
        os.mkdir(modality_path)

    # Move the dicoms to the needed location
    dicoms = os.listdir(contents_path)
    prefix2mod = {prefix: mod for mod, prefix in DICOM_MODALITIES_PREFIX.items()}
    for dicom in dicoms:
        for prefix in prefix2mod.keys():
            if not dicom.startswith(prefix):
                continue
            mod = prefix2mod[prefix]
            old_path = os.path.join(contents_path, dicom)
            new_path = os.path.join(subject_tp_path, mod, dicom)
            shutil.move(old_path, new_path)

    # Remove extra folders
    desired_folders = set(DICOM_MODALITIES_PREFIX.keys())
    found_folders = set(os.listdir(subject_tp_path))
    extra_folders = found_folders - desired_folders
    for folder in extra_folders:
        folder_path = os.path.join(subject_tp_path, folder)
        shutil.rmtree(folder_path)


def has_semiprepared_folder_structure(subject_tp_path, og_path, recursive=True):
    contents = os.listdir(subject_tp_path)
    suffixes_presence = {suffix: False for suffix in NIFTI_MODALITIES}
    for content in contents:
        content_path = os.path.join(subject_tp_path, content)
        if os.path.isdir(content_path):
            if recursive:
                return has_semiprepared_folder_structure(content_path, og_path)
            else:
                continue

        if not content.endswith(".nii.gz"):
            continue

        for suffix in NIFTI_MODALITIES:
            full_suffix = f"_brain_{suffix}.nii.gz"
            if content.endswith(full_suffix):
                suffixes_presence[suffix] = True

    if all(suffixes_presence.values()):
        return True, subject_tp_path

    return False, og_path


def get_timepoints(subject, subject_tp_path):
    contents = os.listdir(subject_tp_path)
    timepoints = set()
    for content in contents:
        content_path = os.path.join(subject_tp_path, subject)
        if os.path.isdir(content_path):
            # Assume any directory at this point represents a timepoint
            timepoints.add(content)
            continue

        pattern = re.compile(
            f"{subject}_(.*)_(?:{BRAIN_SCAN_NAME}|{TUMOR_SEG_NAME})\.nii\.gz"
        )
        result = pattern.search(content)
        timepoint = result.group(1)
        timepoints.add(timepoint)

    return list(timepoints)


def get_tumor_segmentation(subject, timepoint, subject_tp_path):
    contents = os.listdir(subject_tp_path)
    seg_file = f"{subject}_{timepoint}_{TUMOR_SEG_NAME}.nii.gz"
    if seg_file in contents:
        return seg_file
    return None


def move_brain_scans(subject, timepoint, in_subject_path, out_data_path):
    final_path = os.path.join(out_data_path, FINAL_FOLDER, subject, timepoint)
    os.makedirs(final_path, exist_ok=True)

    contents = os.listdir(in_subject_path)

    pattern = re.compile(f"{subject}_{timepoint}_{BRAIN_SCAN_NAME}\.nii\.gz")
    brain_scans = [content for content in contents if pattern.match(content)]

    for scan in brain_scans:
        in_scan = os.path.join(in_subject_path, scan)
        out_scan = os.path.join(final_path, scan)
        shutil.copyfile(in_scan, out_scan)


def move_tumor_segmentation(
    subject, timepoint, seg_file, in_subject_path, out_data_path, out_labels_path
):
    interim_path = os.path.join(out_data_path, INTERIM_FOLDER, subject, timepoint)
    os.makedirs(interim_path, exist_ok=True)

    in_seg_path = os.path.join(in_subject_path, seg_file)
    tumor_mask_path = os.path.join(interim_path, TUMOR_MASK_FOLDER)
    under_review_path = os.path.join(tumor_mask_path, "under_review")
    finalized_path = os.path.join(tumor_mask_path, FINALIZED_PATH)
    os.makedirs(under_review_path, exist_ok=True)
    os.makedirs(finalized_path, exist_ok=True)

    seg_root_path = os.path.join(tumor_mask_path, seg_file)
    seg_under_review_path = os.path.join(under_review_path, seg_file)
    seg_finalized_path = os.path.join(finalized_path, seg_file)
    shutil.copyfile(in_seg_path, seg_root_path)
    shutil.copyfile(in_seg_path, seg_under_review_path)
    shutil.copyfile(in_seg_path, seg_finalized_path)

    # Place the segmentation in the backup folder
    backup_path = os.path.join(out_labels_path, ".tumor_segmentation_backup")
    subject_tp_backup_path = os.path.join(
        backup_path, subject, timepoint, TUMOR_MASK_FOLDER
    )
    os.makedirs(subject_tp_backup_path, exist_ok=True)
    seg_backup_path = os.path.join(subject_tp_backup_path, seg_file)
    shutil.copyfile(in_seg_path, seg_backup_path)

    return in_seg_path, seg_finalized_path


def write_partial_csv(csv_path, subject, timepoint):
    # Used when cases are semi-prepared, in which case they
    # skip the formal csv creation
    if csv_path is None:
        csv_path = get_data_csv_filepath(os.path.join(subject, timepoint))

    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        df = pd.DataFrame(columns=CSV_HEADERS)

    row = pd.Series(index=CSV_HEADERS)
    row["SubjectID"] = subject
    row["Timepoint"] = timepoint
    row.name = get_index(subject, timepoint)
    row = row.fillna("")

    # Check for existence of this row
    row_search = df[(df["SubjectID"] == subject) & (df["Timepoint"] == timepoint)]
    if len(row_search) == 0:
        df = df.append(row)

    df.to_csv(csv_path, index=False)


class InitialSetup(DatasetStage):
    def __init__(
        self,
        data_csv: str,
        input_path: str,
        output_path: str,
        input_labels_path: str,
        output_labels_path,
        done_data_out_path: str,
        done_status: int,
        brain_data_out_path: str,
        brain_status: int,
        tumor_data_out_path: str,
        reviewed_status: int,
    ):
        self.data_csv = data_csv
        self.input_path = input_path
        self.output_path = output_path
        self.input_labels_path = input_labels_path
        self.output_labels_path = output_labels_path
        self.done_data_out_path = done_data_out_path
        self.done_status_code = done_status
        self.brain_data_out_path = brain_data_out_path
        self.brain_status = brain_status
        self.tumor_data_out_path = tumor_data_out_path
        self.reviewed_status = reviewed_status

    @property
    def name(self) -> str:
        return "Initial Setup"

    @property
    def status_code(self) -> int:
        return SETUP_STAGE_STATUS

    def _proceed_to_comparison(self, subject, timepoint, in_subject_path, report):
        index = get_index(subject, timepoint)
        final_path = os.path.join(
            self.tumor_data_out_path, FINAL_FOLDER, subject, timepoint
        )
        input_hash = md5_dir(in_subject_path)
        # Stop if the subject was already present and no input change has happened
        if index in report.index:
            if input_hash == report.loc[index]["input_hash"]:
                return report

        # Move brain scans to its expected location
        move_brain_scans(subject, timepoint, in_subject_path, self.tumor_data_out_path)

        # Move tumor segmentation to its expected location
        seg_file = f"{subject}_{timepoint}_{TUMOR_SEG_NAME}.nii.gz"
        _, seg_finalized_path = move_tumor_segmentation(
            subject,
            timepoint,
            seg_file,
            in_subject_path,
            self.tumor_data_out_path,
            self.output_labels_path,
        )

        # Update the report
        data = {
            "status": self.reviewed_status,
            "data_path": final_path,
            "labels_path": seg_finalized_path,
            "num_changed_voxels": np.nan,
            "brain_mask_hash": "",
            "segmentation_hash": "",
            "input_hash": input_hash,
        }

        subject_series = pd.Series(data)
        subject_series.name = index
        report = report.append(subject_series)

        write_partial_csv(self.data_csv, subject, timepoint)

        return report

    def _proceed_to_tumor_extraction(self, subject, timepoint, in_subject_path, report):
        index = get_index(subject, timepoint)
        input_hash = md5_dir(in_subject_path)
        # Stop if the subject was already present and no input change has happened
        if index in report.index:
            if input_hash == report.loc[index]["input_hash"]:
                return report
        final_path = os.path.join(
            self.brain_data_out_path, FINAL_FOLDER, subject, timepoint
        )
        labels_path = os.path.join(
            self.brain_data_out_path, INTERIM_FOLDER, subject, timepoint
        )
        os.makedirs(final_path, exist_ok=True)
        os.makedirs(labels_path, exist_ok=True)

        # Move brain scans to its expected location
        move_brain_scans(subject, timepoint, in_subject_path, self.brain_data_out_path)

        # Update the report
        data = {
            "status": self.brain_status,
            "data_path": final_path,
            "labels_path": labels_path,
            "num_changed_voxels": np.nan,
            "brain_mask_hash": "",
            "segmentation_hash": "",
            "input_hash": input_hash,
        }

        subject_series = pd.Series(data)
        subject_series.name = index
        report = report.append(subject_series)

        write_partial_csv(self.data_csv, subject, timepoint)

        return report

    def could_run(self, report: pd.DataFrame):
        return True

    def execute(self, report: pd.DataFrame) -> Tuple[pd.DataFrame, bool]:
        # Rewrite the report
        cols = [
            "status",
            "status_name",
            "comment",
            "data_path",
            "labels_path",
            "input_hash",
        ]
        print("Initializing report")
        if report is None:
            print("No previous report was identified. Creating a new one")
            report = pd.DataFrame(columns=cols)

        input_is_prepared = has_prepared_folder_structure(
            self.input_path, self.input_labels_path
        )
        if input_is_prepared:
            # If prepared, store data directly in the data folder
            print("Input data looks prepared already. Skipping preprocessing")
            self.output_path = self.done_data_out_path

        observed_cases = set()

        for subject in os.listdir(self.input_path):
            in_subject_path = os.path.join(self.input_path, subject)
            out_subject_path = os.path.join(self.output_path, subject)
            in_labels_subject_path = os.path.join(self.input_labels_path, subject)
            out_labels_subject_path = os.path.join(self.output_labels_path, subject)

            if not os.path.isdir(in_subject_path):
                continue

            has_semiprepared, _ = has_semiprepared_folder_structure(
                in_subject_path, in_subject_path, recursive=False
            )
            if has_semiprepared:
                timepoints = get_timepoints(subject, in_subject_path)
                for timepoint in timepoints:
                    index = get_index(subject, timepoint)
                    tumor_seg = get_tumor_segmentation(
                        subject, timepoint, in_subject_path
                    )
                    if tumor_seg is not None:
                        report = self._proceed_to_comparison(
                            subject, timepoint, in_subject_path, report
                        )
                    else:
                        report = self._proceed_to_tumor_extraction(
                            subject, timepoint, in_subject_path, report
                        )
                    observed_cases.add(index)
                    continue

            for timepoint in os.listdir(in_subject_path):
                in_tp_path = os.path.join(in_subject_path, timepoint)
                out_tp_path = os.path.join(out_subject_path, timepoint)
                in_labels_tp_path = os.path.join(in_labels_subject_path, timepoint)
                out_labels_tp_path = os.path.join(out_labels_subject_path, timepoint)

                if not os.path.isdir(in_tp_path):
                    continue

                input_hash = md5_dir(in_tp_path)

                index = get_index(subject, timepoint)

                # Keep track of the cases that were found on the input folder
                observed_cases.add(index)

                has_semiprepared, in_tp_path = has_semiprepared_folder_structure(
                    in_tp_path, in_tp_path, recursive=True
                )
                if has_semiprepared:
                    tumor_seg = get_tumor_segmentation(subject, timepoint, in_tp_path)
                    if tumor_seg is not None:
                        report = self._proceed_to_comparison(
                            subject, timepoint, in_tp_path, report
                        )
                    else:
                        report = self._proceed_to_tumor_extraction(
                            subject, timepoint, in_tp_path, report
                        )
                    continue

                if index in report.index:
                    # Case has already been identified, see if input hash is different
                    # or if status is corrupted
                    # if so, override the contents and restart the state for that case
                    case = report.loc[index]
                    has_not_changed = case["input_hash"] == input_hash
                    has_a_valid_status = not np.isnan(case["status"])
                    if has_not_changed and has_a_valid_status:
                        continue

                    print(
                        f"Case {index} has either changed ({not has_not_changed}) or has a corrupted status ({not has_a_valid_status}). Starting from scratch"
                    )

                    shutil.rmtree(out_tp_path, ignore_errors=True)
                    shutil.copytree(in_tp_path, out_tp_path)
                    report = report.drop(index)
                else:
                    # New case not identified by the report. Add it
                    print(f"New case identified: {index}. Adding to report")
                    shutil.rmtree(out_tp_path, ignore_errors=True)
                    shutil.copytree(in_tp_path, out_tp_path)

                data = {
                    "status": self.status_code,
                    "data_path": out_tp_path,
                    "labels_path": "",
                    "num_changed_voxels": np.nan,
                    "brain_mask_hash": "",
                    "segmentation_hash": "",
                    "input_hash": input_hash,
                }

                has_alternative, contents_path = has_alternative_folder_structure(
                    out_tp_path, out_tp_path
                )
                if has_alternative:
                    # Move files around so it has the expected structure
                    to_expected_folder_structure(out_tp_path, contents_path)

                if input_is_prepared:
                    data["status_code"] = self.done_status_code
                    shutil.rmtree(out_labels_tp_path, ignore_errors=True)
                    shutil.copytree(in_labels_tp_path, out_labels_tp_path)

                subject_series = pd.Series(data)
                subject_series.name = index
                report = report.append(subject_series)

        reported_cases = set(report.index)
        removed_cases = reported_cases - observed_cases

        # Stop reporting removed cases
        for case_index in removed_cases:
            report = report.drop(case_index)

        report = report.sort_index()
        return report
