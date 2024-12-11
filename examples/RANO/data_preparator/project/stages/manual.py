from typing import Union, Tuple
import pandas as pd
import os
import shutil

from .row_stage import RowStage
from .constants import TUMOR_MASK_FOLDER, INTERIM_FOLDER, FINAL_FOLDER
from .mlcube_constants import MANUAL_STAGE_STATUS
from .utils import (
    get_id_tp,
    update_row_with_dict,
    set_files_read_only,
    copy_files,
    md5_file,
)


class ManualStage(RowStage):
    def __init__(
        self, data_csv: str, out_path: str, prev_stage_path: str, backup_path: str
    ):
        self.data_csv = data_csv
        self.out_path = out_path
        self.prev_stage_path = prev_stage_path
        self.backup_path = backup_path
        self.rollback_path = os.path.join(os.path.dirname(out_path), "prepared")
        self.brain_mask_file = "brainMask_fused.nii.gz"

    @property
    def name(self):
        return "Manual review"

    @property
    def status_code(self) -> int:
        return MANUAL_STAGE_STATUS

    def __get_input_paths(self, index: Union[str, int]):
        id, tp = get_id_tp(index)
        tumor_mask_path = os.path.join(
            self.prev_stage_path, INTERIM_FOLDER, id, tp, TUMOR_MASK_FOLDER
        )
        brain_mask_path = os.path.join(
            self.prev_stage_path, INTERIM_FOLDER, id, tp, self.brain_mask_file
        )
        return tumor_mask_path, brain_mask_path

    def __get_under_review_path(self, index: Union[str, int]):
        id, tp = get_id_tp(index)
        path = os.path.join(
            self.out_path, INTERIM_FOLDER, id, tp, TUMOR_MASK_FOLDER, "under_review"
        )
        return path

    def __get_output_path(self, index: Union[str, int]):
        id, tp = get_id_tp(index)
        path = os.path.join(
            self.out_path, INTERIM_FOLDER, id, tp, TUMOR_MASK_FOLDER, "finalized"
        )
        return path

    def __get_backup_path(self, index: Union[str, int]):
        id, tp = get_id_tp(index)
        path = os.path.join(self.backup_path, id, tp, TUMOR_MASK_FOLDER)
        return path

    def __get_rollback_paths(self, index: Union[str, int]):
        id, tp = get_id_tp(index)
        data_path = os.path.join(self.rollback_path, FINAL_FOLDER, id, tp)
        labels_path = os.path.join(self.rollback_path, INTERIM_FOLDER, id, tp)
        return data_path, labels_path

    def __report_success(
        self, index: Union[str, int], report: pd.DataFrame
    ) -> pd.DataFrame:
        labels_path = self.__get_output_path(index)
        data_path = report.loc[index, "data_path"]
        report_data = {
            "status": 5,
            "data_path": data_path,
            "labels_path": labels_path,
        }
        update_row_with_dict(report, report_data, index)
        return report

    def __report_step_missing(
        self, index: Union[str, int], report: pd.DataFrame
    ) -> pd.DataFrame:
        in_path, _ = self.__get_input_paths(index)
        data_path = report.loc[index, "data_path"]

        report_data = {
            "status": -self.status_code,
            "data_path": data_path,
            "labels_path": in_path,
        }
        update_row_with_dict(report, report_data, index)
        return report

    def __report_multiple_cases_error(
        self, index: Union[str, int], report: pd.DataFrame, cases: list
    ) -> pd.DataFrame:
        path = self.__get_output_path(index)
        data_path = report.loc[index, "data_path"]

        report_data = {
            "status": -self.status_code - 0.1,  # -5.1
            "data_path": data_path,
            "labels_path": path,
            "comment": f"Multiple files were identified in the labels path: {cases}. " \
            + "Please ensure that there is only the manually corrected segmentation file."
        }
        update_row_with_dict(report, report_data, index)
        return report

    def __rollback(self, index):
        # Unhide the rollback paths
        rollback_paths = self.__get_rollback_paths(index)
        for rollback_path in rollback_paths:
            rollback_dirname = os.path.dirname(rollback_path)
            rollback_basename = os.path.basename(rollback_path)
            hidden_rollback_path = os.path.join(
                rollback_dirname, f".{rollback_basename}"
            )

            if os.path.exists(hidden_rollback_path):
                shutil.move(hidden_rollback_path, rollback_path)

        # Move the modified brain mask to the rollback path
        _, rollback_labels_path = rollback_paths
        tumor_masks_path, brain_mask_path = self.__get_input_paths(index)
        rollback_brain_mask_path = os.path.join(
            rollback_labels_path, self.brain_mask_file
        )
        if os.path.exists(rollback_brain_mask_path):
            os.remove(rollback_brain_mask_path)
        shutil.move(brain_mask_path, rollback_brain_mask_path)

        # Remove the complete subject path
        subject_path = os.path.abspath(os.path.join(tumor_masks_path, ".."))

        shutil.rmtree(subject_path)

    def __report_rollback(
        self, index: Union[str, int], report: pd.DataFrame, mask_hash
    ) -> pd.DataFrame:
        rollback_fets_path, rollback_qc_path = self.__get_rollback_paths(index)

        report_data = {
            "status": 2,  # Move back to nifti transform finished
            "data_path": rollback_qc_path,
            "labels_path": rollback_fets_path,
            "brain_mask_hash": mask_hash,
            "num_changed_voxels": 0.0,  # Ensure voxel count is reset
            "segmentation_hash": "",
        }
        update_row_with_dict(report, report_data, index)
        return report

    def could_run(self, index: Union[str, int], report: pd.DataFrame) -> bool:
        print(f"Checking if {self.name} can run")
        out_path = self.__get_output_path(index)
        cases = []
        if os.path.exists(out_path):
            cases = os.listdir(out_path)

        in_path, brain_path = self.__get_input_paths(index)
        brain_mask_hash = ""
        if os.path.exists(brain_path):
            brain_mask_hash = md5_file(brain_path)
        expected_brain_mask_hash = report.loc[index, "brain_mask_hash"]

        segmentation_exists = os.path.exists(in_path)
        annotation_exists = len(cases) == 1
        brain_mask_changed = brain_mask_hash != expected_brain_mask_hash
        print(f"{segmentation_exists=} and (not {annotation_exists=} or {brain_mask_changed=})")
        return segmentation_exists and (not annotation_exists or brain_mask_changed)

    def execute(
        self, index: Union[str, int], report: pd.DataFrame
    ) -> Tuple[pd.DataFrame, bool]:
        """Manual steps are by definition not doable by an algorithm. Therefore,
        execution of this step leads to a failed stage message, indicating that
        the manual step has not been done.

        Args:
            index (Union[str, int]): current case index
            report (pd.DataFrame): data preparation report

        Returns:
            pd.DataFrame: _description_
        """

        # Generate a hidden copy of the baseline segmentations
        in_path, brain_path = self.__get_input_paths(index)
        out_path = self.__get_output_path(index)
        under_review_path = self.__get_under_review_path(index)
        bak_path = self.__get_backup_path(index)
        if not os.path.exists(bak_path):
            copy_files(in_path, bak_path)
            set_files_read_only(bak_path)
        os.makedirs(under_review_path, exist_ok=True)
        os.makedirs(out_path, exist_ok=True)

        cases = os.listdir(out_path)

        brain_mask_hash = ""
        if os.path.exists(brain_path):
            brain_mask_hash = md5_file(brain_path)
        expected_brain_mask_hash = report.loc[index, "brain_mask_hash"]
        brain_mask_changed = brain_mask_hash != expected_brain_mask_hash

        if brain_mask_changed:
            # Found brain mask changed
            self.__rollback(index)
            # Label this as able to continue
            return self.__report_rollback(index, report, brain_mask_hash), True

        if len(cases) > 1:
            # Found more than one reviewed case
            return self.__report_multiple_cases_error(index, report, cases), False
        elif not len(cases):
            # Found no cases yet reviewed
            return self.__report_step_missing(index, report), False
        return self.__report_success(index, report), True
