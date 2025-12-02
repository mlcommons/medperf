import os
import yaml
import pandas as pd
from typing import List
import math

from .dset_stage import DatasetStage
from .utils import (
    get_id_tp,
    cleanup_storage,
    safe_remove,
    find_finalized_subjects,
    delete_empty_directory,
)
from .mlcube_constants import DONE_STAGE_STATUS, METADATA_PATH
from .env_vars import WORKSPACE_DIR
from .constants import DICOM_ANON_FILENAME, DICOM_COLLAB_FILENAME


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
        base_finalized_dir: str,
    ):
        self.params = params
        self.data_path = data_path
        self.labels_path = labels_path
        self.split_csv_path = os.path.join(data_path, "splits.csv")
        self.train_csv_path = os.path.join(data_path, "train.csv")
        self.val_csv_path = os.path.join(data_path, "val.csv")
        self.staging_folders = staging_folders
        self.base_finalized_dir = base_finalized_dir

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

    def consolidate_metadata(self):
        base_metadata_dir = os.path.join(WORKSPACE_DIR, METADATA_PATH)
        anon_dict = {}
        collab_dict = {}
        files_to_delete = set()
        for subject_id_dir in os.listdir(base_metadata_dir):
            try:
                subject_complete_dir = os.path.join(base_metadata_dir, subject_id_dir)

                for timepoint_dir in os.listdir(subject_complete_dir):
                    subject_timepoint_complete_dir = os.path.join(
                        subject_complete_dir, timepoint_dir
                    )
                    subject_metadata_path = os.path.join(subject_timepoint_complete_dir)
                    if not os.path.isdir(subject_metadata_path):
                        continue

                    anon_yaml = os.path.join(subject_metadata_path, DICOM_ANON_FILENAME)
                    collab_yaml = os.path.join(
                        subject_metadata_path, DICOM_COLLAB_FILENAME
                    )

                    update_tuples = [(anon_yaml, anon_dict), (collab_yaml, collab_dict)]
                    for yaml_file, data_dict in update_tuples:
                        if not os.path.isfile(yaml_file):
                            continue

                        with open(yaml_file, "r") as f:
                            update_dict = yaml.safe_load(f)

                        data_dict.update(**update_dict)
                        files_to_delete.add(yaml_file)
            except OSError:
                pass

        final_anon_file = os.path.join(base_metadata_dir, DICOM_ANON_FILENAME)
        final_collab_file = os.path.join(base_metadata_dir, DICOM_COLLAB_FILENAME)

        write_tuples = [(final_anon_file, anon_dict), (final_collab_file, collab_dict)]
        for file_path, data in write_tuples:
            with open(file_path, "w") as f:
                yaml.dump(data, f)

        for file in files_to_delete:
            safe_remove(file)

        for subdir in os.listdir(base_metadata_dir):
            complete_subdir_path = os.path.join(base_metadata_dir, subdir)
            delete_empty_directory(complete_subdir_path)

    def execute(self) -> pd.DataFrame:
        with open(self.params, "r") as f:
            params = yaml.safe_load(f)

        seed = params["seed"]
        train_pct = params["train_percent"]

        finalized_subjects = find_finalized_subjects()
        split_df = pd.DataFrame(finalized_subjects)
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

        self.consolidate_metadata()
        cleanup_storage(self.staging_folders)

        return True
