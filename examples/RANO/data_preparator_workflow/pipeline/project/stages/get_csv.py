from .row_stage import RowStage
from .CreateCSVForDICOMs import CSVCreator
from .utils import get_id_tp
import pandas as pd
from typing import Union, Tuple
import os
import shutil
from .mlcube_constants import CSV_STAGE_STATUS


class AddToCSV(RowStage):
    def __init__(
        self, input_dir: str, output_csv: str, out_dir: str, prev_stage_path: str
    ):
        self.input_dir = input_dir
        self.output_csv = output_csv
        self.out_dir = out_dir
        self.prev_stage_path = prev_stage_path
        os.makedirs(self.out_dir, exist_ok=True)
        self.csv_processor = CSVCreator(self.input_dir, self.output_csv)
        if os.path.exists(self.output_csv):
            # Use the updated version of the CSV
            self.contents = pd.read_csv(self.output_csv)
            self.csv_processor.output_df_for_csv = self.contents
        else:
            # Use the default, empty version
            self.contents = self.csv_processor.output_df_for_csv

    @property
    def name(self) -> str:
        return "Initial Validation"

    @property
    def status_code(self) -> int:
        return CSV_STAGE_STATUS

    def could_run(self, index: Union[str, int], report: pd.DataFrame) -> bool:
        """Determines if getting a new CSV is necessary.
        This is done by checking the existence of the expected file

        Args:
            index (Union[str, int]): case index in the report
            report (pd.DataFrame): Dataframe containing the current state of the preparation flow

        Returns:
            bool: wether this stage could be executed
        """
        print(f"Checking if {self.name} can run")
        id, tp = get_id_tp(index)
        prev_case_path = os.path.join(self.prev_stage_path, id, tp)
        is_valid = os.path.exists(prev_case_path)
        print(f"{is_valid=}")
        return is_valid

    def execute(self, index: Union[str, int]) -> Tuple[pd.DataFrame, bool]:
        """Adds valid cases to the data csv that is used for later processing
        Invalid cases are flagged in the report

        Args:
            index (Union[str, int]): case index in the report
            report (pd.DataFrame): DataFrame containing the current state of the preparation flow

        Returns:
            pd.DataFrame: Updated report dataframe
        """
        id, tp = get_id_tp(index)
        subject_path = os.path.join(self.input_dir, id)
        tp_path = os.path.join(subject_path, tp)
        subject_out_path = os.path.join(self.out_dir, id)
        tp_out_path = os.path.join(subject_out_path, tp)
        # We will first copy the timepoint to the out folder
        # This is so, if successful, the csv will point to the data
        # in the next stage, instead of the previous
        shutil.rmtree(tp_out_path, ignore_errors=True)
        shutil.copytree(tp_path, tp_out_path)

        try:
            self.csv_processor.process_timepoint(tp, id, subject_out_path)
            report_data = {
                "status": self.status_code,
                "data_path": tp_out_path,
                "labels_path": "",
            }
        except Exception as e:
            report_data = {
                "status": -self.status_code - 0.3,
                "comment": str(e),
                "data_path": tp_path,
                "labels_path": "",
            }
            raise

        missing = self.csv_processor.subject_timepoint_missing_modalities
        extra = self.csv_processor.subject_timepoint_extra_modalities

        success = True
        report_data["comment"] = ""
        for missing_subject, msg in missing:
            if f"{id}_{tp}" in missing_subject:
                # Differentiate errors by floating point value
                status_code = -self.status_code - 0.1  # -1.1
                report_data["status"] = status_code
                report_data["data_path"] = tp_path
                report_data["comment"] += "\n\n" + msg
                success = False

        for extra_subject, msg in extra:
            if f"{id}_{tp}" in extra_subject:
                # Differentiate errors by floating point value
                status_code = -self.status_code - 0.2  # -1.2
                report_data["status"] = status_code
                report_data["data_path"] = tp_path
                report_data["comment"] += "\n\n" + msg
                success = False

        report_data["comment"] = report_data["comment"].strip()
        if not success:
            shutil.rmtree(tp_out_path, ignore_errors=True)
            raise TypeError(report_data["comment"])

        self.csv_processor.write()

        return tp_out_path
