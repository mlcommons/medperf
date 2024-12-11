import os
import yaml
import pandas as pd
from typing import List
import math

from .dset_stage import DatasetStage
from .utils import get_id_tp, cleanup_storage
from .mlcube_constants import DONE_STAGE_STATUS


def row_to_path(row: pd.Series) -> str:
    id = row["SubjectID"]
    tp = row["Timepoint"]
    return os.path.join(id, tp)


class SplitStage(DatasetStage):
    def __init__(
        self,
        params: str,
        data_path: str,
        labels_path: str,
        staging_folders: List[str],
    ):
        self.params = params
        self.data_path = data_path
        self.labels_path = labels_path
        self.split_csv_path = os.path.join(data_path, "splits.csv")
        self.train_csv_path = os.path.join(data_path, "train.csv")
        self.val_csv_path = os.path.join(data_path, "val.csv")
        self.staging_folders = staging_folders

    @property
    def name(self) -> str:
        return "Generate splits"

    @property
    def status_code(self) -> int:
        return DONE_STAGE_STATUS

    def could_run(self, report: pd.DataFrame) -> bool:
        split_exists = os.path.exists(self.split_csv_path)
        if split_exists:
            # This stage already ran
            return False

        for index in report.index:
            id, tp = get_id_tp(index)
            case_data_path = os.path.join(self.data_path, id, tp)
            case_labels_path = os.path.join(self.labels_path, id, tp)
            data_exists = os.path.exists(case_data_path)
            labels_exist = os.path.exists(case_labels_path)

            if not data_exists or not labels_exist:
                # Some subjects are not ready
                return False

        return True

    def __report_success(self, report: pd.DataFrame) -> pd.DataFrame:
        report["status"] = self.status_code

        return report

    def execute(self, report: pd.DataFrame) -> pd.DataFrame:
        with open(self.params, "r") as f:
            params = yaml.safe_load(f)

        seed = params["seed"]
        train_pct = params["train_percent"]

        split_df = report.copy(deep=True)
        split_df["SubjectID"] = split_df.index.str.split("|").str[0]
        split_df["Timepoint"] = split_df.index.str.split("|").str[1]
        split_df = split_df[["SubjectID", "Timepoint"]].reset_index(drop=True)
        subjects = split_df["SubjectID"].drop_duplicates()
        subjects = subjects.sample(frac=1, random_state=seed)
        train_size = math.floor(len(subjects) * train_pct)

        train_subjects = subjects.iloc[:train_size]
        val_subjects = subjects.iloc[train_size:]

        train_mask = split_df["SubjectID"].isin(train_subjects)
        val_mask = split_df["SubjectID"].isin(val_subjects)

        split_df.loc[train_mask, "Split"] = "Train"
        split_df.loc[val_mask, "Split"] = "Val"

        split_df.to_csv(self.split_csv_path, index=False)

        # Generate separate splits files with relative path
        split_df["path"] = split_df.apply(row_to_path, axis=1)

        split_df.loc[train_mask].to_csv(self.train_csv_path, index=False)
        split_df.loc[val_mask].to_csv(self.val_csv_path, index=False)

        report = self.__report_success(report)
        cleanup_storage(self.staging_folders)

        return report, True
