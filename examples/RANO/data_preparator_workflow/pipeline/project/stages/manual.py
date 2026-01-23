from typing import Union, Tuple
import pandas as pd
import os
import shutil
import json
from .row_stage import RowStage
from .constants import INTERIM_FOLDER, FINAL_FOLDER
from .env_vars import DATA_DIR
from .mlcube_constants import (
    MANUAL_STAGE_STATUS,
    BRAIN_MASK_CHANGED_FILE,
    PREP_PATH,
    BRAIN_MASK_REVIEW_PATH,
    TUMOR_EXTRACTION_REVIEW_PATH,
    BRAIN_MASK_FILE,
    GROUND_TRUTH_PATH,
)
from .utils import (
    get_id_tp,
    set_files_read_only,
    copy_files,
    get_manual_approval_finalized_path,
    get_manual_approval_base_path,
    delete_empty_directory,
)


class ManualStage(RowStage):
    def __init__(
        self,
        data_csv: str,
        out_path: str,
        prev_stage_path: str,
        backup_path: str,
    ):
        self.data_csv = data_csv
        self.out_path = out_path
        self.prev_stage_path = prev_stage_path
        self.backup_path = backup_path

    @property
    def name(self):
        return "Manual review"

    @property
    def status_code(self) -> int:
        return MANUAL_STAGE_STATUS

    def __get_input_paths(self, index: Union[str, int]):
        id, tp = get_id_tp(index)
        print(f"{self.prev_stage_path=}")
        tumor_mask_path = os.path.join(
            self.prev_stage_path, INTERIM_FOLDER, id, tp, GROUND_TRUTH_PATH
        )
        brain_mask_dir = get_manual_approval_finalized_path(
            id, tp, BRAIN_MASK_REVIEW_PATH
        )
        brain_mask_path = os.path.join(brain_mask_dir, BRAIN_MASK_FILE)
        return tumor_mask_path, brain_mask_path

    def __get_output_path(self, index: Union[str, int]):
        id, tp = get_id_tp(index)
        path = get_manual_approval_finalized_path(id, tp, TUMOR_EXTRACTION_REVIEW_PATH)
        return path

    def __get_backup_path(self, index: Union[str, int]):
        id, tp = get_id_tp(index)
        path = os.path.join(self.backup_path, id, tp, GROUND_TRUTH_PATH)
        return path

    def __get_rollback_paths(self, index: Union[str, int]):
        id, tp = get_id_tp(index)
        base_rollback_path = os.path.join(DATA_DIR, PREP_PATH, id, tp)
        data_path = os.path.join(base_rollback_path, FINAL_FOLDER, id, tp)
        labels_path = os.path.join(base_rollback_path, INTERIM_FOLDER, id, tp)
        return data_path, labels_path

    def rollback(self, index):
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
        rollback_brain_mask_path = os.path.join(rollback_labels_path, BRAIN_MASK_FILE)
        if os.path.exists(rollback_brain_mask_path):
            os.remove(rollback_brain_mask_path)
        shutil.move(brain_mask_path, rollback_brain_mask_path)

        # Remove the complete subject path
        subject_path = os.path.abspath(
            os.path.join(tumor_masks_path, "..", "..", "..", "..")
        )

        shutil.rmtree(subject_path)

        # Also remove the manual review directory for this subject/timepoint
        id, tp = get_id_tp(index)
        for approval_type in [TUMOR_EXTRACTION_REVIEW_PATH, BRAIN_MASK_REVIEW_PATH]:
            manual_review_path = get_manual_approval_base_path(id, tp, approval_type)
            shutil.rmtree(manual_review_path)
            subject_review_path = os.path.abspath(
                os.path.join(manual_review_path, "..")
            )
            delete_empty_directory(subject_review_path)

    def prepare_directories(self, index: Union[str, int]) -> Tuple[str, str]:
        # Generate a hidden copy of the baseline segmentations
        in_path, brain_path = self.__get_input_paths(index)
        out_path = self.__get_output_path(index)
        bak_path = self.__get_backup_path(index)
        print(f"{in_path=}")
        print(f"{out_path=}")
        print(f"{bak_path=}")
        if not os.path.exists(bak_path) or not os.listdir(bak_path):
            print("Entered if")
            copy_files(in_path, bak_path)
            set_files_read_only(bak_path)

        return out_path, brain_path

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
        print(
            f"{segmentation_exists=} and (not {annotation_exists=} or {brain_mask_changed=})"
        )
        return segmentation_exists and (not annotation_exists or brain_mask_changed)

    def execute(
        self, index: Union[str, int], report: pd.DataFrame = None
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
        out_path, brain_path = self.prepare_directories(index)

        if report is None:
            report = load_report()
        brain_mask_changed, brain_mask_hash = self.check_brain_mask_changed(
            index, brain_path, report
        )

        if brain_mask_changed:
            # Found brain mask changed
            self.rollback(index)
            # Label this as able to continue
            return self.__report_rollback(index, report, brain_mask_hash), True

        return self.check_finalized_cases(index, report, out_path)
