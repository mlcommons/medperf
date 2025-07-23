from typing import Union, List, Tuple
from tqdm import tqdm
import pandas as pd
import os
import shutil
import traceback

from .row_stage import RowStage
from .PrepareDataset import Preparator, FINAL_FOLDER
from .utils import update_row_with_dict, get_id_tp, md5_file


class Extract(RowStage):
    def __init__(
        self,
        data_csv: str,
        out_path: str,
        subpath: str,
        prev_stage_path: str,
        prev_subpath: str,
        # pbar: tqdm,
        func_name: str,
        status_code: int,
        extra_labels_path=[],
    ):
        self.data_csv = data_csv
        self.out_path = out_path
        self.subpath = subpath
        self.data_subpath = FINAL_FOLDER
        self.prev_path = prev_stage_path
        self.prev_subpath = prev_subpath
        os.makedirs(self.out_path, exist_ok=True)
        self.prep = Preparator(data_csv, out_path, "BraTSPipeline")
        self.func_name = func_name
        self.func = getattr(self.prep, func_name)
        self.pbar = tqdm()
        self.failed = False
        self.exception = None
        self.__status_code = status_code
        self.extra_labels_path = extra_labels_path

    @property
    def name(self) -> str:
        return self.func_name.replace("_", " ").capitalize()

    @property
    def status_code(self) -> str:
        return self.__status_code

    def could_run(self, index: Union[str, int], report: pd.DataFrame) -> bool:
        """Determine if case at given index needs to be converted to NIfTI

        Args:
            index (Union[str, int]): Case index, as used by the report dataframe
            report (pd.DataFrame): Report Dataframe for providing additional context

        Returns:
            bool: Wether this stage could be executed for the given case
        """
        print(f"Checking if {self.name} can run")
        prev_paths = self.__get_paths(index, self.prev_path, self.prev_subpath)
        is_valid = all([os.path.exists(path) for path in prev_paths])
        print(f"{is_valid=}")
        return is_valid

    def execute(
        self, index: Union[str, int], report: pd.DataFrame
    ) -> Tuple[pd.DataFrame, bool]:
        """Executes the NIfTI transformation stage on the given case

        Args:
            index (Union[str, int]): case index, as used by the report
            report (pd.DataFrame): DataFrame containing the current state of the preparation flow

        Returns:
            pd.DataFrame: Updated report dataframe
        """
        self.__prepare_exec()
        self.__copy_case(index)
        self._process_case(index)
        report, success = self.__update_state(index, report)
        self.prep.write()

        return report, success

    def __prepare_exec(self):
        # Reset the file contents for errors
        open(self.prep.stderr_log, "w").close()

        # Update the out dataframes to current state
        self.prep.read()

    def __get_paths(self, index: Union[str, int], path: str, subpath: str):
        id, tp = get_id_tp(index)
        data_path = os.path.join(path, self.data_subpath, id, tp)
        out_path = os.path.join(path, subpath, id, tp)
        return data_path, out_path

    def __copy_case(self, index: Union[str, int]):
        prev_paths = self.__get_paths(index, self.prev_path, self.prev_subpath)
        copy_paths = self.__get_paths(index, self.out_path, self.prev_subpath)
        for prev, copy in zip(prev_paths, copy_paths):
            shutil.rmtree(copy, ignore_errors=True)
            shutil.copytree(prev, copy, dirs_exist_ok=True)

    def _process_case(self, index: Union[str, int]):
        id, tp = get_id_tp(index)
        df = self.prep.subjects_df
        row_search = df[(df["SubjectID"] == id) & (df["Timepoint"] == tp)]
        if len(row_search) > 0:
            row = row_search.iloc[0]
        else:
            # Most probably this case was semi-prepared. Mock a row
            row = pd.Series({"SubjectID": id, "Timepoint": tp, "T1": "", "T1GD": "", "T2": "", "FLAIR": ""})
        self.func(row, self.pbar)

    def __hide_paths(self, hide_paths):
        for path in hide_paths:
            dirname = os.path.dirname(path)
            hidden_name = f".{os.path.basename(path)}"
            hidden_path = os.path.join(dirname, hidden_name)
            if os.path.exists(hidden_path):
                shutil.rmtree(hidden_path)
            shutil.move(path, hidden_path)

    def __update_state(
        self, index: Union[str, int], report: pd.DataFrame
    ) -> Tuple[pd.DataFrame, bool]:
        if self.failed:
            del_paths = self.__get_paths(index, self.out_path, self.subpath)
            report, success = self.__report_failure(index, report)
            for del_path in del_paths:
                shutil.rmtree(del_path, ignore_errors=True)
        else:
            # Backup the paths in case we need to revert to this stage
            hide_paths = self.__get_paths(index, self.prev_path, self.prev_subpath)
            _, out_path = self.__get_paths(index, self.out_path, self.subpath)
            # Wait a little so that file gets created
            brain_mask_file = os.path.join(out_path, "brainMask_fused.nii.gz")
            # Handle the case where a brain mask doesn't exist
            # Due to the subject being semi-prepared
            brain_mask_hash = ""
            if os.path.exists(brain_mask_file):
                brain_mask_hash = md5_file(brain_mask_file)
            report, success = self.__report_success(index, report, brain_mask_hash)
            self.__hide_paths(hide_paths)

        return report, success

    def __report_success(
        self, index: Union[str, int], report: pd.DataFrame, brain_mask_hash: str
    ) -> Tuple[pd.DataFrame, bool]:
        data_path, labels_path = self.__get_paths(index, self.out_path, self.subpath)
        labels_path = os.path.join(labels_path, *self.extra_labels_path)
        report_data = {
            "status": self.status_code,
            "data_path": data_path,
            "labels_path": labels_path,
            "brain_mask_hash": brain_mask_hash,
        }
        update_row_with_dict(report, report_data, index)
        return report, True

    def __report_failure(
        self, index: Union[str, int], report: pd.DataFrame
    ) -> Tuple[pd.DataFrame, bool]:
        prev_data_path, prev_labels_path = self.__get_paths(
            index, self.prev_path, self.prev_subpath
        )
        msg = f"{str(self.exception)}: {self.traceback}"

        report_data = {
            "status": -self.status_code,
            "comment": msg,
            "data_path": prev_data_path,
            "labels_path": prev_labels_path,
        }
        update_row_with_dict(report, report_data, index)
        return report, False
