from typing import Union, Tuple
import os
import shutil
from time import sleep

import pandas as pd
from pandas import DataFrame

from .dset_stage import DatasetStage
from .utils import (
    get_id_tp,
    get_subdirectories,
    get_manual_approval_finalized_path,
    get_changed_voxels_file,
    find_finalized_subjects,
)
from .constants import FINAL_FOLDER
from .mlcube_constants import (
    CONFIRM_STAGE_STATUS,
    TUMOR_EXTRACTION_REVIEW_PATH,
    AUX_FILES_PATH,
)
from .env_vars import DATA_DIR


class ConfirmStage(DatasetStage):
    def __init__(
        self,
        out_data_path: str,
        out_labels_path: str,
        prev_stage_path: str,
        backup_path: str,
    ):
        self.out_data_path = out_data_path
        self.out_labels_path = out_labels_path
        self.prev_stage_path = prev_stage_path
        self.backup_path = backup_path
        self.prompt_file = ".prompt.txt"
        self.response_file = ".response.txt"

    @property
    def name(self):
        return "Annotations Confirmation"

    @property
    def status_code(self):
        return CONFIRM_STAGE_STATUS

    def __get_input_data_path(self, id, tp):
        path = os.path.join(self.prev_stage_path, id, tp, FINAL_FOLDER, id, tp)
        return path

    def __get_input_label_path(self, id, tp):
        path = get_manual_approval_finalized_path(id, tp, TUMOR_EXTRACTION_REVIEW_PATH)

        case = os.listdir(path)[0]

        return os.path.join(path, case)

    def __get_output_data_path(self, id, tp):
        path = os.path.join(self.out_data_path, id, tp)
        return path

    def __get_output_label_path(self, id, tp):
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

    def __process_row(self, subject_dict) -> pd.Series:
        """process a row by moving the required files
        to their respective locations, and removing any extra files

        Args:
            report (DataFrame): data preparation report

        Returns:
            DataFrame: modified data preparation report
        """
        subject_id, timepoint = subject_dict["SubjectID"], subject_dict["Timepoint"]
        input_data_path = self.__get_input_data_path(subject_id, timepoint)
        input_label_filepath = self.__get_input_label_path(subject_id, timepoint)
        output_data_path = self.__get_output_data_path(subject_id, timepoint)
        output_label_path, filename = self.__get_output_label_path(
            subject_id, timepoint
        )
        output_label_filepath = os.path.join(output_label_path, filename)

        shutil.rmtree(output_data_path, ignore_errors=True)
        shutil.copytree(input_data_path, output_data_path)
        os.makedirs(output_label_path, exist_ok=True)
        shutil.copy(input_label_filepath, output_label_filepath)

    def could_run(self, report: DataFrame) -> bool:
        print(f"Checking if {self.name} can run")
        # could run once all cases have been compared to the ground truth
        missing_voxels = report["num_changed_voxels"].isnull().values.any()
        prev_path_exists = os.path.exists(self.prev_stage_path)
        empty_prev_path = True
        if prev_path_exists:
            empty_prev_path = len(os.listdir(self.prev_stage_path)) == 0

        print(
            f"{prev_path_exists=} and not {empty_prev_path=} and not {missing_voxels=}"
        )
        return prev_path_exists and not empty_prev_path and not missing_voxels

    @staticmethod
    def calculate_exact_match_percent():
        """
        This value is equal to the sum of all subjects where no voxels were
        changed in the Tumor Segmentation divided by the total number of subjects.
        """
        base_aux_dir = os.path.join(DATA_DIR, AUX_FILES_PATH)
        num_subjects = 0
        num_unchanged_subjects = 0

        for subject_id in get_subdirectories(base_aux_dir):
            complete_subject_path = os.path.join(base_aux_dir, subject_id)
            for timepoint in get_subdirectories(complete_subject_path):
                changed_voxels_file = get_changed_voxels_file(subject_id, timepoint)
                if not os.path.isfile(changed_voxels_file):
                    continue
                num_subjects += 1
                with open(changed_voxels_file, "r") as f:
                    changed_voxels = int(f.read())

                if not changed_voxels:
                    num_unchanged_subjects += 1

        return num_unchanged_subjects / num_subjects

    def execute(self) -> Tuple[DataFrame, bool]:
        exact_match_percent = self.calculate_exact_match_percent()

        rounded_percent = round(exact_match_percent * 100, 2)
        msg_file = os.path.join(DATA_DIR, AUX_FILES_PATH, ".msg")
        print(f"{str(rounded_percent)=}")
        with open(msg_file, "w") as f:
            f.write(str(rounded_percent))
        return

    def move_labels(self):
        finalized_subjects = find_finalized_subjects()
        for finalized_subject in finalized_subjects:
            self.__process_row(finalized_subject)
        return True
