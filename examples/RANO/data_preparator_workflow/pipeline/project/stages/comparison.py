from typing import Union, Tuple
import os

import pandas as pd
from pandas import DataFrame
import numpy as np
import nibabel as nib

from .row_stage import RowStage
from .utils import (
    get_id_tp,
    get_changed_voxels_file,
    md5_file,
    get_manual_approval_finalized_path,
)
from .constants import INTERIM_FOLDER
from .mlcube_constants import (
    COMPARISON_STAGE_STATUS,
    GROUND_TRUTH_PATH,
    TUMOR_EXTRACTION_REVIEW_PATH,
    TUMOR_PATH,
)
from .env_vars import DATA_DIR


class SegmentationComparisonStage(RowStage):
    def __init__(
        self,
        data_csv: str,
        out_path: str,
        prev_stage_path,
        backup_path: str,
    ):
        self.data_csv = data_csv
        self.out_path = out_path
        self.prev_stage_path = prev_stage_path
        self.backup_path = backup_path

    @property
    def name(self):
        return "Label Segmentation Comparison"

    @property
    def status_code(self):
        return COMPARISON_STAGE_STATUS

    def __get_input_path(self, index: Union[str, int]) -> str:
        id, tp = get_id_tp(index)
        path = get_manual_approval_finalized_path(id, tp, TUMOR_EXTRACTION_REVIEW_PATH)
        return path

    def __get_backup_path(self, index: Union[str, int]) -> str:
        id, tp = get_id_tp(index)
        path = os.path.join(
            DATA_DIR, TUMOR_PATH, id, tp, INTERIM_FOLDER, id, tp, GROUND_TRUTH_PATH
        )
        return path

    def __get_output_path(self, index: Union[str, int]) -> str:
        id, tp = get_id_tp(index)
        path = os.path.join(self.out_path, id, tp)
        return path

    def __get_case_path(self, index: Union[str, int]) -> str:
        path = self.__get_input_path(index)
        case = os.listdir(path)[0]

        return os.path.join(path, case)

    def __report_gt_not_found(
        self, index: Union[str, int], report: pd.DataFrame, reviewed_hash: str
    ) -> pd.DataFrame:
        case_path = self.__get_case_path(index)
        data_path = report.loc[index, "data_path"]
        report_data = {
            "status": -self.status_code - 0.2,  # -6.2
            "data_path": data_path,
            "labels_path": case_path,
            "segmentation_hash": reviewed_hash,
        }

        return report

    def __report_exact_match(
        self, index: Union[str, int], report: pd.DataFrame, reviewed_hash: str
    ) -> pd.DataFrame:
        case_path = self.__get_case_path(index)
        data_path = report.loc[index, "data_path"]
        report_data = {
            "status": -self.status_code - 0.1,  # -6.1
            "data_path": data_path,
            "labels_path": case_path,
            "num_changed_voxels": 0,
            "segmentation_hash": reviewed_hash,
        }

        return report

    def __report_success(
        self,
        index: Union[str, int],
        report: pd.DataFrame,
        num_changed_voxels: int,
        reviewed_hash: str,
    ) -> pd.DataFrame:
        case_path = self.__get_case_path(index)
        data_path = report.loc[index, "data_path"]
        report_data = {
            "status": -self.status_code,  # -6
            "data_path": data_path,
            "labels_path": case_path,
            "num_changed_voxels": num_changed_voxels,
            "segmentation_hash": reviewed_hash,
        }
        update_row_with_dict(report, report_data, index)
        return report

    def could_run(self, index: Union[str, int], report: DataFrame) -> bool:
        print(f"Checking if {self.name} can run")
        # Ensure a single reviewed segmentation file exists
        path = self.__get_input_path(index)
        gt_path = self.__get_backup_path(index)

        is_valid = True
        path_exists = os.path.exists(path)
        gt_path_exists = os.path.exists(gt_path)
        contains_case = False
        reviewed_hash = None
        if path_exists:
            cases = os.listdir(path)
            num_cases = len(cases)
            if num_cases:
                reviewed_file = os.path.join(path, cases[0])
                reviewed_hash = md5_file(reviewed_file)
            contains_case = num_cases == 1

        prev_hash = report.loc[index]["segmentation_hash"]
        hash_changed = prev_hash != reviewed_hash
        print(
            f"{path_exists=} and {contains_case=} and {gt_path_exists=} and {hash_changed=}"
        )
        is_valid = path_exists and contains_case and gt_path_exists and hash_changed

        return is_valid

    def execute(self, index: Union[str, int]) -> Tuple[DataFrame, bool]:

        id, tp = get_id_tp(index)
        path = self.__get_input_path(index)
        cases = os.listdir(path)
        print(f"{path=}")
        print(f"{cases=}")
        match_output_path = self.__get_output_path(index)
        os.makedirs(match_output_path, exist_ok=True)
        # Get the necessary files for match check
        # We assume reviewed and gt files have the same name
        reviewed_file = os.path.join(path, cases[0])
        reviewed_hash = md5_file(reviewed_file)
        gt_file = os.path.join(self.__get_backup_path(index), cases[0])
        print(f"{gt_file=}")
        if not os.path.exists(gt_file):
            print("Ground truth file not found, reviewed file most probably renamed")
            report = self.__report_gt_not_found(index, report, reviewed_hash)
            raise ValueError("Ground truth file not found")

        reviewed_img = nib.load(reviewed_file)
        gt_img = nib.load(gt_file)

        reviewed_voxels = np.array(reviewed_img.dataobj)
        gt_voxels = np.array(gt_img.dataobj)

        num_changed_voxels = np.sum(reviewed_voxels != gt_voxels)
        print(f"{num_changed_voxels=}")
        changed_voxels_file = get_changed_voxels_file(id, tp)
        with open(changed_voxels_file, "w") as f:
            f.write(str(num_changed_voxels))

        return True
