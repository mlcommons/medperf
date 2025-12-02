from typing import Union
from tqdm import tqdm
import pandas as pd
import os
import shutil

from .row_stage import RowStage
from .PrepareDataset import Preparator
from .utils import get_id_tp
from .mlcube_constants import NIFTI_STAGE_STATUS
from .constants import FINAL_FOLDER, EXEC_NAME


class NIfTITransform(RowStage):
    def __init__(
        self,
        data_csv: str,
        out_path: str,
        prev_stage_path: str,
        metadata_path: str,
        data_out: str,
    ):
        self.data_csv = data_csv
        self.out_path = out_path
        self.data_out = data_out
        self.prev_stage_path = prev_stage_path
        self.metadata_path = metadata_path
        os.makedirs(self.out_path, exist_ok=True)
        self.prep = Preparator(data_csv, out_path, EXEC_NAME)
        # self.pbar = pbar
        self.pbar = tqdm()

    @property
    def name(self) -> str:
        return "NiFTI Conversion"

    @property
    def status_code(self) -> int:
        return NIFTI_STAGE_STATUS

    def could_run(self, index: Union[str, int], report: pd.DataFrame) -> bool:
        """Determine if case at given index needs to be converted to NIfTI

        Args:
            index (Union[str, int]): Case index, as used by the report dataframe
            report (pd.DataFrame): Report Dataframe for providing additional context

        Returns:
            bool: Wether this stage could be executed for the given case
        """
        print(f"Checking if {self.name} can run")
        id, tp = get_id_tp(index)
        prev_case_path = os.path.join(self.prev_stage_path, id, tp)
        if os.path.exists(prev_case_path):
            is_valid = len(os.listdir(prev_case_path)) > 0
            print(f"{is_valid}")
            return is_valid
        return False

    def execute(
        self,
        index: Union[str, int],
    ) -> pd.DataFrame:
        """Executes the NIfTI transformation stage on the given case

        Args:
            index (Union[str, int]): case index, as used by the report
            report (pd.DataFrame): DataFrame containing the current state of the preparation flow

        Returns:
            pd.DataFrame: Updated report dataframe
        """
        self.__prepare_exec()
        self.__process_case(index)
        self.__cleanup_artifacts(index)
        success = self.__validate_result(index)
        self.prep.write()
        self.__update_metadata(index)

        return success

    def __cleanup_artifacts(self, index):
        unused_artifacts_substrs = ["raw", "to_SRI", ".mat"]
        _, out_path = self.__get_output_paths(index)
        root_artifacts = os.listdir(out_path)
        for artifact in root_artifacts:
            if not any([substr in artifact for substr in unused_artifacts_substrs]):
                continue
            artifact_path = os.path.join(out_path, artifact)
            os.remove(artifact_path)

    def __get_output_paths(self, index: Union[str, int]):
        id, tp = get_id_tp(index)
        fets_path = os.path.join(self.prep.final_output_dir, id, tp)
        qc_path = os.path.join(self.prep.interim_output_dir, id, tp)

        return fets_path, qc_path

    def __prepare_exec(self):
        # Reset the file contents for errors
        open(self.prep.stderr_log, "w").close()

        self.prep.read()

    def __process_case(self, index: Union[str, int]):
        id, tp = get_id_tp(index)
        df = self.prep.subjects_df
        row = df[(df["SubjectID"] == id) & (df["Timepoint"] == tp)].iloc[0]
        self.prep.convert_to_dicom(hash(index), row, self.pbar)

    def __undo_current_stage_changes(self, index: Union[str, int]):
        fets_path, qc_path = self.__get_output_paths(index)
        shutil.rmtree(fets_path, ignore_errors=True)
        shutil.rmtree(qc_path, ignore_errors=True)

    def __validate_result(self, index: Union[str, int]) -> pd.DataFrame:
        id, tp = get_id_tp(index)
        failing = self.prep.failing_subjects
        failing_subject = failing[
            (failing["SubjectID"] == id) & (failing["Timepoint"] == tp)
        ]
        if len(failing_subject):
            self.__undo_current_stage_changes(index)
            self.__report_failure()
        else:
            success = True

        return success

    def __update_metadata(self, index):
        id, tp = get_id_tp(index)
        fets_path = os.path.join(self.out_path, FINAL_FOLDER)
        outfile_dir = os.path.join(self.metadata_path, id, tp)
        os.makedirs(outfile_dir, exist_ok=True)
        for file in os.listdir(fets_path):
            filepath = os.path.join(fets_path, file)
            out_filepath = os.path.join(self.metadata_path, id, tp, file)
            if os.path.isfile(filepath) and filepath.endswith(".yaml"):
                shutil.copyfile(filepath, out_filepath)

    def __report_failure(self):

        with open(self.prep.stderr_log, "r") as f:
            msg = f.read()

        raise TypeError(msg)
