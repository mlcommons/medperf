from typing import Union, Tuple
import os
import yaml
import shutil
from time import sleep
from typing import List

import pandas as pd
from pandas import DataFrame

from .dset_stage import DatasetStage
from .utils import get_id_tp, cleanup_storage
from .constants import TUMOR_MASK_FOLDER, INTERIM_FOLDER, FINAL_FOLDER
from .mlcube_constants import CONFIRM_STAGE_STATUS


class ConfirmStage(DatasetStage):
    def __init__(
        self,
        data_csv: str,
        out_data_path: str,
        out_labels_path: str,
        prev_stage_path: str,
        backup_path: str,
        staging_folders: List[str],
    ):
        self.data_csv = data_csv
        self.out_data_path = out_data_path
        self.out_labels_path = out_labels_path
        self.prev_stage_path = prev_stage_path
        self.backup_path = backup_path
        self.staging_folders = staging_folders
        self.prompt_file = ".prompt.txt"
        self.response_file = ".response.txt"

    @property
    def name(self):
        return "Annotations Confirmation"

    @property
    def status_code(self):
        return CONFIRM_STAGE_STATUS

    def __get_input_data_path(self, index: Union[str, int]):
        id, tp = get_id_tp(index)
        path = os.path.join(self.prev_stage_path, FINAL_FOLDER, id, tp)
        return path

    def __get_input_label_path(self, index: Union[str, int]):
        id, tp = get_id_tp(index)
        path = os.path.join(
            self.prev_stage_path, INTERIM_FOLDER, id, tp, TUMOR_MASK_FOLDER, "finalized"
        )
        case = os.listdir(path)[0]

        return os.path.join(path, case)

    def __get_output_data_path(self, index: Union[str, int]):
        id, tp = get_id_tp(index)
        path = os.path.join(self.out_data_path, id, tp)
        return path

    def __get_output_label_path(self, index: Union[str, int]):
        id, tp = get_id_tp(index)
        path = os.path.join(self.out_labels_path, id, tp)
        filename = f"{id}_{tp}_final_seg.nii.gz"
        return path, filename

    def __confirm(self, exact_match_percent: float) -> bool:
        exact_match_percent = round(exact_match_percent * 100, 2)
        msg = (
            f"We've identified {exact_match_percent}% of cases have not been modified "
            + "with respect to the baseline segmentation. Do you confirm this is intended? "
            + "[Y]/n"
        )

        # user_input = input(msg).lower()
        prompt_path = os.path.join(self.out_data_path, self.prompt_file)
        response_path = os.path.join(self.out_data_path, self.response_file)

        with open(prompt_path, "w") as f:
            f.write(msg)

        while not os.path.exists(response_path):
            sleep(1)

        with open(response_path, "r") as f:
            user_input = f.readline().strip()

        os.remove(prompt_path)
        os.remove(response_path)

        return user_input == "y" or user_input == ""

    def __report_failure(self, report: DataFrame) -> DataFrame:
        # For this stage, failure is done when the user doesn't confirm
        # This means he probably wants to keep working on the data
        # And needs to know which rows are exact matches.
        # Because of this, failing this stage keeps the report intact
        return report

    def __process_row(self, row: pd.Series) -> pd.Series:
        """process a row by moving the required files
        to their respective locations, and removing any extra files

        Args:
            report (DataFrame): data preparation report

        Returns:
            DataFrame: modified data preparation report
        """
        index = row.name
        input_data_path = self.__get_input_data_path(index)
        input_label_filepath = self.__get_input_label_path(index)
        output_data_path = self.__get_output_data_path(index)
        output_label_path, filename = self.__get_output_label_path(index)
        output_label_filepath = os.path.join(output_label_path, filename)

        shutil.rmtree(output_data_path, ignore_errors=True)
        shutil.copytree(input_data_path, output_data_path)
        os.makedirs(output_label_path, exist_ok=True)
        shutil.copy(input_label_filepath, output_label_filepath)

        row["status"] = self.status_code
        row["data_path"] = output_data_path
        row["labels_path"] = output_label_path
        return row

    def could_run(self, report: DataFrame) -> bool:
        print(f"Checking if {self.name} can run")
        # could run once all cases have been compared to the ground truth
        missing_voxels = report["num_changed_voxels"].isnull().values.any()
        prev_path_exists = os.path.exists(self.prev_stage_path)
        empty_prev_path = True
        if prev_path_exists:
            empty_prev_path = len(os.listdir(self.prev_stage_path)) == 0

        print(f"{prev_path_exists=} and not {empty_prev_path=} and not {missing_voxels=}")
        return prev_path_exists and not empty_prev_path and not missing_voxels

    def execute(self, report: DataFrame) -> Tuple[DataFrame, bool]:
        exact_match_percent = (report["num_changed_voxels"] == 0).sum() / len(report)
        confirmed = self.__confirm(exact_match_percent)

        if not confirmed:
            report = self.__report_failure(report)
            return report, False

        report = report.apply(self.__process_row, axis=1)
        # Remove all intermediary steps
        cleanup_storage(self.staging_folders)
        if os.path.exists(self.data_csv):
            os.remove(self.data_csv)

        return report, True
